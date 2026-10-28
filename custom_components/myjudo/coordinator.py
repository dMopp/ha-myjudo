"""Data update coordinator for JUDO myjudo."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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


class JudoCoordinator(DataUpdateCoordinator[dict[str, JudoDevice]]):
    """Polls myjudo.eu for all devices of the account."""

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
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="auth_failed"
            ) from err
        except JudoError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                translation_placeholders={"error": str(err)},
            ) from err

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

    async def async_write(self, serial: str, index: int, data: str = "") -> None:
        """Write a register and raise a user-facing error on failure."""
        try:
            await self.client.write(self.data[serial], index, data)
        except JudoError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_failed",
                translation_placeholders={"error": str(err)},
            ) from err

    def set_optimistic(self, serial: str, key: str, value: object) -> None:
        """Show a written value right away; the next poll confirms it."""
        self.data[serial].values[key] = value
        self.async_update_listeners()
