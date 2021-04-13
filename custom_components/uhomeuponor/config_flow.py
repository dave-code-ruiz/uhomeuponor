from homeassistant import config_entries
from .const import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

class ExampleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Example config flow."""
    async def async_step_user(self, info):
        if info is not None:
            _LOGGER.debug ("Aqui debemos hacer algo con info: %s", info)
            pass  # TODO: process info Flow

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required("password"): str})
        )
