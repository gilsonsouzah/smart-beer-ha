"""Base entity for Consul Smart Beer integration."""

from __future__ import annotations

from whirlpool.refrigerator import Refrigerator

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SmartBeerCoordinator
from .const import DOMAIN


class SmartBeerEntity(CoordinatorEntity[SmartBeerCoordinator]):
    """Base class for Consul Smart Beer entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SmartBeerCoordinator,
        refrigerator: Refrigerator,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._refrigerator = refrigerator
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, refrigerator.said)},
            name=refrigerator.name or "Smart Beer",
            manufacturer="Consul",
            model="Smart Beer",
            model_id=refrigerator.appliance_info.model_number or None,
            serial_number=refrigerator.appliance_info.serial_number or None,
        )

    @property
    def refrigerator(self) -> Refrigerator:
        """Return the refrigerator instance."""
        return self._refrigerator

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available:
            return False
        # Check if device is online
        data = self.coordinator.data.get(self._refrigerator.said, {})
        return data.get("online", False)
