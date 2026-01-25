"""Tests for Consul Smart Beer __init__.py."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
from whirlpool.auth import AccountLockedError

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from custom_components.consul_smart_beer import async_setup_entry, async_unload_entry
from custom_components.consul_smart_beer.const import DOMAIN


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.data = {
        "username": "test@example.com",
        "password": "testpassword123",
    }
    entry.entry_id = "test_entry_id"
    return entry


@pytest.fixture
def mock_hass(hass: HomeAssistant):
    """Create a mock Home Assistant instance."""
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    return hass


async def test_setup_entry_success(mock_hass, mock_config_entry, mock_auth, mock_appliances_manager):
    """Test successful setup entry."""
    with patch(
        "custom_components.consul_smart_beer.Auth",
        return_value=mock_auth,
    ), patch(
        "custom_components.consul_smart_beer.AppliancesManager",
        return_value=mock_appliances_manager,
    ), patch(
        "custom_components.consul_smart_beer.SmartBeerCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ):
        result = await async_setup_entry(mock_hass, mock_config_entry)
    
    assert result is True
    assert mock_config_entry.runtime_data is not None


async def test_setup_entry_auth_failed(mock_hass, mock_config_entry):
    """Test setup entry with authentication failure."""
    mock_auth = MagicMock()
    mock_auth.do_auth = AsyncMock(return_value=False)
    
    with patch(
        "custom_components.consul_smart_beer.Auth",
        return_value=mock_auth,
    ):
        with pytest.raises(ConfigEntryAuthFailed):
            await async_setup_entry(mock_hass, mock_config_entry)


async def test_setup_entry_account_locked(mock_hass, mock_config_entry):
    """Test setup entry with account locked."""
    mock_auth = MagicMock()
    mock_auth.do_auth = AsyncMock(side_effect=AccountLockedError())
    
    with patch(
        "custom_components.consul_smart_beer.Auth",
        return_value=mock_auth,
    ):
        with pytest.raises(ConfigEntryAuthFailed):
            await async_setup_entry(mock_hass, mock_config_entry)


async def test_setup_entry_connection_error(mock_hass, mock_config_entry):
    """Test setup entry with connection error."""
    mock_auth = MagicMock()
    mock_auth.do_auth = AsyncMock(side_effect=aiohttp.ClientError("Connection failed"))
    
    with patch(
        "custom_components.consul_smart_beer.Auth",
        return_value=mock_auth,
    ):
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(mock_hass, mock_config_entry)


async def test_setup_entry_invalid_token(mock_hass, mock_config_entry):
    """Test setup entry with invalid token after auth."""
    mock_auth = MagicMock()
    mock_auth.do_auth = AsyncMock(return_value=True)
    mock_auth.is_access_token_valid.return_value = False
    
    with patch(
        "custom_components.consul_smart_beer.Auth",
        return_value=mock_auth,
    ):
        with pytest.raises(ConfigEntryAuthFailed):
            await async_setup_entry(mock_hass, mock_config_entry)


async def test_unload_entry(mock_hass, mock_config_entry, mock_appliances_manager):
    """Test unload entry."""
    # Create a mock coordinator
    mock_coordinator = MagicMock()
    mock_coordinator.appliances_manager = mock_appliances_manager
    mock_config_entry.runtime_data = mock_coordinator
    
    result = await async_unload_entry(mock_hass, mock_config_entry)
    
    assert result is True
    mock_appliances_manager.disconnect.assert_called_once()
