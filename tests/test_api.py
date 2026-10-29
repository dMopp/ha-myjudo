"""Tests for the myjudo.eu client and register parsing."""

from homeassistant.helpers.aiohttp_client import async_get_clientsession
import pytest

from custom_components.myjudo.api import (
    BASE_URL,
    HOLIDAY_OFF,
    JudoAuthError,
    JudoClient,
    JudoConnectionError,
    is_softwell_p,
    le_hex,
    parse_values,
)

from .conftest import SERIAL


def test_parse_values(device_data):
    raw = device_data["data"][0]["data"][0]["data"]
    registers = {
        k: v["data"] for k, v in raw.items() if isinstance(v, dict) and v.get("data")
    }
    values = parse_values(registers, softwell_p=False)
    assert values == {
        "next_service": 354,
        "total_water": 667249,
        "soft_water": 439493,
        "hard_water": 227756,
        "output_hardness": 5,
        "input_hardness": 15,
        "regeneration_count": 1336,
        "regeneration_running": False,
        "salt_stock": 20.5,
        "salt_range": 205,
        "water_flow": 0,
        "battery": None,
        "valve_closed": False,
        "sleep_mode": 0,
        "max_flow": 3000,
        "extraction_quantity": 300,
        "extraction_time": 30,
        "holiday_mode": HOLIDAY_OFF,
    }


def test_battery_only_with_data():
    values = parse_values({"93": "000000550000000000"}, softwell_p=False)
    assert values["battery"] == 0x55


def test_is_softwell_p():
    assert is_softwell_p({"9": "C5B40600"})
    assert not is_softwell_p({"792": "2:00"})


async def test_get_devices_auto_layout(hass, mock_api):
    client = JudoClient(async_get_clientsession(hass), "judouser", "secret")
    devices = await client.get_devices(softwell_p=None)
    assert devices[SERIAL].values["valve_closed"] is False


def test_parse_values_softwell_p_and_missing():
    values = parse_values({"9": "C5B40600"}, softwell_p=True)
    assert values["total_water"] == 439493
    assert values["output_hardness"] is None
    assert "valve_closed" not in values


@pytest.mark.parametrize(
    ("value", "bits", "expected"),
    [(5, 8, "05"), (3000, 16, "B80B"), (20500, 16, "1450")],
)
def test_le_hex(value, bits, expected):
    assert le_hex(value, bits) == expected


async def test_get_devices_and_messages(hass, mock_api):
    client = JudoClient(async_get_clientsession(hass), "judouser", "secret")
    devices = await client.get_devices(softwell_p=False)
    assert list(devices) == [SERIAL]
    device = devices[SERIAL]
    assert device.online
    assert device.dt == "0x32"
    assert device.last_update.isoformat() == "2026-10-28T22:56:31+01:00"

    messages = await client.get_latest_messages()
    msg = messages[SERIAL]
    assert (msg.msg_type, msg.code, msg.id) == ("w", "28", 1003)
    assert msg.timestamp.isoformat() == "2026-02-22T09:10:06+01:00"


async def test_relogin_on_expired_token(hass, aioclient_mock, device_data):
    aioclient_mock.get(
        f"{BASE_URL}?command=login", json={"status": "ok", "token": "NEW"}
    )
    aioclient_mock.get(
        f"{BASE_URL}?command=get+device+data&token=OLD",
        json={"status": "error", "data": "login failed"},
    )
    aioclient_mock.get(
        f"{BASE_URL}?command=get+device+data&token=NEW", json=device_data
    )
    client = JudoClient(async_get_clientsession(hass), "judouser", "secret")
    client._token = "OLD"
    devices = await client.get_devices(softwell_p=False)
    assert SERIAL in devices


async def test_login_rejected(hass, aioclient_mock):
    aioclient_mock.get(
        f"{BASE_URL}?command=login", json={"status": "error", "data": "login failed"}
    )
    client = JudoClient(async_get_clientsession(hass), "judouser", "wrong")
    with pytest.raises(JudoAuthError):
        await client.login()


async def test_not_json(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}?command=login", text="<html>maintenance</html>")
    client = JudoClient(async_get_clientsession(hass), "judouser", "secret")
    with pytest.raises(JudoConnectionError):
        await client.login()
