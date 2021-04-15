"""Uponor U@Home integration
Exposes Climate control entities for Uponor thermostats

- UponorThermostat
"""

import voluptuous as vol

from requests.exceptions import RequestException

from homeassistant.exceptions import PlatformNotReady
from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateEntity
from homeassistant.components.climate.const import (
    DOMAIN, 
    HVAC_MODE_AUTO, HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_COOL, 
    PRESET_COMFORT, PRESET_ECO,
    CURRENT_HVAC_HEAT, CURRENT_HVAC_COOL, CURRENT_HVAC_IDLE,
    SUPPORT_PRESET_MODE, SUPPORT_TARGET_TEMPERATURE)
from homeassistant.const import (
    ATTR_ATTRIBUTION, ATTR_ENTITY_ID, ATTR_TEMPERATURE, ATTR_BATTERY_LEVEL, 
    CONF_FRIENDLY_NAME, CONF_HOST, CONF_NAME, CONF_PREFIX,
    PRECISION_TENTHS, 
    TEMP_CELSIUS)
import homeassistant.helpers.config_validation as cv
from logging import getLogger

from .uponor_api import UponorClient
from .uponor_api.const import (UHOME_MODE_HEAT, UHOME_MODE_COOL, UHOME_MODE_ECO, UHOME_MODE_COMFORT)

CONF_SUPPORTS_HEATING = "supports_heating"
CONF_SUPPORTS_COOLING = "supports_cooling"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PREFIX): cv.string,
    vol.Optional(CONF_SUPPORTS_HEATING, default=True): cv.boolean,
    vol.Optional(CONF_SUPPORTS_COOLING, default=True): cv.boolean,
})

ATTR_TECHNICAL_ALARM = "technical_alarm"
ATTR_RF_SIGNAL_ALARM = "rf_alarm"
ATTR_BATTERY_ALARM = "battery_alarm"

_LOGGER = getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Alexa alarm control panel platform by config_entry."""
    _LOGGER.info("init setup climate platform for %s", config_entry)
    # return await async_setup_platform(
    #     hass, config_entry.data, async_add_entities, discovery_info=None
    # )

# async def async_setup_platform(
#     hass, config, async_add_entities, discovery_info=None
# ) -> bool:
#     """Set up the Alexa alarm control panel platform."""
#     """Set up climate for device."""
#     _LOGGER.info("init setup climate platform for %s", config)

#     host = config[CONF_HOST]
#     prefix = config[CONF_PREFIX]
#     supports_heating = True
#     supports_cooling = True

#     _LOGGER.info("init setup host %s", host)

#     uponor = await hass.async_add_executor_job(lambda: UponorClient(hass=hass, server=host))
#     try:
#         await uponor.rescan()
#     except (ValueError, RequestException) as err:
#         _LOGGER.error("Received error from UHOME: %s", err)
#         raise PlatformNotReady
    
#     async_add_entities([UponorThermostat(prefix, uponor, thermostat, supports_heating, supports_cooling)
#                   for thermostat in uponor.thermostats], True)
    
#     _LOGGER.info("finish setup climate platform for Uhome Uponor")
#     return True

def setup_platform(hass, config, add_entities, discovery_info=None):
    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    prefix = config.get(CONF_PREFIX)
    supports_heating = config.get(CONF_SUPPORTS_HEATING)
    supports_cooling = config.get(CONF_SUPPORTS_COOLING)

    uponor = UponorClient(hass=hass, server=host)
    try:
        uponor.rescan()
    except (ValueError, RequestException) as err:
        _LOGGER.error("Received error from UHOME: %s", err)
        raise PlatformNotReady

    # Add Climate / Thermostat entities
    add_entities([UponorThermostat(prefix, uponor, thermostat, supports_heating, supports_cooling)
                  for thermostat in uponor.thermostats], True)

    _LOGGER.info("finish setup climate platform for Uhome Uponor")

class UponorThermostat(ClimateEntity):
    """HA Thermostat climate entity. Utilizes Uponor U@Home API to interact with U@Home"""

    def __init__(self, prefix, uponor_client, thermostat, supports_heating, supports_cooling):
        self._available = False
        self.prefix = prefix
        self.uponor_client = uponor_client
        self.thermostat = thermostat
        self.supports_heating = supports_heating
        self.supports_cooling = supports_cooling

        self.identity = f"{prefix or ''}controller{str(thermostat.controller_index)}_thermostat{str(thermostat.thermostat_index)}_thermostat"

    # ** Generic **
    @property
    def name(self):
        return f"{self.prefix or ''}{self.thermostat.by_name('room_name').value}"

    @property
    def unique_id(self):
        return self.identity

    @property
    def available(self):
        return self._available

    # ** Static **
    @property
    def temperature_unit(self):
        return TEMP_CELSIUS

    @property
    def precision(self):
        return PRECISION_TENTHS

    @property
    def target_temperature_step(self):
        return '0.5'

    @property
    def supported_features(self):
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE

    @property
    def hvac_modes(self):
        modes = []

        if self.supports_heating:
            modes.append(HVAC_MODE_HEAT)

        if self.supports_cooling:
            modes.append(HVAC_MODE_COOL)

        return modes

    @property
    def preset_modes(self):
        return [PRESET_ECO, PRESET_COMFORT]

    # ** State **
    @property
    def current_humidity(self):
        return self.thermostat.by_name('rh_value').value

    @property
    def current_temperature(self):
        return self.thermostat.by_name('room_temperature').value

    @property
    def target_temperature(self):
        return self.thermostat.by_name('room_setpoint').value
    
    @property
    def device_state_attributes(self):
        return {
            ATTR_TECHNICAL_ALARM: self.thermostat.by_name('technical_alarm').value,
            ATTR_RF_SIGNAL_ALARM: self.thermostat.by_name('rf_alarm').value,
            ATTR_BATTERY_ALARM: self.thermostat.by_name('battery_alarm').value
        }
        
    @property
    def preset_mode(self):
        if self.uponor_client.uhome.by_name('forced_eco_mode').value == 1:
            return PRESET_ECO

        return PRESET_COMFORT

    @property
    def hvac_mode(self):
        if self.uponor_client.uhome.by_name('hc_mode').value == 1:
            return HVAC_MODE_COOL

        return HVAC_MODE_HEAT

    @property
    def hvac_action(self):
        if self.thermostat.by_name('room_in_demand').value == 0:
            return CURRENT_HVAC_IDLE
        
        if self.hvac_mode == HVAC_MODE_HEAT:
            return CURRENT_HVAC_HEAT
        else:
            return CURRENT_HVAC_COOL

    # ** Actions **
    def update(self):
        # Update Uhome (to get HC mode) and thermostat
        try:
            self.uponor_client.update_devices(self.uponor_client.uhome, self.thermostat)
            valid = self.thermostat.is_valid()
            self._available = valid
            if not valid:
                _LOGGER.debug("The thermostat '%s' had invalid data, and is therefore unavailable", self.identity)
        except Exception as ex:
            self._available = False
            _LOGGER.error("Uponor thermostat was unable to update: %s", ex)

    def set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVAC_MODE_HEAT:
            value = UHOME_MODE_HEAT
        else:
            value = UHOME_MODE_COOL
        self.thermostat.set_hvac_mode(value)

    # Support setting preset_mode
    def set_preset_mode(self, preset_mode):
        if preset_mode == PRESET_ECO:
            value = UHOME_MODE_ECO
        else:
            value = UHOME_MODE_COMFORT
        self.thermostat.set_preset_mode(value)
        self.thermostat.set_auto_mode()

    def set_temperature(self, **kwargs):
        if kwargs.get(ATTR_TEMPERATURE) is None:
            return
        self.thermostat.set_setpoint(kwargs.get(ATTR_TEMPERATURE))
