"""Tests for Consul Smart Beer coordinator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta

import aiohttp
from whirlpool.auth import AccountLockedError

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.consul_smart_beer import SmartBeerCoordinator
from custom_components.consul_smart_beer.const import DEFAULT_SCAN_INTERVAL


@pytest.fixture
def coordinator(hass: HomeAssistant, mock_appliances_manager, mock_auth):
    """Create a test coordinator."""
    return SmartBeerCoordinator(hass, mock_appliances_manager, mock_auth)


def test_coordinator_init(coordinator, hass):
    """Test coordinator initialization."""
    assert coordinator.name == "consul_smart_beer"
    assert coordinator.update_interval == timedelta(seconds=DEFAULT_SCAN_INTERVAL)


def test_coordinator_refrigerators(coordinator, mock_refrigerator):
    """Test coordinator returns refrigerators."""
    refrigerators = coordinator.refrigerators
    assert len(refrigerators) == 1
    assert refrigerators[0] == mock_refrigerator


async def test_coordinator_update_success(coordinator, mock_refrigerator):
    """Test successful coordinator update."""
    data = await coordinator._async_update_data()
    
    assert "TEST_SAID_12345" in data
    assert data["TEST_SAID_12345"]["temp"] == -2
    assert data["TEST_SAID_12345"]["turbo_mode"] is False
    assert data["TEST_SAID_12345"]["display_lock"] is False
    assert data["TEST_SAID_12345"]["online"] is True


async def test_coordinator_update_refreshes_token_if_needed(coordinator, mock_auth):
    """Test coordinator refreshes token if needed."""
    mock_auth.is_access_token_valid.return_value = False
    
    await coordinator._async_update_data()
    
    mock_auth.do_auth.assert_called_once()


async def test_coordinator_update_account_locked(coordinator, mock_auth):
    """Test coordinator handles account locked error."""
    mock_auth.is_access_token_valid.return_value = False
    mock_auth.do_auth = AsyncMock(side_effect=AccountLockedError())
    
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_coordinator_update_connection_error(coordinator, mock_appliances_manager):
    """Test coordinator handles connection error."""
    mock_appliances_manager.fetch_all_data = AsyncMock(
        side_effect=aiohttp.ClientError("Connection failed")
    )
    
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_coordinator_update_unexpected_error(coordinator, mock_appliances_manager):
    """Test coordinator handles unexpected error."""
    mock_appliances_manager.fetch_all_data = AsyncMock(
        side_effect=ValueError("Unexpected error")
    )
    
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
