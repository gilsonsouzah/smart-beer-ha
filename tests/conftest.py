"""Pytest configuration for Consul Smart Beer tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from whirlpool.httpapi.refrigerator import Refrigerator
from whirlpool.types import ApplianceInfo


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations in all tests."""
    yield


@pytest.fixture
def mock_refrigerator():
    """Create a mock refrigerator."""
    refrigerator = MagicMock(spec=Refrigerator)
    refrigerator.said = "TEST_SAID_12345"
    refrigerator.name = "Smart Beer Test"
    refrigerator.appliance_info = ApplianceInfo(
        said="TEST_SAID_12345",
        name="Smart Beer Test",
        category="Refrigerator",
        model_number="CZD12AT",
        serial_number="SN123456789",
    )
    refrigerator.get_offset_temp.return_value = -2
    refrigerator.get_temp.return_value = 11
    refrigerator.get_turbo_mode.return_value = False
    refrigerator.get_display_lock.return_value = False
    refrigerator.get_online.return_value = True
    refrigerator.set_offset_temp = AsyncMock(return_value=True)
    refrigerator.set_turbo_mode = AsyncMock(return_value=True)
    refrigerator.set_display_lock = AsyncMock(return_value=True)
    refrigerator.fetch_data = AsyncMock(return_value=True)
    return refrigerator


@pytest.fixture
def mock_appliances_manager(mock_refrigerator):
    """Create a mock appliances manager."""
    manager = MagicMock()
    manager.refrigerators = [mock_refrigerator]
    manager.connect = AsyncMock(return_value=True)
    manager.disconnect = AsyncMock()
    return manager


@pytest.fixture
def mock_auth():
    """Create a mock auth object."""
    auth = MagicMock()
    auth.do_auth = AsyncMock(return_value=True)
    auth.is_access_token_valid.return_value = True
    auth.get_access_token.return_value = "test_access_token"
    return auth


@pytest.fixture
def mock_backend_selector():
    """Create a mock backend selector."""
    selector = MagicMock()
    return selector
