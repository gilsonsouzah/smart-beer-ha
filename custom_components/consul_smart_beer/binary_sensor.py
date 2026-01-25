"""Binary sensor platform for Consul Smart Beer integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from whirlpool.refrigerator import Refrigerator

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SmartBeerConfigEntry, SmartBeerCoordinator
from .entity import SmartBeerEntity


@dataclass(frozen=True, kw_only=True)
class SmartBeerBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Consul Smart Beer binary sensor entity."""

    value_fn: Callable[[dict[str, Any]], bool | None]


BINARY_SENSOR_DESCRIPTIONS: tuple[SmartBeerBinarySensorEntityDescription, ...] = (
    SmartBeerBinarySensorEntityDescription(
        key="online",
        translation_key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda data: data.get("online"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartBeerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Consul Smart Beer binary sensors."""
    coordinator = entry.runtime_data
    
    entities: list[SmartBeerBinarySensorEntity] = []
    
    for refrigerator in coordinator.refrigerators:
        for description in BINARY_SENSOR_DESCRIPTIONS:
            entities.append(
                SmartBeerBinarySensorEntity(coordinator, refrigerator, description)
            )
    
    async_add_entities(entities)


class SmartBeerBinarySensorEntity(SmartBeerEntity, BinarySensorEntity):
    """Representation of a Consul Smart Beer binary sensor."""

    entity_description: SmartBeerBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: SmartBeerCoordinator,
        refrigerator: Refrigerator,
        description: SmartBeerBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, refrigerator)
        self.entity_description = description
        self._attr_unique_id = f"{refrigerator.said}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return True if the binary sensor is on."""
        data = self.coordinator.data.get(self._refrigerator.said, {})
        return self.entity_description.value_fn(data)

    @property
    def available(self) -> bool:
        """Return True if entity is available (override for connectivity sensor)."""
        # The connectivity sensor should always be available if coordinator is available
        if self.entity_description.key == "online":
            return self.coordinator.last_update_success
        return super().available
