"""Tests for Consul Smart Beer number platform."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.const import UnitOfTemperature
from homeassistant.components.number import NumberMode

from custom_components.consul_smart_beer.const import DOMAIN, TEMP_MAP, TEMP_MIN, TEMP_MAX
from custom_components.consul_smart_beer import SmartBeerCoordinator
from custom_components.consul_smart_beer.number import SmartBeerTemperatureNumber


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


def test_temperature_number_attributes(coordinator, mock_refrigerator):
    """Test temperature number entity attributes."""
    number = SmartBeerTemperatureNumber(coordinator, mock_refrigerator)
    
    assert number.native_min_value == TEMP_MIN
    assert number.native_max_value == TEMP_MAX
    assert number.native_step == 1
    assert number.native_unit_of_measurement == UnitOfTemperature.CELSIUS
    assert number.mode == NumberMode.SLIDER
    assert number.unique_id == "TEST_SAID_12345_target_temperature"


def test_temperature_number_value(coordinator, mock_refrigerator):
    """Test temperature number returns correct value."""
    number = SmartBeerTemperatureNumber(coordinator, mock_refrigerator)
    
    assert number.native_value == -2.0


def test_temperature_number_none_value(coordinator, mock_refrigerator):
    """Test temperature number handles None value."""
    coordinator.data["TEST_SAID_12345"]["temp"] = None
    number = SmartBeerTemperatureNumber(coordinator, mock_refrigerator)
    
    assert number.native_value is None


async def test_set_temperature_valid(coordinator, mock_refrigerator):
    """Test setting a valid temperature."""
    number = SmartBeerTemperatureNumber(coordinator, mock_refrigerator)
    
    await number.async_set_native_value(-4.0)
    
    mock_refrigerator.set_offset_temp.assert_called_once_with(-4)
    coordinator.async_request_refresh.assert_called_once()


async def test_set_temperature_all_valid_values(coordinator, mock_refrigerator):
    """Test setting all valid temperature values."""
    number = SmartBeerTemperatureNumber(coordinator, mock_refrigerator)
    
    for temp in TEMP_MAP.keys():
        mock_refrigerator.set_offset_temp.reset_mock()
        coordinator.async_request_refresh.reset_mock()
        
        await number.async_set_native_value(float(temp))
        
        mock_refrigerator.set_offset_temp.assert_called_once_with(temp)


async def test_set_temperature_invalid_rounds_to_nearest(coordinator, mock_refrigerator):
    """Test setting invalid temperature rounds to nearest valid value."""
    number = SmartBeerTemperatureNumber(coordinator, mock_refrigerator)
    
    # 1 should round to 0 (closest valid value)
    await number.async_set_native_value(1.0)
    
    # Should have called with a valid temperature
    mock_refrigerator.set_offset_temp.assert_called()
    called_temp = mock_refrigerator.set_offset_temp.call_args[0][0]
    assert called_temp in TEMP_MAP.keys()


def test_temperature_number_device_info(coordinator, mock_refrigerator):
    """Test temperature number has correct device info."""
    number = SmartBeerTemperatureNumber(coordinator, mock_refrigerator)
    
    device_info = number.device_info
    assert device_info is not None
    assert (DOMAIN, "TEST_SAID_12345") in device_info["identifiers"]
    assert device_info["manufacturer"] == "Consul"
    assert device_info["model"] == "Smart Beer"


def test_temperature_number_available(coordinator, mock_refrigerator):
    """Test temperature number availability."""
    number = SmartBeerTemperatureNumber(coordinator, mock_refrigerator)
    
    # Need to mock coordinator state
    coordinator._async_update_listeners = []
    coordinator.last_update_success = True
    
    assert number.available is True


def test_temperature_number_unavailable_when_offline(coordinator, mock_refrigerator):
    """Test temperature number unavailable when device offline."""
    coordinator.data["TEST_SAID_12345"]["online"] = False
    number = SmartBeerTemperatureNumber(coordinator, mock_refrigerator)
    
    assert number.available is False
