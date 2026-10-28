"""Base entity for JUDO myjudo."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import JudoDevice
from .const import DOMAIN, MANUFACTURER
from .coordinator import JudoCoordinator


class JudoEntity(CoordinatorEntity[JudoCoordinator]):
    """Entity bound to one device of the account."""

    _attr_has_entity_name = True
    # Key in JudoDevice.values; None for entities that do not read a value.
    value_key: str | None = None

    def __init__(self, coordinator: JudoCoordinator, serial: str, key: str) -> None:
        super().__init__(coordinator)
        self.serial = serial
        self._attr_unique_id = f"{serial}_{key}"
        self._attr_translation_key = key
        device = coordinator.data[serial]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            manufacturer=MANUFACTURER,
            name=MANUFACTURER,
            model="SOFTwell P" if coordinator.softwell_p else None,
            model_id=device.dt or None,
            serial_number=serial,
            sw_version=device.sw_version,
            hw_version=device.hw_version,
        )

    @property
    def device(self) -> JudoDevice:
        return self.coordinator.data[self.serial]

    @property
    def available(self) -> bool:
        if not super().available or self.serial not in self.coordinator.data:
            return False
        if self.value_key is None:
            return True
        return self.device.values.get(self.value_key) is not None


def has_value(coordinator: JudoCoordinator, serial: str, key: str) -> bool:
    """Only create entities for values the device actually reports."""
    return coordinator.data[serial].values.get(key) is not None
