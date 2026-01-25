"""Tests for Consul Smart Beer sensor platform."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.const import UnitOfTemperature
from homeassistant.components.sensor import SensorDeviceClass

from custom_components.consul_smart_beer.const import DOMAIN
from custom_components.consul_smart_beer import SmartBeerCoordinator
from custom_components.consul_smart_beer.sensor import (
    SmartBeerSensorEntity,
    SENSOR_DESCRIPTIONS,
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
    return coordinator


def test_sensor_descriptions():
    """Test sensor descriptions are defined correctly."""
    assert len(SENSOR_DESCRIPTIONS) > 0
    
    temp_sensor = SENSOR_DESCRIPTIONS[0]
    assert temp_sensor.key == "temperature"
    assert temp_sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert temp_sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS


def test_temperature_sensor_value(coordinator, mock_refrigerator):
    """Test temperature sensor returns correct value."""
    description = SENSOR_DESCRIPTIONS[0]  # Temperature sensor
    
    sensor = SmartBeerSensorEntity(coordinator, mock_refrigerator, description)
    
    assert sensor.native_value == -2
    assert sensor.unique_id == "TEST_SAID_12345_temperature"


def test_temperature_sensor_unavailable(coordinator, mock_refrigerator):
    """Test temperature sensor shows unavailable when offline."""
    # Set device to offline
    coordinator.data["TEST_SAID_12345"]["online"] = False
    
    description = SENSOR_DESCRIPTIONS[0]
    sensor = SmartBeerSensorEntity(coordinator, mock_refrigerator, description)
    
    assert sensor.available is False


def test_temperature_sensor_available(coordinator, mock_refrigerator):
    """Test temperature sensor shows available when online."""
    description = SENSOR_DESCRIPTIONS[0]
    sensor = SmartBeerSensorEntity(coordinator, mock_refrigerator, description)
    
    # Mock that coordinator update was successful
    coordinator._async_update_listeners = []
    coordinator.last_update_success = True
    
    assert sensor.available is True


def test_sensor_device_info(coordinator, mock_refrigerator):
    """Test sensor has correct device info."""
    description = SENSOR_DESCRIPTIONS[0]
    sensor = SmartBeerSensorEntity(coordinator, mock_refrigerator, description)
    
    device_info = sensor.device_info
    assert device_info is not None
    assert (DOMAIN, "TEST_SAID_12345") in device_info["identifiers"]
    assert device_info["manufacturer"] == "Consul"
    assert device_info["model"] == "Smart Beer"


def test_sensor_has_entity_name(coordinator, mock_refrigerator):
    """Test sensor uses entity name."""
    description = SENSOR_DESCRIPTIONS[0]
    sensor = SmartBeerSensorEntity(coordinator, mock_refrigerator, description)
    
    assert sensor.has_entity_name is True
