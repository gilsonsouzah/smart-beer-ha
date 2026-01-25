"""Switch platform for Consul Smart Beer integration."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from whirlpool.refrigerator import Refrigerator

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SmartBeerConfigEntry, SmartBeerCoordinator
from .entity import SmartBeerEntity


@dataclass(frozen=True, kw_only=True)
class SmartBeerSwitchEntityDescription(SwitchEntityDescription):
    """Describes a Consul Smart Beer switch entity."""

    value_fn: Callable[[dict[str, Any]], bool | None]
    turn_on_fn: Callable[[Refrigerator], Coroutine[Any, Any, bool]]
    turn_off_fn: Callable[[Refrigerator], Coroutine[Any, Any, bool]]


SWITCH_DESCRIPTIONS: tuple[SmartBeerSwitchEntityDescription, ...] = (
    SmartBeerSwitchEntityDescription(
        key="turbo_mode",
        translation_key="turbo_mode",
        icon="mdi:snowflake-alert",
        value_fn=lambda data: data.get("turbo_mode"),
        turn_on_fn=lambda r: r.set_turbo_mode(True),
        turn_off_fn=lambda r: r.set_turbo_mode(False),
    ),
    SmartBeerSwitchEntityDescription(
        key="display_lock",
        translation_key="display_lock",
        icon="mdi:lock",
        value_fn=lambda data: data.get("display_lock"),
        turn_on_fn=lambda r: r.set_display_lock(True),
        turn_off_fn=lambda r: r.set_display_lock(False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartBeerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Consul Smart Beer switches."""
    coordinator = entry.runtime_data
    
    entities: list[SmartBeerSwitchEntity] = []
    
    for refrigerator in coordinator.refrigerators:
        for description in SWITCH_DESCRIPTIONS:
            entities.append(
                SmartBeerSwitchEntity(coordinator, refrigerator, description)
            )
    
    async_add_entities(entities)


class SmartBeerSwitchEntity(SmartBeerEntity, SwitchEntity):
    """Representation of a Consul Smart Beer switch."""

    entity_description: SmartBeerSwitchEntityDescription

    def __init__(
        self,
        coordinator: SmartBeerCoordinator,
        refrigerator: Refrigerator,
        description: SmartBeerSwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, refrigerator)
        self.entity_description = description
        self._attr_unique_id = f"{refrigerator.said}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return True if the switch is on."""
        data = self.coordinator.data.get(self._refrigerator.said, {})
        return self.entity_description.value_fn(data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.entity_description.turn_on_fn(self._refrigerator)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.entity_description.turn_off_fn(self._refrigerator)
        await self.coordinator.async_request_refresh()
