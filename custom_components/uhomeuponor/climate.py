"""
Support for Uponor Smatrix U@home thermostats.

For more details about this platform, please refer to the documentation at
https://github.com/fcastroruiz/uhome
"""

import logging
import requests
import voluptuous as vol
import json

from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateDevice
from homeassistant.components.climate.const import (
    DOMAIN, HVAC_MODE_AUTO, HVAC_MODE_HEAT, HVAC_MODE_COOL, PRESET_ECO, PRESET_AWAY, PRESET_NONE, PRESET_HOME, PRESET_COMFORT, SUPPORT_PRESET_MODE, CURRENT_HVAC_HEAT, CURRENT_HVAC_OFF,
    CURRENT_HVAC_COOL, SUPPORT_TARGET_TEMPERATURE)
from homeassistant.const import (
    ATTR_ATTRIBUTION, ATTR_ENTITY_ID, ATTR_TEMPERATURE, CONF_FRIENDLY_NAME, CONF_HOST, CONF_NAME, CONF_PREFIX,
    PRECISION_TENTHS, TEMP_CELSIUS)
import homeassistant.helpers.config_validation as cv
from custom_components.uhomeuponor import (Uhome)

CONF_EXTERNAL_TEMP = 'external_temp'
CONF_AWAY_TEMP = 'away_temp'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PREFIX): cv.string,
})

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities,
                   discovery_info=None):
    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    prefix = config.get(CONF_PREFIX)

    uhome = Uhome(ip=host)
    try:
        uhome.update()
    except (ValueError, TypeError) as err:
        _LOGGER.error("Received error from UHOME: %s", err)
        return False

    add_entities([UHomeClimateThermostat(host, prefix, uhome, thermostat)
                  for thermostat in uhome.uhome_thermostats], True)

    _LOGGER.info("finish setup platform climate Uhome Uponor")


class UHomeClimateThermostat(ClimateDevice, Uhome):
    """Representation of a Uponor Thermostat device."""

    def __init__(self, host, prefix, uhome, thermostat):
        """Initialize the thermostat."""
        self.host = host
        self.prefix = prefix
        self.uhome = uhome
        self.thermostat = thermostat

    @property
    def available(self):
        """Return if thermostat is available."""
        return True

    @property
    def state(self):
        """Return the state of the thermostat."""
        return self.hvac_mode

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE

    @property
    def name(self):
        """Return the name of the thermostat."""
        if self.prefix is None:
            return str(self.thermostat.uhome_thermostat_keys['room_name']['value'])
        else:
            return str(self.prefix) + str(self.thermostat.uhome_thermostat_keys['room_name']['value'])

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the thermostat temperature."""
        return self.thermostat.uhome_thermostat_keys['room_temperature']['value']

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self.thermostat.uhome_thermostat_keys['room_setpoint']['value']

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return '0.5'

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature we try to reach."""
        return self.thermostat.uhome_thermostat_keys['max_setpoint']['value']

    @property
    def target_temperature_low(self):
        """Return the lowbound target temperature we try to reach."""
        return self.thermostat.uhome_thermostat_keys['min_setpoint']['value']


    @property
    def hvac_mode(self):
        """Return current operation."""
        if self.thermostat.uhome_thermostat_keys['cooling_allowed']['value'] is 1:
            return HVAC_MODE_COOL
        else:
            return HVAC_MODE_HEAT

    @property
    def hvac_modes(self):
        """List of available operation modes."""
#        return [HVAC_MODE_AUTO, HVAC_MODE_HEAT, HVAC_MODE_COOL]
        return [HVAC_MODE_HEAT, HVAC_MODE_COOL]

    @property
    def hvac_action(self):
        """Return the current running hvac operation if supported.
        Need to be one of CURRENT_HVAC_*.
        """
        work_on = self.thermostat.uhome_thermostat_keys['room_in_demand']['value']
        if work_on is 1:
            if self.hvac_mode is HVAC_MODE_HEAT:
                return CURRENT_HVAC_HEAT
            else:
                return CURRENT_HVAC_COOL
        else:
            return CURRENT_HVAC_OFF

    @property
    def preset_mode(self):
        """Return current operation."""
        return PRESET_NONE

    @property
    def preset_modes(self):
        """List of available operation modes."""
        return [PRESET_NONE, PRESET_COMFORT, PRESET_ECO, PRESET_AWAY, PRESET_HOME]

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_TENTHS

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
           name = 'setpoint_write_enable'
           value = 0
           self.uhome.set_thermostat_value(self.thermostat, name, value)
           name = 'room_setpoint'
           value = kwargs.get(ATTR_TEMPERATURE)
           self.uhome.set_thermostat_value(self.thermostat, name, value)

    def set_hvac_mode(self, hvac_mode):
        """Set operation mode."""
        self.uhome.set_hc_mode(self.thermostat, hvac_mode)

    def set_preset_mode(self, preset_mode):
        """Set operation mode."""
        self.uhome.set_preset_mode(self.thermostat, preset_mode)

    def update(self):
        """Fetch new state data for the thermostat.
        This is the only method that should fetch new data for Home Assistant.
        """
        self.uhome.update_keys(self.uhome.uhome_module_keys)
        self.uhome.update_keys(self.thermostat.uhome_thermostat_keys)

