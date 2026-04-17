"""Uponor U@Home integration

For more details about this platform, please refer to the documentation at
https://github.com/fcastroruiz/uhomeuponor
"""
from logging import getLogger
import asyncio
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform, CONF_HOST
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry, entity_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.util.dt as dt_util
from .uponor_api.const import DOMAIN
from .uponor_api import UponorClient

_LOGGER = getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.CLIMATE]

UNAVAILABLE_THRESHOLD = timedelta(minutes=2)
RELOAD_COOLDOWN = timedelta(minutes=10)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = config.get(DOMAIN) or {}
    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up this integration using UI."""
    _LOGGER.info("Loading setup entry")

    if config_entry.options:
        if config_entry.data != config_entry.options:
            dev_reg = device_registry.async_get(hass)
            ent_reg = entity_registry.async_get(hass)
            dev_reg.async_clear_config_entry(config_entry.entry_id)
            ent_reg.async_clear_config_entry(config_entry.entry_id)
            hass.config_entries.async_update_entry(config_entry, data=config_entry.options)

    host = config_entry.data[CONF_HOST]
    session = async_get_clientsession(hass)

    uponor = UponorClient(hass=hass, server=host, session=session)
    try:
        await asyncio.wait_for(uponor.rescan(), timeout=8.0)
    except asyncio.CancelledError:
        raise
    except asyncio.TimeoutError as err:
        _LOGGER.warning("Timeout connecting to Uponor gateway at %s, will retry", host)
        raise ConfigEntryNotReady(f"Timeout connecting to Uponor gateway at {host}") from err
    except Exception as err:
        _LOGGER.warning("Failed to connect to Uponor gateway at %s: %s, will retry", host, err)
        raise ConfigEntryNotReady(f"Cannot connect to Uponor gateway at {host}: {err}") from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {
        "client": uponor,
        "last_successful_update": dt_util.now(),
        "unavailable_since": None,
        "reload_in_progress": False,
        "last_reload_attempt": None,
    }

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    config_entry.async_on_unload(config_entry.add_update_listener(async_update_options))
    
    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    _LOGGER.debug("Update setup entry: %s, data: %s, options: %s", entry.entry_id, entry.data, entry.options)
    # Unload first to ensure clean state (if loaded), then reload
    if entry.state in (ConfigEntryState.LOADED, ConfigEntryState.SETUP_RETRY):
        await hass.config_entries.async_unload(entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading setup entry: %s, data: %s, options: %s", config_entry.entry_id, config_entry.data, config_entry.options)
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id, None)
    return unload_ok
