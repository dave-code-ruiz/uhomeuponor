"""Uponor U@Home integration

For more details about this platform, please refer to the documentation at
https://github.com/fcastroruiz/uhomeuponor
"""
from homeassistant.const import CONF_HOST
from logging import getLogger
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.config_entries import ConfigEntry

_LOGGER = getLogger(__name__)
DOMAIN = "uhomeuponor"
PLATFORMS = [Platform.SENSOR, Platform.CLIMATE]

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up this integration using UI."""
    _LOGGER.info("Loading setup")
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = config.get(DOMAIN) or {}
    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up this integration using UI."""
    #host = config_entry.data[CONF_HOST]
    _LOGGER.info("Loading setup entry")

    # hass.async_create_task(hass.config_entries.async_forward_entry_setup(config_entry, "climate"))
    # hass.async_create_task(hass.config_entries.async_forward_entry_setup(config_entry, "sensor"))
    hass.config_entries.async_setup_platforms(config_entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
