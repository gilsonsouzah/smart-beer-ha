"""Tests for Consul Smart Beer config flow."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.consul_smart_beer.const import DOMAIN


@pytest.fixture
def mock_setup_entry():
    """Mock setup entry."""
    with patch(
        "custom_components.consul_smart_beer.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_auth_success(mock_auth, mock_appliances_manager):
    """Mock successful authentication."""
    with patch(
        "custom_components.consul_smart_beer.config_flow.Auth",
        return_value=mock_auth,
    ), patch(
        "custom_components.consul_smart_beer.config_flow.AppliancesManager",
        return_value=mock_appliances_manager,
    ):
        yield


@pytest.fixture
def mock_auth_failure():
    """Mock failed authentication."""
    mock_auth = MagicMock()
    mock_auth.do_auth = AsyncMock(return_value=False)
    mock_auth.is_access_token_valid.return_value = False
    
    with patch(
        "custom_components.consul_smart_beer.config_flow.Auth",
        return_value=mock_auth,
    ):
        yield


@pytest.fixture
def mock_no_appliances(mock_auth):
    """Mock no appliances found."""
    mock_manager = MagicMock()
    mock_manager.connect = AsyncMock(return_value=True)
    mock_manager.disconnect = AsyncMock()
    mock_manager.refrigerators = []
    
    with patch(
        "custom_components.consul_smart_beer.config_flow.Auth",
        return_value=mock_auth,
    ), patch(
        "custom_components.consul_smart_beer.config_flow.AppliancesManager",
        return_value=mock_manager,
    ):
        yield


async def test_form_user_step(hass: HomeAssistant):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_form_user_success(
    hass: HomeAssistant, mock_auth_success, mock_setup_entry
):
    """Test successful user form submission."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "test@example.com",
            "password": "testpassword123",
        },
    )
    await hass.async_block_till_done()
    
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Consul Smart Beer (test@example.com)"
    assert result2["data"] == {
        "username": "test@example.com",
        "password": "testpassword123",
    }


async def test_form_invalid_auth(hass: HomeAssistant, mock_auth_failure):
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "test@example.com",
            "password": "wrongpassword",
        },
    )
    
    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_no_appliances(hass: HomeAssistant, mock_no_appliances):
    """Test we handle no appliances found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "test@example.com",
            "password": "testpassword123",
        },
    )
    
    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "no_appliances"}


async def test_form_already_configured(
    hass: HomeAssistant, mock_auth_success, mock_setup_entry
):
    """Test we handle already configured accounts."""
    # Create first entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "test@example.com",
            "password": "testpassword123",
        },
    )
    await hass.async_block_till_done()
    
    # Try to create second entry with same email
    result2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            "username": "test@example.com",
            "password": "testpassword123",
        },
    )
    
    assert result3["type"] == FlowResultType.ABORT
    assert result3["reason"] == "already_configured"
