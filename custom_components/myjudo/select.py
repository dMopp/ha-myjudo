"""Holiday mode select for JUDO myjudo."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import CMD_HOLIDAY_MODE, CMD_OPEN_VALVE, HOLIDAY_OFF, HOLIDAY_TO_RAW
from .coordinator import JudoConfigEntry
from .entity import JudoEntity, has_value

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JudoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        JudoHolidaySelect(coordinator, serial, "holiday_mode")
        for serial in coordinator.data
        if has_value(coordinator, serial, "holiday_mode")
    )


class JudoHolidaySelect(JudoEntity, SelectEntity):
    """Holiday mode of the leakage protection."""

    _attr_options = list(HOLIDAY_TO_RAW)
    value_key = "holiday_mode"

    @property
    def current_option(self) -> str | None:
        return self.device.values.get(self.value_key)

    async def async_select_option(self, option: str) -> None:
        if option == HOLIDAY_OFF:
            # Leaving the "lock" variant needs the valve opened first.
            await self.coordinator.async_write(self.serial, CMD_OPEN_VALVE)
        await self.coordinator.async_write(
            self.serial, CMD_HOLIDAY_MODE, str(HOLIDAY_TO_RAW[option])
        )
        self.coordinator.set_optimistic(self.serial, self.value_key, option)
