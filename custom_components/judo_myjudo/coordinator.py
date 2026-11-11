"""Data update coordinator for JUDO myjudo."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from homeassistant.util.hass_dict import HassKey

from .api import JudoAuthError, JudoClient, JudoConnectionError, JudoDevice, JudoError
from .const import (
    CONF_MODEL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MODEL_AUTO,
    MODEL_SOFTWELL_P,
)

_LOGGER = logging.getLogger(__name__)

type JudoConfigEntry = ConfigEntry[JudoCoordinator]

# The cloud also rejects valid logins while JUDO maintains its servers
# (e.g. 2026-11-06 to 2026-11-09). Only ask for a new password once logins
# have been rejected for this long; until then keep retrying.
AUTH_GRACE = timedelta(hours=1)
# First rejected login per config entry. Kept in hass.data so it survives the
# setup retries, which create a new coordinator each time.
AUTH_FAILED_SINCE: HassKey[dict[str, datetime]] = HassKey(f"{DOMAIN}_auth_failed_since")


class JudoCoordinator(DataUpdateCoordinator[dict[str, JudoDevice]]):
    """Polls the JU-Control cloud for all devices of the account."""

    config_entry: JudoConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: JudoConfigEntry, client: JudoClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.client = client

    @property
    def model(self) -> str:
        return self.config_entry.options.get(CONF_MODEL, MODEL_AUTO)

    @property
    def softwell_p(self) -> bool | None:
        """Register layout to use; None lets the client detect it."""
        if self.model == MODEL_AUTO:
            return None
        return self.model == MODEL_SOFTWELL_P

    async def _async_update_data(self) -> dict[str, JudoDevice]:
        try:
            devices = await self.client.get_devices(self.softwell_p)
        except JudoAuthError as err:
            self._handle_auth_failure()
            raise UpdateFailed(
                translation_domain=DOMAIN, translation_key="auth_failed"
            ) from err
        except JudoError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        self._handle_auth_success()

        # The message log is a nice-to-have; keep the last known message if it fails.
        try:
            messages = await self.client.get_latest_messages()
        except JudoConnectionError as err:
            _LOGGER.debug("Could not fetch message log: %s", err)
            messages = {
                serial: dev.message
                for serial, dev in (self.data or {}).items()
                if dev.message
            }
        for serial, device in devices.items():
            device.message = messages.get(serial)
        return devices

    def _handle_auth_failure(self) -> None:
        """Ask for a new password once logins failed for longer than AUTH_GRACE."""
        failed_since = self.hass.data.setdefault(AUTH_FAILED_SINCE, {})
        entry_id = self.config_entry.entry_id
        now = dt_util.utcnow()
        first = failed_since.setdefault(entry_id, now)
        if now - first >= AUTH_GRACE:
            self.config_entry.async_start_reauth(self.hass)
        else:
            _LOGGER.debug("Login rejected since %s, retrying", first)

    def _handle_auth_success(self) -> None:
        """Forget earlier rejected logins and drop a pending password prompt."""
        failed_since = self.hass.data.get(AUTH_FAILED_SINCE)
        if (
            not failed_since
            or failed_since.pop(self.config_entry.entry_id, None) is None
        ):
            return
        for flow in list(
            self.config_entry.async_get_active_flows(self.hass, {SOURCE_REAUTH})
        ):
            self.hass.config_entries.flow.async_abort(flow["flow_id"])

    async def async_write(self, serial: str, index: int, data: str = "") -> None:
        """Write a register and raise a user-facing error on failure."""
        device = self.data.get(serial) if self.data else None
        if device is None:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="device_not_found",
                translation_placeholders={"serial": serial},
            )
        try:
            await self.client.write(device, index, data)
        except JudoError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_failed",
                translation_placeholders={"error": str(err)},
            ) from err

    def set_optimistic(self, serial: str, key: str, value: object) -> None:
        """Show a written value right away; the next poll confirms it."""
        device = self.data.get(serial) if self.data else None
        if device is None:
            return
        device.values[key] = value
        self.async_update_listeners()
