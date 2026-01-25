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
    _parse_float,
    _parse_int,
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
            "weight": "4147.0",
            "cans": "6",
            "longnecks": "2",
            "bottles": "1",
            "volume": "3.41",
            "running_hours": "1960",
            "wifi_rssi": "-52",
            "door_open": False,
            "door_alarm": False,
            "power_outage": False,
        }
    }
    return coordinator


def test_parse_float():
    """Test float parsing helper."""
    assert _parse_float("4147.0") == 4147.0
    assert _parse_float("3.41") == 3.41
    assert _parse_float("0") == 0.0
    assert _parse_float(None) is None
    assert _parse_float("invalid") is None


def test_parse_int():
    """Test int parsing helper."""
    assert _parse_int("6") == 6
    assert _parse_int("1960") == 1960
    assert _parse_int("-52") == -52
    assert _parse_int("4147.0") == 4147  # Float string to int
    assert _parse_int(None) is None
    assert _parse_int("invalid") is None


def test_sensor_descriptions():
    """Test sensor descriptions are defined correctly."""
    assert len(SENSOR_DESCRIPTIONS) == 8
    
    # Temperature sensor
    temp_sensor = SENSOR_DESCRIPTIONS[0]
    assert temp_sensor.key == "temperature"
    assert temp_sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert temp_sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS
    
    # Weight sensor
    weight_sensor = SENSOR_DESCRIPTIONS[1]
    assert weight_sensor.key == "weight"
    assert weight_sensor.device_class == SensorDeviceClass.WEIGHT
    
    # Content sensors
    assert SENSOR_DESCRIPTIONS[2].key == "cans"
    assert SENSOR_DESCRIPTIONS[3].key == "longnecks"
    assert SENSOR_DESCRIPTIONS[4].key == "bottles"
    assert SENSOR_DESCRIPTIONS[5].key == "volume"
    
    # Diagnostic sensors
    assert SENSOR_DESCRIPTIONS[6].key == "running_hours"
    assert SENSOR_DESCRIPTIONS[7].key == "wifi_rssi"


def test_temperature_sensor_value(coordinator, mock_refrigerator):
    """Test temperature sensor returns correct value."""
    description = SENSOR_DESCRIPTIONS[0]  # Temperature sensor
    
    sensor = SmartBeerSensorEntity(coordinator, mock_refrigerator, description)
    
    assert sensor.native_value == -2
    assert sensor.unique_id == "TEST_SAID_12345_temperature"


def test_weight_sensor_value(coordinator, mock_refrigerator):
    """Test weight sensor returns correct value."""
    description = SENSOR_DESCRIPTIONS[1]  # Weight sensor
    
    sensor = SmartBeerSensorEntity(coordinator, mock_refrigerator, description)
    
    assert sensor.native_value == 4147.0
    assert sensor.unique_id == "TEST_SAID_12345_weight"


def test_cans_sensor_value(coordinator, mock_refrigerator):
    """Test cans sensor returns correct value."""
    description = SENSOR_DESCRIPTIONS[2]  # Cans sensor
    
    sensor = SmartBeerSensorEntity(coordinator, mock_refrigerator, description)
    
    assert sensor.native_value == 6
    assert sensor.unique_id == "TEST_SAID_12345_cans"


def test_wifi_rssi_sensor_value(coordinator, mock_refrigerator):
    """Test WiFi RSSI sensor returns correct value."""
    description = SENSOR_DESCRIPTIONS[7]  # WiFi RSSI sensor
    
    sensor = SmartBeerSensorEntity(coordinator, mock_refrigerator, description)
    
    assert sensor.native_value == -52
    assert sensor.unique_id == "TEST_SAID_12345_wifi_rssi"


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
