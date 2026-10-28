"""Number entities for JUDO myjudo."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import math

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfMass,
    UnitOfTime,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import (
    CMD_EXTRACTION_QUANTITY,
    CMD_EXTRACTION_TIME,
    CMD_MAX_FLOW,
    CMD_OPEN_VALVE,
    CMD_OUTPUT_HARDNESS,
    CMD_SALT_STOCK,
    CMD_SLEEP_MODE,
    le_hex,
)
from .const import (
    CONF_SODIUM_INPUT,
    CONF_SODIUM_LIMIT,
    DEFAULT_SODIUM_LIMIT,
    DOMAIN,
    SODIUM_PER_DH,
)
from .coordinator import JudoConfigEntry, JudoCoordinator
from .entity import JudoEntity, has_value
from .sensor import HARDNESS

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class JudoNumberDescription(NumberEntityDescription):
    """Writable register. `write` sends the value, returns nothing."""

    write: Callable[[JudoCoordinator, str, float], Awaitable[None]]


def _register(
    index: int, bits: int, factor: float = 1
) -> Callable[[JudoCoordinator, str, float], Awaitable[None]]:
    async def write(coordinator: JudoCoordinator, serial: str, value: float) -> None:
        await coordinator.async_write(
            serial, index, le_hex(round(value * factor), bits)
        )

    return write


async def _write_sleep_mode(
    coordinator: JudoCoordinator, serial: str, value: float
) -> None:
    hours = int(value)
    if hours == 0:
        # Opening the valve ends the sleep mode.
        await coordinator.async_write(serial, CMD_OPEN_VALVE)
        return
    # First set the duration, then an empty write starts the sleep mode.
    await coordinator.async_write(serial, CMD_SLEEP_MODE, str(hours))
    await coordinator.async_write(serial, CMD_SLEEP_MODE)


async def _write_hardness(
    coordinator: JudoCoordinator, serial: str, value: float
) -> None:
    target = int(value)
    options = coordinator.config_entry.options
    sodium_input = options.get(CONF_SODIUM_INPUT, 0)
    input_hardness = coordinator.data[serial].values.get("input_hardness")
    if sodium_input and input_hardness:
        limit = options.get(CONF_SODIUM_LIMIT, DEFAULT_SODIUM_LIMIT)
        sodium = (input_hardness - target) * SODIUM_PER_DH + sodium_input
        if sodium >= limit:
            minimum = math.ceil(input_hardness - (limit - sodium_input) / SODIUM_PER_DH)
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="sodium_limit",
                translation_placeholders={
                    "sodium": f"{sodium:.1f}",
                    "limit": f"{limit:g}",
                    "minimum": str(minimum),
                },
            )
    await coordinator.async_write(serial, CMD_OUTPUT_HARDNESS, le_hex(target, 8))


NUMBERS: tuple[JudoNumberDescription, ...] = (
    JudoNumberDescription(
        key="output_hardness",
        native_min_value=1,
        native_max_value=30,
        native_step=1,
        native_unit_of_measurement=HARDNESS,
        write=_write_hardness,
    ),
    JudoNumberDescription(
        key="salt_stock",
        device_class=NumberDeviceClass.WEIGHT,
        native_min_value=0,
        native_max_value=50,
        native_step=0.5,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        mode=NumberMode.BOX,
        write=_register(CMD_SALT_STOCK, 16, 1000),
    ),
    JudoNumberDescription(
        key="sleep_mode",
        device_class=NumberDeviceClass.DURATION,
        native_min_value=0,
        native_max_value=10,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.HOURS,
        write=_write_sleep_mode,
    ),
    JudoNumberDescription(
        key="max_flow",
        device_class=NumberDeviceClass.VOLUME_FLOW_RATE,
        native_min_value=500,
        native_max_value=5000,
        native_step=500,
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_HOUR,
        entity_category=EntityCategory.CONFIG,
        mode=NumberMode.BOX,
        write=_register(CMD_MAX_FLOW, 16),
    ),
    JudoNumberDescription(
        key="extraction_quantity",
        device_class=NumberDeviceClass.VOLUME,
        native_min_value=100,
        native_max_value=3000,
        native_step=100,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        entity_category=EntityCategory.CONFIG,
        mode=NumberMode.BOX,
        write=_register(CMD_EXTRACTION_QUANTITY, 16),
    ),
    JudoNumberDescription(
        key="extraction_time",
        device_class=NumberDeviceClass.DURATION,
        native_min_value=10,
        native_max_value=600,
        native_step=10,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.CONFIG,
        mode=NumberMode.BOX,
        write=_register(CMD_EXTRACTION_TIME, 16),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JudoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        JudoNumber(coordinator, serial, desc)
        for serial in coordinator.data
        for desc in NUMBERS
        if has_value(coordinator, serial, desc.key)
    )


class JudoNumber(JudoEntity, NumberEntity):
    """Writable setting of the device."""

    entity_description: JudoNumberDescription

    def __init__(
        self,
        coordinator: JudoCoordinator,
        serial: str,
        description: JudoNumberDescription,
    ) -> None:
        super().__init__(coordinator, serial, description.key)
        self.entity_description = description
        self.value_key = description.key

    @property
    def native_value(self) -> float | None:
        return self.device.values.get(self.value_key)

    async def async_set_native_value(self, value: float) -> None:
        await self.entity_description.write(self.coordinator, self.serial, value)
        # Polled values are ints for whole numbers; keep the optimistic one alike.
        self.coordinator.set_optimistic(
            self.serial, self.value_key, int(value) if value.is_integer() else value
        )
