from __future__ import annotations
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
import logging
import voluptuous as vol
from homeassistant.const import (CONF_HOST, CONF_NAME, CONF_PREFIX)

_LOGGER = logging.getLogger(__name__)
DOMAIN = "uhomeuponor"

class UhomeuponorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Uponor config flow."""
    VERSION = 1
    # CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            _LOGGER.info ("user_input: %s", user_input)
            # Validate user input
            #valid = await is_valid(user_input)
            #if valid:
            #title = f"{self.info[CONF_HOST]} - {self.device_id}"
            title = f"Uhome Uponor"
            prefix = user_input.get(CONF_PREFIX) if user_input.get(CONF_PREFIX) else ""
            return self.async_create_entry(
                        title=title,
                        data={
                            "host": user_input[CONF_HOST],
                            "prefix": prefix,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PREFIX): str,
                }
            ), errors=errors
        )

    # @staticmethod
    # @callback
    # def async_get_options_flow(
    #     config_entry: ConfigEntry,
    # ) -> UhomeuponorOptionsFlowHandler:
    #     """Options callback for uponor."""
    #     return UhomeuponorOptionsFlowHandler(config_entry)


# class UhomeuponorOptionsFlowHandler(config_entries.OptionsFlow):
#     """Config flow options for uponor."""

#     def __init__(self, entry: ConfigEntry) -> None:
#         """Initialize AccuWeather options flow."""
#         self.config_entry = entry

#     async def async_step_init(self, user_input=None):
#         """Manage the options."""
#         return await self.async_step_user()

#     async def async_step_user(self, user_input=None):
#         errors = {}
#         if user_input is not None:
#             _LOGGER.info ("Aqui debemos hacer algo con user_input: %s", user_input)
#             # Validate user input
#             #valid = await is_valid(user_input)
#             #if valid:
#             #title = f"{self.info[CONF_HOST]} - {self.device_id}"
#             title = f"Uhome Uponor"
#             return self.async_create_entry(
#                         title=title,
#                         data={
#                             "host": user_input[CONF_HOST],
#                             "prefix": user_input[CONF_PREFIX],
#                         },
#                     )

#         return self.async_show_form(
#             step_id="user",
#             data_schema=vol.Schema(
#                 {
#                     vol.Required(CONF_HOST): str,
#                     vol.Optional(CONF_PREFIX): str,
#                 }
#             ), errors=errors
#         )

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