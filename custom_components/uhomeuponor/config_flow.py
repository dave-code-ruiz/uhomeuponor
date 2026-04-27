from __future__ import annotations
import asyncio
import aiohttp
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import logging
import voluptuous as vol
from homeassistant.const import (CONF_HOST, CONF_PREFIX)
from .uponor_api.const import DOMAIN
from .uponor_api import UponorClient, UponorAPIException

_LOGGER = logging.getLogger(__name__)

CONF_SUPPORTS_HEATING = "supports_heating"
CONF_SUPPORTS_COOLING = "supports_cooling"

class UhomeuponorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Uponor config flow."""
    VERSION = 1

    async def _async_validate_connection(self, host: str) -> bool:
        """Validate connectivity to Uponor gateway with a simple ping.

        Uses a lightweight JSON-RPC request instead of full rescan() to avoid
        long-running coroutine cancellation in Python 3.11+ (CancelledError from
        aiohttp's asyncio.timeout() is BaseException, not caught by except Exception).
        Full initialization is handled by async_setup_entry with ConfigEntryNotReady.
        """
        _LOGGER.debug("Validating connection to host: %s", host)
        try:
            session = async_get_clientsession(self.hass)
            timeout = aiohttp.ClientTimeout(total=5)
            payload = {"jsonrpc": "2.0", "method": "login", "params": {}, "id": 1}
            async with session.post(
                f"http://{host}/api", json=payload, timeout=timeout
            ) as resp:
                if resp.status == 200:
                    _LOGGER.debug("Connection validated successfully for host: %s", host)
                    return True
                _LOGGER.warning("Unexpected HTTP status %d from host %s", resp.status, host)
                return False
        except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError) as ex:
            _LOGGER.warning("Connection failed to host %s: %s", host, ex)
            return False
        except Exception as ex:
            _LOGGER.exception("Unexpected error validating host %s: %s", host, ex)
            return False

    async def async_step_user(self, user_input=None):
        errors = {}
        _LOGGER.info("Init config step uhomeuponor")
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            _LOGGER.debug("user_input: %s", user_input)
            try:
                host = user_input.get(CONF_HOST, "")
                if not await self._async_validate_connection(host):
                    errors["base"] = "cannot_connect"
                else:
                    title = "Uhome Uponor"
                    data = {
                        CONF_HOST: host,
                        CONF_PREFIX: user_input.get(CONF_PREFIX, ""),
                        CONF_SUPPORTS_HEATING: user_input.get(CONF_SUPPORTS_HEATING, True),
                        CONF_SUPPORTS_COOLING: user_input.get(CONF_SUPPORTS_COOLING, True),
                    }
                    return self.async_create_entry(
                        title=title,
                        data=data,
                    )
            except Exception:
                _LOGGER.exception("Unexpected error while creating config entry")
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PREFIX): str,
                    vol.Optional(CONF_SUPPORTS_HEATING, default=True): bool,
                    vol.Optional(CONF_SUPPORTS_COOLING, default=True): bool,
                }
            ), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry):
        return OptionsFlowHandler()

class OptionsFlowHandler(config_entries.OptionsFlow):

    async def async_step_init(self, _user_input=None):
        """Manage the options."""
        return await self.async_step_user()
    
    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        _LOGGER.debug("entra en step user: %s", user_input)
        _LOGGER.info("Init Option config step uhomeuponor")
        errors = {}
        options = self.config_entry.data
        if user_input is not None:
            try:
                data = {
                    CONF_HOST: user_input.get(CONF_HOST, options.get(CONF_HOST)),
                    CONF_PREFIX: user_input.get(CONF_PREFIX, ""),
                    CONF_SUPPORTS_HEATING: user_input.get(
                        CONF_SUPPORTS_HEATING, options.get(CONF_SUPPORTS_HEATING, True)
                    ),
                    CONF_SUPPORTS_COOLING: user_input.get(
                        CONF_SUPPORTS_COOLING, options.get(CONF_SUPPORTS_COOLING, True)
                    ),
                }
                _LOGGER.debug("user_input data: %s, id: %s", data, self.config_entry.entry_id)
                title = "Uhome Uponor"
                return self.async_create_entry(
                    title=title,
                    data=data,
                )
            except Exception:
                _LOGGER.exception("Unexpected error while saving options")
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=options.get(CONF_HOST)): str,
                    vol.Optional(CONF_PREFIX, default=options.get(CONF_PREFIX, "")): str,
                    vol.Optional(CONF_SUPPORTS_HEATING, default=options.get(CONF_SUPPORTS_HEATING, True)): bool,
                    vol.Optional(CONF_SUPPORTS_COOLING, default=options.get(CONF_SUPPORTS_COOLING, True)): bool,
                }
            ), errors=errors
        )

# class UhomeuponorDicoveryFlow(DiscoveryFlowHandler[Awaitable[bool]], domain=DOMAIN):
#     """Discovery flow handler."""

#     VERSION = 1

#     def __init__(self) -> None:
#         """Set up config flow."""
#         super().__init__(
#             DOMAIN,
#             "Uponor Checker",
#             _async_supported,
#         )

#     async def async_step_onboarding(
#         self, data: dict[str, Any] | None = None
#     ) -> FlowResult:
#         """Handle a flow initialized by onboarding."""
#         has_devices = await self._discovery_function(self.hass)

#         if not has_devices:
#             return self.async_abort(reason="no_devices_found")
#         return self.async_create_entry(title=self._title, data={})