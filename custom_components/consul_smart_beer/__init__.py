"""The Consul Smart Beer integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp
from whirlpool.appliancesmanager import AppliancesManager
from whirlpool.auth import AccountLockedError, Auth
from whirlpool.backendselector import BackendSelector
from whirlpool.refrigerator import Refrigerator
from whirlpool.types import Brand, Region

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
]


class SmartBeerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Consul Smart Beer data updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        appliances_manager: AppliancesManager,
        auth: Auth,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.appliances_manager = appliances_manager
        self.auth = auth

    @property
    def refrigerators(self) -> list[Refrigerator]:
        """Return list of refrigerators."""
        return self.appliances_manager.refrigerators

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Refresh token if needed
            if not self.auth.is_access_token_valid():
                await self.auth.do_auth()
                
            # Fetch data for all appliances
            await self.appliances_manager.fetch_all_data()
            
            # Build data dict with all refrigerator states
            data: dict[str, Any] = {}
            for refrigerator in self.refrigerators:
                # Helper to convert string "0"/"1" to boolean
                def str_to_bool(value: str | None) -> bool | None:
                    if value is None:
                        return None
                    return str(value) == "1"
                
                # Basic data from Refrigerator class methods
                basic_data = {
                    "temp": refrigerator.get_offset_temp(),
                    "temp_raw": refrigerator.get_temp(),
                    "turbo_mode": refrigerator.get_turbo_mode(),
                    "display_lock": refrigerator.get_display_lock(),
                    "online": refrigerator.get_online(),
                    "name": refrigerator.name,
                    "said": refrigerator.said,
                }
                
                # Extended data - access raw attributes directly
                # Content sensors (Smart Beer specific - "lk" = Lifekeeper)
                basic_data["weight"] = refrigerator._get_attribute("lkWeight")
                basic_data["cans"] = refrigerator._get_attribute("lkCans")
                basic_data["longnecks"] = refrigerator._get_attribute("lkLongneck")
                basic_data["bottles"] = refrigerator._get_attribute("lkBottles")
                basic_data["volume"] = refrigerator._get_attribute("lkVolume")
                basic_data["weight_delta"] = refrigerator._get_attribute("lkDelta")
                
                # Door status (convert "0"/"1" strings to boolean)
                basic_data["door_open"] = str_to_bool(refrigerator._get_attribute("Refrigerator_OpStatusDoorOpen"))
                basic_data["door_alarm"] = str_to_bool(refrigerator._get_attribute("Sys_AlertStatusDoorOpenAlarm"))
                
                # Power/System status (convert "0"/"1" strings to boolean)
                basic_data["power_outage"] = str_to_bool(refrigerator._get_attribute("XCat_PowerStatusPowerOutage"))
                basic_data["system_state"] = refrigerator._get_attribute("Sys_OpStatusState")
                basic_data["fault_code"] = refrigerator._get_attribute("Sys_AlertStatusCustomerFaultCode")
                
                # Diagnostics
                basic_data["running_hours"] = refrigerator._get_attribute("XCat_OdometerStatusRunningHours")
                basic_data["total_hours"] = refrigerator._get_attribute("XCat_OdometerStatusTotalHours")
                basic_data["wifi_rssi"] = refrigerator._get_attribute("XCat_WifiStatusRssiAntennaDiversity")
                
                # Device info
                basic_data["model_number"] = refrigerator._get_attribute("ModelNumber")
                basic_data["serial_number"] = refrigerator._get_attribute("SerialNumber")
                basic_data["wifi_version"] = refrigerator._get_attribute("ISP_WIFI_VERSION")
                basic_data["mac_address"] = refrigerator._get_attribute("MAC_Address")
                
                # Raw attributes for debugging (all available attributes)
                basic_data["raw_attributes"] = {}
                if hasattr(refrigerator, '_data_dict') and refrigerator._data_dict:
                    for key, value in refrigerator._data_dict.items():
                        if isinstance(value, dict) and 'value' in value:
                            basic_data["raw_attributes"][key] = value.get('value')
                        else:
                            basic_data["raw_attributes"][key] = value
                
                data[refrigerator.said] = basic_data
            
            return data
            
        except AccountLockedError as err:
            raise ConfigEntryAuthFailed("Account locked") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error updating data")
            raise UpdateFailed(f"Unexpected error: {err}") from err


type SmartBeerConfigEntry = ConfigEntry[SmartBeerCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: SmartBeerConfigEntry) -> bool:
    """Set up Consul Smart Beer from a config entry."""
    session = async_get_clientsession(hass)
    
    # Consul brand in US region
    backend_selector = BackendSelector(Brand.Consul, Region.US)
    
    auth = Auth(
        backend_selector,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        session,
    )
    
    try:
        auth_result = await auth.do_auth(store=False)
        if not auth_result:
            raise ConfigEntryAuthFailed("Authentication failed")
    except AccountLockedError as err:
        raise ConfigEntryAuthFailed("Account locked") from err
    except aiohttp.ClientError as err:
        raise ConfigEntryNotReady("Cannot connect to Consul servers") from err
    
    if not auth.is_access_token_valid():
        raise ConfigEntryAuthFailed("Invalid credentials")
    
    # Create appliances manager and fetch appliances
    appliances_manager = AppliancesManager(backend_selector, auth, session)
    
    try:
        if not await appliances_manager.fetch_appliances():
            raise ConfigEntryNotReady("Failed to fetch appliances")
    except aiohttp.ClientError as err:
        raise ConfigEntryNotReady("Cannot connect to Consul servers") from err
    
    if not appliances_manager.refrigerators:
        _LOGGER.warning("No Smart Beer appliances found")
    
    # Connect to event socket for real-time updates
    try:
        await appliances_manager.connect()
    except Exception as err:
        _LOGGER.warning("Could not connect to event socket: %s", err)
    
    # Create coordinator
    coordinator = SmartBeerCoordinator(hass, appliances_manager, auth)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator in entry
    entry.runtime_data = coordinator
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SmartBeerConfigEntry) -> bool:
    """Unload a config entry."""
    # Disconnect from event socket
    coordinator = entry.runtime_data
    try:
        await coordinator.appliances_manager.disconnect()
    except Exception as err:
        _LOGGER.warning("Error disconnecting: %s", err)
    
    # Unload platforms
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
