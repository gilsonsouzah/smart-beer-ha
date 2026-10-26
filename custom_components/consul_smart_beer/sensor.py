"""Sensor platform for Consul Smart Beer integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from whirlpool.refrigerator import Refrigerator

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfMass,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SmartBeerConfigEntry, SmartBeerCoordinator
from .entity import SmartBeerEntity


def _parse_float(value: str | None) -> float | None:
    """Parse string to float, return None if invalid."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_int(value: str | None) -> int | None:
    """Parse string to int, return None if invalid."""
    if value is None:
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True, kw_only=True)
class SmartBeerSensorEntityDescription(SensorEntityDescription):
    """Describes a Consul Smart Beer sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any]


SENSOR_DESCRIPTIONS: tuple[SmartBeerSensorEntityDescription, ...] = (
    # Temperature sensor
    SmartBeerSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("temp"),
    ),
    # Content sensors (Lifekeeper)
    SmartBeerSensorEntityDescription(
        key="weight",
        translation_key="weight",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weight-gram",
        value_fn=lambda data: _parse_float(data.get("weight")),
    ),
    SmartBeerSensorEntityDescription(
        key="cans",
        translation_key="cans",
        icon="mdi:beer",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _parse_int(data.get("cans")),
    ),
    SmartBeerSensorEntityDescription(
        key="longnecks",
        translation_key="longnecks",
        icon="mdi:bottle-soda-classic",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _parse_int(data.get("longnecks")),
    ),
    SmartBeerSensorEntityDescription(
        key="bottles",
        translation_key="bottles",
        icon="mdi:bottle-wine",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _parse_int(data.get("bottles")),
    ),
    SmartBeerSensorEntityDescription(
        key="volume",
        translation_key="volume",
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cup-water",
        value_fn=lambda data: _parse_float(data.get("volume")),
    ),
    # Diagnostic sensors
    SmartBeerSensorEntityDescription(
        key="running_hours",
        translation_key="running_hours",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:clock-outline",
        value_fn=lambda data: _parse_int(data.get("running_hours")),
    ),
    SmartBeerSensorEntityDescription(
        key="wifi_rssi",
        translation_key="wifi_rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement="dBm",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:wifi",
        value_fn=lambda data: _parse_int(data.get("wifi_rssi")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartBeerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Consul Smart Beer sensors."""
    coordinator = entry.runtime_data
    
    entities: list[SmartBeerSensorEntity] = []
    
    for refrigerator in coordinator.refrigerators:
        for description in SENSOR_DESCRIPTIONS:
            entities.append(
                SmartBeerSensorEntity(coordinator, refrigerator, description)
            )
    
    async_add_entities(entities)


class SmartBeerSensorEntity(SmartBeerEntity, SensorEntity):
    """Representation of a Consul Smart Beer sensor."""

    entity_description: SmartBeerSensorEntityDescription

    def __init__(
        self,
        coordinator: SmartBeerCoordinator,
        refrigerator: Refrigerator,
        description: SmartBeerSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, refrigerator)
        self.entity_description = description
        self._attr_unique_id = f"{refrigerator.said}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        data = self.coordinator.data.get(self._refrigerator.said, {})
        return self.entity_description.value_fn(data)
