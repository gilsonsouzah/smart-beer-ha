"""Tests for Consul Smart Beer switch platform."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.consul_smart_beer.const import DOMAIN
from custom_components.consul_smart_beer import SmartBeerCoordinator
from custom_components.consul_smart_beer.switch import (
    SmartBeerSwitchEntity,
    SWITCH_DESCRIPTIONS,
)


@pytest.fixture
def coordinator(hass: HomeAssistant, mock_appliances_manager, mock_auth):
    """Create a test coordinator."""
    coordinator = SmartBeerCoordinator(hass, mock_appliances_manager, mock_auth)
    coordinator.data = {
        "TEST_SAID_12345": {
            "temp": -2,
            "temp_raw": 11,
            "turbo_mode": False,
            "display_lock": False,
            "online": True,
            "name": "Smart Beer Test",
            "said": "TEST_SAID_12345",
        }
    }
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


def test_switch_descriptions():
    """Test switch descriptions are defined correctly."""
    assert len(SWITCH_DESCRIPTIONS) == 2
    
    happy_hour_switch = next(s for s in SWITCH_DESCRIPTIONS if s.key == "happy_hour")
    assert happy_hour_switch.icon == "mdi:party-popper"
    
    lock_switch = next(s for s in SWITCH_DESCRIPTIONS if s.key == "display_lock")
    assert lock_switch.icon == "mdi:lock"


def test_happy_hour_switch_off(coordinator, mock_refrigerator):
    """Test happy hour switch shows off state."""
    description = next(s for s in SWITCH_DESCRIPTIONS if s.key == "happy_hour")
    
    switch = SmartBeerSwitchEntity(coordinator, mock_refrigerator, description)
    
    assert switch.is_on is False
    assert switch.unique_id == "TEST_SAID_12345_happy_hour"


def test_happy_hour_switch_on(coordinator, mock_refrigerator):
    """Test happy hour switch shows on state."""
    coordinator.data["TEST_SAID_12345"]["turbo_mode"] = True
    description = next(s for s in SWITCH_DESCRIPTIONS if s.key == "happy_hour")
    
    switch = SmartBeerSwitchEntity(coordinator, mock_refrigerator, description)
    
    assert switch.is_on is True


async def test_turn_on_happy_hour(coordinator, mock_refrigerator):
    """Test turning on happy hour."""
    description = next(s for s in SWITCH_DESCRIPTIONS if s.key == "happy_hour")
    switch = SmartBeerSwitchEntity(coordinator, mock_refrigerator, description)
    
    await switch.async_turn_on()
    
    mock_refrigerator.set_turbo_mode.assert_called_once_with(True)
    coordinator.async_request_refresh.assert_called_once()


async def test_turn_off_happy_hour(coordinator, mock_refrigerator):
    """Test turning off happy hour."""
    description = next(s for s in SWITCH_DESCRIPTIONS if s.key == "happy_hour")
    switch = SmartBeerSwitchEntity(coordinator, mock_refrigerator, description)
    
    await switch.async_turn_off()
    
    mock_refrigerator.set_turbo_mode.assert_called_once_with(False)
    coordinator.async_request_refresh.assert_called_once()


def test_display_lock_switch_off(coordinator, mock_refrigerator):
    """Test display lock switch shows off state."""
    description = next(s for s in SWITCH_DESCRIPTIONS if s.key == "display_lock")
    
    switch = SmartBeerSwitchEntity(coordinator, mock_refrigerator, description)
    
    assert switch.is_on is False
    assert switch.unique_id == "TEST_SAID_12345_display_lock"


async def test_turn_on_display_lock(coordinator, mock_refrigerator):
    """Test turning on display lock."""
    description = next(s for s in SWITCH_DESCRIPTIONS if s.key == "display_lock")
    switch = SmartBeerSwitchEntity(coordinator, mock_refrigerator, description)
    
    await switch.async_turn_on()
    
    mock_refrigerator.set_display_lock.assert_called_once_with(True)


async def test_turn_off_display_lock(coordinator, mock_refrigerator):
    """Test turning off display lock."""
    description = next(s for s in SWITCH_DESCRIPTIONS if s.key == "display_lock")
    switch = SmartBeerSwitchEntity(coordinator, mock_refrigerator, description)
    
    await switch.async_turn_off()
    
    mock_refrigerator.set_display_lock.assert_called_once_with(False)


def test_switch_device_info(coordinator, mock_refrigerator):
    """Test switch has correct device info."""
    description = SWITCH_DESCRIPTIONS[0]
    switch = SmartBeerSwitchEntity(coordinator, mock_refrigerator, description)
    
    device_info = switch.device_info
    assert device_info is not None
    assert device_info["manufacturer"] == "Consul"
    assert device_info["model"] == "Smart Beer"
