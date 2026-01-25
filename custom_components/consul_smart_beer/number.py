"""Number platform for Consul Smart Beer integration."""

from __future__ import annotations

from typing import Any

from whirlpool.refrigerator import Refrigerator

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SmartBeerConfigEntry, SmartBeerCoordinator
from .const import TEMP_MAP, TEMP_MAX, TEMP_MIN
from .entity import SmartBeerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartBeerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Consul Smart Beer number entities."""
    coordinator = entry.runtime_data
    
    entities: list[SmartBeerTemperatureNumber] = []
    
    for refrigerator in coordinator.refrigerators:
        entities.append(SmartBeerTemperatureNumber(coordinator, refrigerator))
    
    async_add_entities(entities)


class SmartBeerTemperatureNumber(SmartBeerEntity, NumberEntity):
    """Number entity for Consul Smart Beer target temperature."""

    _attr_native_min_value = TEMP_MIN
    _attr_native_max_value = TEMP_MAX
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = NumberMode.SLIDER
    _attr_translation_key = "target_temperature"
    _attr_icon = "mdi:thermometer"

    def __init__(
        self,
        coordinator: SmartBeerCoordinator,
        refrigerator: Refrigerator,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, refrigerator)
        self._attr_unique_id = f"{refrigerator.said}_target_temperature"

    @property
    def native_value(self) -> float | None:
        """Return the current temperature setting."""
        data = self.coordinator.data.get(self._refrigerator.said, {})
        temp = data.get("temp")
        if temp is not None:
            return float(temp)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the target temperature."""
        temp_int = int(value)
        
        # Validate temperature is one of the allowed values
        if temp_int not in TEMP_MAP:
            # Find the closest valid temperature
            valid_temps = list(TEMP_MAP.keys())
            temp_int = min(valid_temps, key=lambda x: abs(x - temp_int))
        
        await self._refrigerator.set_offset_temp(temp_int)
        await self.coordinator.async_request_refresh()
