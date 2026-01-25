"""Tests for Consul Smart Beer binary sensor platform."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.consul_smart_beer.const import DOMAIN
from custom_components.consul_smart_beer import SmartBeerCoordinator
from custom_components.consul_smart_beer.binary_sensor import (
    SmartBeerBinarySensorEntity,
    BINARY_SENSOR_DESCRIPTIONS,
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
            "door_open": False,
            "door_alarm": False,
            "power_outage": False,
        }
    }
    return coordinator


def test_binary_sensor_descriptions():
    """Test binary sensor descriptions are defined correctly."""
    assert len(BINARY_SENSOR_DESCRIPTIONS) == 4
    
    # Online sensor
    online_sensor = BINARY_SENSOR_DESCRIPTIONS[0]
    assert online_sensor.key == "online"
    assert online_sensor.device_class == BinarySensorDeviceClass.CONNECTIVITY
    
    # Door sensor
    door_sensor = BINARY_SENSOR_DESCRIPTIONS[1]
    assert door_sensor.key == "door_open"
    assert door_sensor.device_class == BinarySensorDeviceClass.DOOR
    
    # Door alarm sensor
    door_alarm_sensor = BINARY_SENSOR_DESCRIPTIONS[2]
    assert door_alarm_sensor.key == "door_alarm"
    assert door_alarm_sensor.device_class == BinarySensorDeviceClass.PROBLEM
    
    # Power outage sensor
    power_sensor = BINARY_SENSOR_DESCRIPTIONS[3]
    assert power_sensor.key == "power_outage"
    assert power_sensor.device_class == BinarySensorDeviceClass.PROBLEM


def test_online_sensor_on(coordinator, mock_refrigerator):
    """Test online sensor shows on when device is online."""
    description = BINARY_SENSOR_DESCRIPTIONS[0]
    
    sensor = SmartBeerBinarySensorEntity(coordinator, mock_refrigerator, description)
    
    assert sensor.is_on is True
    assert sensor.unique_id == "TEST_SAID_12345_online"


def test_online_sensor_off(coordinator, mock_refrigerator):
    """Test online sensor shows off when device is offline."""
    coordinator.data["TEST_SAID_12345"]["online"] = False
    description = BINARY_SENSOR_DESCRIPTIONS[0]
    
    sensor = SmartBeerBinarySensorEntity(coordinator, mock_refrigerator, description)
    
    assert sensor.is_on is False


def test_door_sensor_closed(coordinator, mock_refrigerator):
    """Test door sensor shows off when door is closed."""
    description = BINARY_SENSOR_DESCRIPTIONS[1]  # door_open
    
    sensor = SmartBeerBinarySensorEntity(coordinator, mock_refrigerator, description)
    
    assert sensor.is_on is False
    assert sensor.unique_id == "TEST_SAID_12345_door_open"


def test_door_sensor_open(coordinator, mock_refrigerator):
    """Test door sensor shows on when door is open."""
    coordinator.data["TEST_SAID_12345"]["door_open"] = True
    description = BINARY_SENSOR_DESCRIPTIONS[1]
    
    sensor = SmartBeerBinarySensorEntity(coordinator, mock_refrigerator, description)
    
    assert sensor.is_on is True


def test_power_outage_sensor(coordinator, mock_refrigerator):
    """Test power outage sensor."""
    description = BINARY_SENSOR_DESCRIPTIONS[3]  # power_outage
    
    sensor = SmartBeerBinarySensorEntity(coordinator, mock_refrigerator, description)
    
    assert sensor.is_on is False
    assert sensor.unique_id == "TEST_SAID_12345_power_outage"
    
    # Test when power outage occurred
    coordinator.data["TEST_SAID_12345"]["power_outage"] = True
    assert sensor.is_on is True


def test_online_sensor_always_available(coordinator, mock_refrigerator):
    """Test online sensor is always available when coordinator is working."""
    # The connectivity sensor should be available even when device is offline
    coordinator.data["TEST_SAID_12345"]["online"] = False
    coordinator.last_update_success = True
    
    description = BINARY_SENSOR_DESCRIPTIONS[0]
    sensor = SmartBeerBinarySensorEntity(coordinator, mock_refrigerator, description)
    
    assert sensor.available is True


def test_binary_sensor_device_info(coordinator, mock_refrigerator):
    """Test binary sensor has correct device info."""
    description = BINARY_SENSOR_DESCRIPTIONS[0]
    sensor = SmartBeerBinarySensorEntity(coordinator, mock_refrigerator, description)
    
    device_info = sensor.device_info
    assert device_info is not None
    assert (DOMAIN, "TEST_SAID_12345") in device_info["identifiers"]
    assert device_info["manufacturer"] == "Consul"
    assert device_info["model"] == "Smart Beer"


def test_binary_sensor_has_entity_name(coordinator, mock_refrigerator):
    """Test binary sensor uses entity name."""
    description = BINARY_SENSOR_DESCRIPTIONS[0]
    sensor = SmartBeerBinarySensorEntity(coordinator, mock_refrigerator, description)
    
    assert sensor.has_entity_name is True
