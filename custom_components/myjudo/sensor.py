"""Sensors for JUDO myjudo."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfTime,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .api import JudoDevice
from .const import MESSAGE_CODES
from .coordinator import JudoConfigEntry, JudoCoordinator
from .entity import JudoEntity, has_value

PARALLEL_UPDATES = 0
HARDNESS = "°dH"


@dataclass(frozen=True, kw_only=True)
class JudoSensorDescription(SensorEntityDescription):
    """Sensor reading one parsed value."""


def _water(key: str) -> JudoSensorDescription:
    return JudoSensorDescription(
        key=key,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        suggested_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        suggested_display_precision=3,
    )


SENSORS: tuple[JudoSensorDescription, ...] = (
    _water("total_water"),
    _water("soft_water"),
    _water("hard_water"),
    JudoSensorDescription(
        key="water_flow",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_HOUR,
    ),
    JudoSensorDescription(key="input_hardness", native_unit_of_measurement=HARDNESS),
    JudoSensorDescription(
        key="salt_range",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
    ),
    JudoSensorDescription(
        key="next_service",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
    ),
    JudoSensorDescription(
        key="regeneration_count", state_class=SensorStateClass.TOTAL_INCREASING
    ),
    JudoSensorDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JudoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = []
    for serial in coordinator.data:
        entities.extend(
            JudoSensor(coordinator, serial, desc)
            for desc in SENSORS
            if has_value(coordinator, serial, desc.key)
        )
        entities.append(JudoMessageSensor(coordinator, serial, "last_message"))
        entities.append(
            JudoTimestampSensor(
                coordinator,
                serial,
                "last_message_time",
                lambda d: d.message and d.message.timestamp,
            )
        )
        entities.append(
            JudoTimestampSensor(
                coordinator, serial, "last_update", lambda d: d.last_update
            )
        )
        if has_value(coordinator, serial, "regeneration_count"):
            entities.append(
                JudoLastRegenerationSensor(coordinator, serial, "last_regeneration")
            )
    async_add_entities(entities)


class JudoSensor(JudoEntity, SensorEntity):
    """Plain value sensor."""

    entity_description: JudoSensorDescription

    def __init__(
        self,
        coordinator: JudoCoordinator,
        serial: str,
        description: JudoSensorDescription,
    ) -> None:
        super().__init__(coordinator, serial, description.key)
        self.entity_description = description
        self.value_key = description.key

    @property
    def native_value(self) -> Any:
        return self.device.values.get(self.value_key)


class JudoTimestampSensor(JudoEntity, SensorEntity):
    """Timestamp taken from the device data."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: JudoCoordinator,
        serial: str,
        key: str,
        getter: Callable[[JudoDevice], datetime | None],
    ) -> None:
        super().__init__(coordinator, serial, key)
        self._getter = getter

    @property
    def native_value(self) -> datetime | None:
        return self._getter(self.device) or None


class JudoMessageSensor(JudoEntity, SensorEntity):
    """Latest entry of the device message log."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = MESSAGE_CODES

    @property
    def native_value(self) -> str | None:
        msg = self.device.message
        if msg is None:
            return None
        code = f"{msg.type}_{msg.code}"
        return code if code in MESSAGE_CODES else "other"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        msg = self.device.message
        if msg is None:
            return None
        return {"type": msg.type, "code": msg.code, "message_id": msg.id}


class JudoLastRegenerationSensor(JudoEntity, RestoreSensor):
    """When the regeneration counter last went up.

    The cloud does not report this, so it is tracked locally and survives
    restarts. It stays empty until the first regeneration after setup.
    """

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    value_key = "regeneration_count"

    def __init__(self, coordinator: JudoCoordinator, serial: str, key: str) -> None:
        super().__init__(coordinator, serial, key)
        self._last_count: int | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._last_count = last_state.attributes.get("regeneration_count")
        if (last := await self.async_get_last_sensor_data()) is not None and isinstance(
            last.native_value, datetime
        ):
            self._attr_native_value = last.native_value
        self._track()

    def _track(self) -> None:
        count = self.device.values.get("regeneration_count")
        if count is None:
            return
        if self._last_count is not None and count > self._last_count:
            self._attr_native_value = dt_util.utcnow()
        self._last_count = count

    @callback
    def _handle_coordinator_update(self) -> None:
        self._track()
        super()._handle_coordinator_update()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"regeneration_count": self._last_count}
