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
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SmartBeerConfigEntry, SmartBeerCoordinator
from .entity import SmartBeerEntity


@dataclass(frozen=True, kw_only=True)
class SmartBeerSensorEntityDescription(SensorEntityDescription):
    """Describes a Consul Smart Beer sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any]


SENSOR_DESCRIPTIONS: tuple[SmartBeerSensorEntityDescription, ...] = (
    SmartBeerSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("temp"),
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
