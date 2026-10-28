"""Leakage protection valve for JUDO myjudo."""

from __future__ import annotations

from homeassistant.components.valve import (
    ValveDeviceClass,
    ValveEntity,
    ValveEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import CMD_CLOSE_VALVE, CMD_OPEN_VALVE
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
        JudoValve(coordinator, serial, "valve")
        for serial in coordinator.data
        if has_value(coordinator, serial, "valve_closed")
    )


class JudoValve(JudoEntity, ValveEntity):
    """Main water valve of the leakage protection."""

    _attr_device_class = ValveDeviceClass.WATER
    _attr_supported_features = ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE
    _attr_reports_position = False
    value_key = "valve_closed"

    @property
    def is_closed(self) -> bool | None:
        return self.device.values.get(self.value_key)

    async def async_open_valve(self) -> None:
        await self.coordinator.async_write(self.serial, CMD_OPEN_VALVE)
        self.coordinator.set_optimistic(self.serial, self.value_key, False)

    async def async_close_valve(self) -> None:
        await self.coordinator.async_write(self.serial, CMD_CLOSE_VALVE)
        self.coordinator.set_optimistic(self.serial, self.value_key, True)
