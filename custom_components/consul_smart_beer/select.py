"""Select platform for Consul Smart Beer integration."""

from __future__ import annotations

from whirlpool.refrigerator import Refrigerator

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SmartBeerConfigEntry, SmartBeerCoordinator
from .const import TEMP_MAP
from .entity import SmartBeerEntity

# Options for temperature selection (display value -> actual value)
TEMPERATURE_OPTIONS: dict[str, int] = {
    "-4°C (Mais gelado)": -4,
    "-2°C": -2,
    "0°C": 0,
    "3°C": 3,
    "5°C (Menos gelado)": 5,
}

# Reverse lookup
TEMPERATURE_OPTIONS_REVERSE: dict[int, str] = {v: k for k, v in TEMPERATURE_OPTIONS.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartBeerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Consul Smart Beer select entities."""
    coordinator = entry.runtime_data

    entities: list[SmartBeerTemperatureSelect] = []

    for refrigerator in coordinator.refrigerators:
        entities.append(SmartBeerTemperatureSelect(coordinator, refrigerator))

    async_add_entities(entities)


class SmartBeerTemperatureSelect(SmartBeerEntity, SelectEntity):
    """Select entity for Consul Smart Beer target temperature."""

    _attr_translation_key = "target_temperature"
    _attr_icon = "mdi:thermometer"
    _attr_options = list(TEMPERATURE_OPTIONS.keys())

    def __init__(
        self,
        coordinator: SmartBeerCoordinator,
        refrigerator: Refrigerator,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, refrigerator)
        self._attr_unique_id = f"{refrigerator.said}_target_temperature"

    @property
    def current_option(self) -> str | None:
        """Return the current temperature option."""
        data = self.coordinator.data.get(self._refrigerator.said, {})
        temp = data.get("temp")
        if temp is not None and temp in TEMPERATURE_OPTIONS_REVERSE:
            return TEMPERATURE_OPTIONS_REVERSE[temp]
        return None

    async def async_select_option(self, option: str) -> None:
        """Set the target temperature."""
        temp = TEMPERATURE_OPTIONS.get(option)
        if temp is not None:
            await self._refrigerator.set_offset_temp(temp)
            await self.coordinator.async_request_refresh()
