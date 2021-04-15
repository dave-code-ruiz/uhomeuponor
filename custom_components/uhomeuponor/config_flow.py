from homeassistant import config_entries
import logging
import voluptuous as vol
from homeassistant.const import (CONF_HOST, CONF_NAME, CONF_PREFIX)

_LOGGER = logging.getLogger(__name__)
DOMAIN = "uhomeuponor"

class UhomeuponorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Uponor config flow."""
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            _LOGGER.info ("user_input: %s", user_input)
            # Validate user input
            #valid = await is_valid(user_input)
            #if valid:
            #title = f"{self.info[CONF_HOST]} - {self.device_id}"
            title = f"Uhome Uponor"
            return self.async_create_entry(
                        title=title,
                        data={
                            "host": user_input[CONF_HOST],
                            "prefix": user_input[CONF_PREFIX],
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
