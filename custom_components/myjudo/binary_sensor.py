"""Binary sensors for JUDO myjudo."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import JudoConfigEntry
from .entity import JudoEntity, has_value

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JudoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = []
    for serial in coordinator.data:
        entities.append(JudoOnlineSensor(coordinator, serial, "online"))
        if has_value(coordinator, serial, "regeneration_running"):
            entities.append(
                JudoRegenerationSensor(coordinator, serial, "regeneration_running")
            )
    async_add_entities(entities)


class JudoOnlineSensor(JudoEntity, BinarySensorEntity):
    """Whether the device is connected to the cloud."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool:
        return self.device.online


class JudoRegenerationSensor(JudoEntity, BinarySensorEntity):
    """Regeneration in progress."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    value_key = "regeneration_running"

    @property
    def is_on(self) -> bool | None:
        return self.device.values.get(self.value_key)
