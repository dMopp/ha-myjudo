"""Client for the JUDO myjudo.eu cloud interface.

The interface is not officially documented. Register indices and byte offsets
were taken from the community project "getjudo" by ShapeLabs
(https://github.com/www-ShapeLabs-de/Judo-i-soft-save-plus-to-mqtt-bridge) and verified
against a live i-soft safe device.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import logging
from typing import Any
from zoneinfo import ZoneInfo

import aiohttp

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://www.myjudo.eu/interface/"
TIMEOUT = aiohttp.ClientTimeout(total=30)
# myjudo.eu reports timestamps in German local time without an offset.
JUDO_TZ = ZoneInfo("Europe/Berlin")

# Write indices
CMD_OUTPUT_HARDNESS = 60
CMD_START_REGENERATION = 65
CMD_CLOSE_VALVE = 72
CMD_OPEN_VALVE = 73
CMD_EXTRACTION_TIME = 74
CMD_MAX_FLOW = 75
CMD_EXTRACTION_QUANTITY = 76
CMD_HOLIDAY_MODE = 77
CMD_SALT_STOCK = 94
CMD_SLEEP_MODE = 171

HOLIDAY_OFF = "off"
HOLIDAY_LOCK = "lock"
HOLIDAY_MODE_1 = "mode_1"
HOLIDAY_MODE_2 = "mode_2"
HOLIDAY_TO_RAW = {HOLIDAY_OFF: 0, HOLIDAY_MODE_1: 3, HOLIDAY_MODE_2: 5, HOLIDAY_LOCK: 9}
RAW_TO_HOLIDAY = {raw: name for name, raw in HOLIDAY_TO_RAW.items()}


class JudoError(Exception):
    """Generic error talking to myjudo.eu."""


class JudoAuthError(JudoError):
    """Login rejected."""


class JudoConnectionError(JudoError):
    """Network problem or unexpected answer."""


@dataclass
class JudoMessage:
    """Latest warning or error from the device message log."""

    id: int
    msg_type: str
    code: str
    timestamp: datetime | None


@dataclass
class JudoDevice:
    """Parsed state of one device."""

    serial: str
    da: str
    dt: str
    online: bool
    sw_version: str | None
    hw_version: str | None
    last_update: datetime | None
    registers: dict[str, str] = field(repr=False)
    values: dict[str, Any] = field(default_factory=dict)
    message: JudoMessage | None = None


def _le(registers: dict[str, str], index: int, start: int, end: int) -> int | None:
    """Decode a little endian slice of a register's hex string.

    Offsets are character positions in the raw string as delivered by the
    cloud, including the "n:" prefix some registers carry.
    """
    raw = registers.get(str(index))
    if not raw or len(raw) < end:
        return None
    try:
        return int.from_bytes(bytes.fromhex(raw[start:end]), byteorder="little")
    except ValueError:
        return None


def _parse_local(value: str | None, fmt: str) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.strptime(value, fmt)
        if dt.tzinfo is not None:
            return dt
        return dt.replace(tzinfo=JUDO_TZ)
    except ValueError:
        return None


def is_softwell_p(registers: dict[str, str]) -> bool:
    """Guess the register layout: SOFTwell P has no leakage protection data."""
    return "792" not in registers


def parse_values(registers: dict[str, str], softwell_p: bool) -> dict[str, Any]:
    """Turn raw registers into entity values. Missing registers give None."""
    v: dict[str, Any] = {}

    hours = _le(registers, 7, 0, 4)
    v["next_service"] = None if hours is None else hours // 24

    v["total_water"] = _le(registers, 9 if softwell_p else 8, 0, 8)
    v["output_hardness"] = _le(registers, 790, 18, 20)
    v["input_hardness"] = _le(registers, 790, 54, 56)
    v["regeneration_count"] = _le(registers, 791, 62, 66)
    regen = _le(registers, 791, 2, 4)
    v["regeneration_running"] = None if regen is None else bool(regen & 0x0F)

    if softwell_p:
        return v

    v["soft_water"] = _le(registers, 9, 0, 8)
    if v["total_water"] is not None and v["soft_water"] is not None:
        v["hard_water"] = max(v["total_water"] - v["soft_water"], 0)
    else:
        v["hard_water"] = None
    salt = _le(registers, 94, 0, 4)
    v["salt_stock"] = None if salt is None else salt / 1000
    v["salt_range"] = _le(registers, 94, 4, 8)
    v["water_flow"] = _le(registers, 790, 34, 38)
    # Devices without a backup battery report the register as all zeros.
    battery = registers.get("93", "")
    v["battery"] = _le(registers, 93, 6, 8) if battery.strip("0") else None
    lock = _le(registers, 792, 2, 4)
    v["valve_closed"] = None if lock is None else lock > 0
    v["sleep_mode"] = _le(registers, 792, 20, 22)
    v["max_flow"] = _le(registers, 792, 26, 30)
    v["extraction_quantity"] = _le(registers, 792, 30, 34)
    v["extraction_time"] = _le(registers, 792, 34, 38)
    holiday = _le(registers, 792, 38, 40)
    v["holiday_mode"] = (
        None if holiday is None else RAW_TO_HOLIDAY.get(holiday, HOLIDAY_OFF)
    )
    return v


def le_hex(value: int, length: int) -> str:
    """Encode an integer as little endian hex with 8 or 16 bits."""
    if length == 8:
        return f"{value:02X}"
    return value.to_bytes(2, byteorder="little").hex().upper()


class JudoClient:
    """Minimal async client for myjudo.eu."""

    def __init__(
        self, session: aiohttp.ClientSession, username: str, password: str
    ) -> None:
        self._session = session
        self._username = username
        self._password_md5 = hashlib.md5(password.encode("utf-8")).hexdigest()  # noqa: S324 - required by the API
        self._token: str | None = None

    async def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        try:
            async with self._session.get(
                BASE_URL,
                params=params,
                timeout=TIMEOUT,
                headers={"User-Agent": "Mozilla"},
            ) as resp:
                resp.raise_for_status()
                text = await resp.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise JudoConnectionError(
                f"Request failed: {err.__class__.__name__}"
            ) from err
        try:
            data = json.loads(text)
        except ValueError as err:
            raise JudoConnectionError("Answer is not JSON") from err
        if not isinstance(data, dict):
            raise JudoConnectionError("Unexpected answer")
        return data

    async def login(self) -> None:
        """Get a fresh token."""
        data = await self._request(
            {
                "group": "register",
                "command": "login",
                "name": "login",
                "user": self._username,
                "password": self._password_md5,
                "nohash": "Service",
                "role": "customer",
            }
        )
        token = data.get("token")
        if data.get("status") != "ok" or not token:
            raise JudoAuthError("Login rejected")
        self._token = token

    async def _authed(self, params: dict[str, Any]) -> dict[str, Any]:
        """Run a request with the token, logging in again once if it expired."""
        for attempt in range(2):
            if self._token is None:
                await self.login()
            data = await self._request(
                {"token": self._token, "group": "register", **params}
            )
            if data.get("status") == "ok":
                return data
            if data.get("data") == "login failed" and attempt == 0:
                _LOGGER.debug("Token expired, logging in again")
                self._token = None
                continue
            raise JudoConnectionError(f"Server answered: {data.get('data')}")
        raise JudoConnectionError("Unreachable")  # pragma: no cover

    async def get_devices(self, softwell_p: bool | None) -> dict[str, JudoDevice]:
        """Fetch all devices of the account.

        softwell_p selects the register layout; None detects it per device.
        """
        data = await self._authed({"command": "get device data"})
        devices: dict[str, JudoDevice] = {}
        for entry in data.get("data") or []:
            serial = entry.get("serialnumber")
            sub = (entry.get("data") or [None])[0]
            if not serial or not isinstance(sub, dict):
                continue
            raw = sub.get("data") or {}
            registers = {
                key: reg["data"]
                for key, reg in raw.items()
                if isinstance(reg, dict) and reg.get("data")
            }
            devices[serial] = JudoDevice(
                serial=serial,
                da=sub.get("da", ""),
                dt=sub.get("dt", ""),
                online=entry.get("status") == "online",
                sw_version=sub.get("sv"),
                hw_version=sub.get("hv"),
                last_update=_parse_local(raw.get("lu"), "%Y-%m-%d %H:%M:%S"),
                registers=registers,
                values=parse_values(
                    registers,
                    is_softwell_p(registers) if softwell_p is None else softwell_p,
                ),
            )
        return devices

    async def get_latest_messages(self) -> dict[str, JudoMessage]:
        """Return the newest message per device serial."""
        data = await self._authed({"command": "get error messages"})
        latest: dict[str, JudoMessage] = {}
        for entry in data.get("data") or []:
            serial = entry.get("serialnumber")
            if not serial or serial in latest:
                continue
            ts = entry.get("ts_sort") or ""
            latest[serial] = JudoMessage(
                id=int(entry.get("id", 0)),
                msg_type=str(entry.get("type", "")),
                code=str(entry.get("error", "")),
                timestamp=_parse_local(ts.split(".")[0], "%Y-%m-%d %H:%M:%S"),
            )
        return latest

    async def write(self, device: JudoDevice, index: int, data: str = "") -> None:
        """Write a register on the device."""
        await self._authed(
            {
                "command": "write data",
                "serial_number": device.serial,
                "dt": device.dt,
                "index": index,
                "data": data,
                "da": device.da,
                "role": "customer",
            }
        )
