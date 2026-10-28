"""Buttons for JUDO myjudo."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import CMD_START_REGENERATION
from .coordinator import JudoConfigEntry
from .entity import JudoEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JudoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        JudoRegenerationButton(coordinator, serial, "start_regeneration")
        for serial in coordinator.data
    )


class JudoRegenerationButton(JudoEntity, ButtonEntity):
    """Start a regeneration."""

    async def async_press(self) -> None:
        await self.coordinator.async_write(self.serial, CMD_START_REGENERATION)
        self.coordinator.set_optimistic(self.serial, "regeneration_running", True)
