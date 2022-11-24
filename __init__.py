"""Uponor U@Home integration

For more details about this platform, please refer to the documentation at
https://github.com/fcastroruiz/uhomeuponor
"""
from logging import getLogger
import asyncio
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry, entity_registry
from .uponor_api.const import DOMAIN

_LOGGER = getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.CLIMATE]

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = config.get(DOMAIN) or {}
    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up this integration using UI."""
    _LOGGER.info("Loading setup entry")

    # hass.config_entries.async_setup_platforms(config_entry, PLATFORMS)
    if config_entry.options:
        if config_entry.data != config_entry.options:
            dev_reg = device_registry.async_get(hass)
            ent_reg = entity_registry.async_get(hass)
            dev_reg.async_clear_config_entry(config_entry.entry_id)
            ent_reg.async_clear_config_entry(config_entry.entry_id)
            hass.config_entries.async_update_entry(config_entry, data=config_entry.options)
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    config_entry.async_on_unload(config_entry.add_update_listener(async_update_options))
    
    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    _LOGGER.debug("Update setup entry: %s, data: %s, options: %s", entry.entry_id, entry.data, entry.options)
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading setup entry: %s, data: %s, options: %s", config_entry.entry_id, config_entry.data, config_entry.options)
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    return unload_ok
    #if unload_ok:
    #    hass.data[DOMAIN].pop(config_entry.entry_id)
