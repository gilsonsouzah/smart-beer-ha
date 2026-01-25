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
from homeassistant.const import EntityCategory
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
    SmartBeerBinarySensorEntityDescription(
        key="door_open",
        translation_key="door_open",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:door",
        value_fn=lambda data: data.get("door_open"),
    ),
    SmartBeerBinarySensorEntityDescription(
        key="door_alarm",
        translation_key="door_alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:door-open",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("door_alarm"),
    ),
    SmartBeerBinarySensorEntityDescription(
        key="power_outage",
        translation_key="power_outage",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:power-plug-off",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("power_outage"),
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
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes for debugging."""
        # Only add raw attributes to the online/connectivity sensor
        if self.entity_description.key == "online":
            data = self.coordinator.data.get(self._refrigerator.said, {})
            raw_attrs = data.get("raw_attributes", {})
            if raw_attrs:
                return {"raw_api_data": raw_attrs}
        return None

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
