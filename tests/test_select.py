"""Tests for Consul Smart Beer select platform."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.consul_smart_beer.const import DOMAIN, TEMP_MAP
from custom_components.consul_smart_beer import SmartBeerCoordinator
from custom_components.consul_smart_beer.select import (
    SmartBeerTemperatureSelect,
    TEMPERATURE_OPTIONS,
    TEMPERATURE_OPTIONS_REVERSE,
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


def test_temperature_options_defined():
    """Test temperature options are correctly defined."""
    assert len(TEMPERATURE_OPTIONS) == 5
    assert TEMPERATURE_OPTIONS["-4°C (Mais gelado)"] == -4
    assert TEMPERATURE_OPTIONS["-2°C"] == -2
    assert TEMPERATURE_OPTIONS["0°C"] == 0
    assert TEMPERATURE_OPTIONS["3°C"] == 3
    assert TEMPERATURE_OPTIONS["5°C (Menos gelado)"] == 5


def test_temperature_options_reverse():
    """Test reverse temperature options mapping."""
    assert TEMPERATURE_OPTIONS_REVERSE[-4] == "-4°C (Mais gelado)"
    assert TEMPERATURE_OPTIONS_REVERSE[-2] == "-2°C"
    assert TEMPERATURE_OPTIONS_REVERSE[0] == "0°C"
    assert TEMPERATURE_OPTIONS_REVERSE[3] == "3°C"
    assert TEMPERATURE_OPTIONS_REVERSE[5] == "5°C (Menos gelado)"


def test_temperature_select_attributes(coordinator, mock_refrigerator):
    """Test temperature select entity attributes."""
    select = SmartBeerTemperatureSelect(coordinator, mock_refrigerator)

    assert select.unique_id == "TEST_SAID_12345_target_temperature"
    assert select.icon == "mdi:thermometer"
    assert len(select.options) == 5


def test_temperature_select_current_option(coordinator, mock_refrigerator):
    """Test temperature select returns correct current option."""
    select = SmartBeerTemperatureSelect(coordinator, mock_refrigerator)

    assert select.current_option == "-2°C"


def test_temperature_select_current_option_all_values(coordinator, mock_refrigerator):
    """Test temperature select returns correct option for all valid temperatures."""
    select = SmartBeerTemperatureSelect(coordinator, mock_refrigerator)

    for temp, label in TEMPERATURE_OPTIONS_REVERSE.items():
        coordinator.data["TEST_SAID_12345"]["temp"] = temp
        assert select.current_option == label


def test_temperature_select_none_value(coordinator, mock_refrigerator):
    """Test temperature select handles None value."""
    coordinator.data["TEST_SAID_12345"]["temp"] = None
    select = SmartBeerTemperatureSelect(coordinator, mock_refrigerator)

    assert select.current_option is None


def test_temperature_select_invalid_value(coordinator, mock_refrigerator):
    """Test temperature select handles invalid temperature value."""
    coordinator.data["TEST_SAID_12345"]["temp"] = 99  # Invalid value
    select = SmartBeerTemperatureSelect(coordinator, mock_refrigerator)

    assert select.current_option is None


async def test_select_option(coordinator, mock_refrigerator):
    """Test selecting a temperature option."""
    select = SmartBeerTemperatureSelect(coordinator, mock_refrigerator)

    await select.async_select_option("-4°C (Mais gelado)")

    mock_refrigerator.set_offset_temp.assert_called_once_with(-4)
    coordinator.async_request_refresh.assert_called_once()


async def test_select_all_options(coordinator, mock_refrigerator):
    """Test selecting all valid temperature options."""
    select = SmartBeerTemperatureSelect(coordinator, mock_refrigerator)

    for label, temp in TEMPERATURE_OPTIONS.items():
        mock_refrigerator.set_offset_temp.reset_mock()
        coordinator.async_request_refresh.reset_mock()

        await select.async_select_option(label)

        mock_refrigerator.set_offset_temp.assert_called_once_with(temp)
        coordinator.async_request_refresh.assert_called_once()


def test_temperature_select_device_info(coordinator, mock_refrigerator):
    """Test temperature select has correct device info."""
    select = SmartBeerTemperatureSelect(coordinator, mock_refrigerator)

    device_info = select.device_info
    assert device_info is not None
    assert (DOMAIN, "TEST_SAID_12345") in device_info["identifiers"]
    assert device_info["manufacturer"] == "Consul"
    assert device_info["model"] == "Smart Beer"


def test_temperature_select_available(coordinator, mock_refrigerator):
    """Test temperature select availability."""
    select = SmartBeerTemperatureSelect(coordinator, mock_refrigerator)

    coordinator._async_update_listeners = []
    coordinator.last_update_success = True

    assert select.available is True


def test_temperature_select_unavailable_when_offline(coordinator, mock_refrigerator):
    """Test temperature select unavailable when device offline."""
    coordinator.data["TEST_SAID_12345"]["online"] = False
    select = SmartBeerTemperatureSelect(coordinator, mock_refrigerator)

    assert select.available is False
