from __future__ import annotations
import asyncio
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
import logging
import voluptuous as vol
from homeassistant.const import (CONF_HOST, CONF_NAME, CONF_PREFIX)
from .uponor_api.const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_SUPPORTS_HEATING = "supports_heating"
CONF_SUPPORTS_COOLING = "supports_cooling"

class UhomeuponorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Uponor config flow."""
    VERSION = 1
    # CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        _LOGGER.info("Init config step uhomeuponor")
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            _LOGGER.debug("user_input: %s", user_input)
            # Validate user input
            #valid = await is_valid(user_input)
            #if valid:
            #title = f"{self.info[CONF_HOST]} - {self.device_id}"
            title = f"Uhome Uponor"
            data={
                CONF_HOST: user_input[CONF_HOST],
                CONF_PREFIX: (user_input.get(CONF_PREFIX) if user_input.get(CONF_PREFIX) else ""),
                CONF_SUPPORTS_HEATING: user_input[CONF_SUPPORTS_HEATING],
                CONF_SUPPORTS_COOLING: user_input[CONF_SUPPORTS_COOLING]}
            return self.async_create_entry(
                        title=title,
                        data=data
                        # options=data
                    )

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
        return OptionsFlowHandler(entry)

class OptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

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
            data={
                CONF_HOST: user_input[CONF_HOST], 
                CONF_PREFIX: user_input[CONF_PREFIX],
                CONF_SUPPORTS_HEATING: user_input[CONF_SUPPORTS_HEATING],
                CONF_SUPPORTS_COOLING: user_input[CONF_SUPPORTS_COOLING],
                }
            _LOGGER.debug("user_input data: %s, id: %s", data, self.config_entry.entry_id)
            title = f"Uhome Uponor"
            return self.async_create_entry(
                title=title, 
                data=data
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=options.get(CONF_HOST)): str,
                    vol.Optional(CONF_PREFIX, default=options.get(CONF_PREFIX)): str,
                    vol.Optional(CONF_SUPPORTS_HEATING, default=options.get(CONF_SUPPORTS_HEATING)): bool,
                    vol.Optional(CONF_SUPPORTS_COOLING, default=options.get(CONF_SUPPORTS_COOLING)): bool,
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