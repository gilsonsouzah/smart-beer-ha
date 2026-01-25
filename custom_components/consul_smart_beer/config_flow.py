"""Config flow for Consul Smart Beer integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from whirlpool.appliancesmanager import AppliancesManager
from whirlpool.auth import AccountLockedError, Auth
from whirlpool.backendselector import BackendSelector
from whirlpool.types import Brand, Region

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(
    hass: HomeAssistant, data: dict[str, Any]
) -> tuple[str | None, list[Any] | None]:
    """Validate the user input and return error key if any, plus appliances list."""
    session = async_get_clientsession(hass)
    
    # Consul brand in US region (Smart Beer is sold in Brazil but uses US backend)
    backend_selector = BackendSelector(Brand.Consul, Region.US)
    
    auth = Auth(
        backend_selector,
        data[CONF_USERNAME],
        data[CONF_PASSWORD],
        session,
    )
    
    try:
        auth_result = await auth.do_auth(store=False)
        if not auth_result:
            return "invalid_auth", None
            
        if not auth.is_access_token_valid():
            return "invalid_auth", None
            
    except AccountLockedError:
        return "account_locked", None
    except aiohttp.ClientError:
        return "cannot_connect", None
    except Exception:
        _LOGGER.exception("Unexpected error during authentication")
        return "unknown", None
    
    # Try to fetch appliances to verify account has Smart Beer devices
    try:
        appliances_manager = AppliancesManager(backend_selector, auth, session)
        await appliances_manager.fetch_appliances()
        
        # Check for refrigerators (Smart Beer is a TED refrigerator)
        if not appliances_manager.refrigerators:
            return "no_appliances", None
            
        return None, appliances_manager.refrigerators
        
    except aiohttp.ClientError:
        return "cannot_connect", None
    except Exception:
        _LOGGER.exception("Unexpected error fetching appliances")
        return "unknown", None


class ConsulSmartBeerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Consul Smart Beer."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
            self._abort_if_unique_id_configured()

            error_key, appliances = await validate_input(self.hass, user_input)
            
            if error_key is None and appliances:
                # Store appliance info for display
                appliance_names = [a.name for a in appliances]
                _LOGGER.info(
                    "Found %d Smart Beer appliance(s): %s",
                    len(appliances),
                    ", ".join(appliance_names),
                )
                
                return self.async_create_entry(
                    title=f"Consul Smart Beer ({user_input[CONF_USERNAME]})",
                    data=user_input,
                )
            
            if error_key:
                errors["base"] = error_key

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
