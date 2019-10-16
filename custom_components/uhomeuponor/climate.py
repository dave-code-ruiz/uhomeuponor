"""
Support for Uponor Smatrix U@home thermostats.

For more details about this platform, please refer to the documentation at
https://github.com/fcastroruiz/uhomeuponor
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

    add_entities([UHomeClimateThermostat(prefix, uhome, thermostat)
                  for thermostat in uhome.uhome_thermostats], True)
    add_entities([GeneralClimateThermostat(prefix, uhome)])

    _LOGGER.info("finish setup platform climate Uhome Uponor")


class UHomeClimateThermostat(ClimateDevice, Uhome):
    """Representation of a Uponor Thermostat device."""

    def __init__(self, prefix, uhome, thermostat):
        """Initialize the thermostat."""
        self.prefix = prefix
        self.uhome = uhome
        self.thermostat = thermostat
        self._preset_mode = PRESET_NONE
        self._hvac_mode = None

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
        value = self._returnvalue(self.thermostat.uhome_thermostat_keys['room_temperature']['value'], self.thermostat.uhome_thermostat_keys['min_setpoint']['value'], self.thermostat.uhome_thermostat_keys['max_setpoint']['value'])
        return value

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
        if self.uhome.uhome_module_keys['hc_mode']['value'] == 1:
            return HVAC_MODE_COOL
        else:
            return HVAC_MODE_HEAT

    @property
    def hvac_modes(self):
        """List of available operation modes."""
        return [HVAC_MODE_HEAT, HVAC_MODE_COOL]

    def set_hvac_mode(self, hvac_mode):
        """Set operation mode."""
        value = '0'

    @property
    def hvac_action(self):
        """Return the current running hvac operation if supported.
        Need to be one of CURRENT_HVAC_*.
        """
        work_on = self.thermostat.uhome_thermostat_keys['room_in_demand']['value']
        if work_on == 1:
            if self.hvac_mode == HVAC_MODE_HEAT:
                return CURRENT_HVAC_HEAT
            else:
                return CURRENT_HVAC_COOL
        else:
            return CURRENT_HVAC_OFF

    @property
    def preset_mode(self):
        """Return current operation."""
        if self.uhome.uhome_module_keys['holiday_mode']['value'] == 1:
            return PRESET_AWAY
        else:
            if self.uhome.uhome_module_keys['forced_eco_mode']['value'] == 1:
                return PRESET_ECO
            else:
                return PRESET_COMFORT

    @property
    def preset_modes(self):
        """List of available operation modes."""
        return [PRESET_NONE, PRESET_COMFORT, PRESET_ECO, PRESET_AWAY, PRESET_HOME]

    def set_preset_mode(self, preset_mode):
        """Set operation mode."""
        value = '0'

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

    def update(self):
        """Fetch new state data for the thermostat.
        This is the only method that should fetch new data for Home Assistant.
        """
        self.uhome.update_keys(self.uhome.uhome_module_keys)
        self.uhome.update_keys(self.thermostat.uhome_thermostat_keys)

    def _returnvalue(self, value, minvalue, maxvalue):
        if value <= maxvalue and value >= minvalue:
            return value
        if value > maxvalue:
            return maxvalue
        if value < minvalue:
            return minvalue

class GeneralClimateThermostat(ClimateDevice, Uhome):
    """Representation of a Uponor Thermostat device."""

    def __init__(self, prefix, uhome):
        """Initialize the thermostat."""
        self.prefix = prefix
        self.uhome = uhome
        self._preset_mode = None
        self._hvac_mode = None

    @property
    def available(self):
        """Return if thermostat is available."""
        return True

    @property
    def state(self):
        """Return the state of the thermostat."""
        if self.uhome.uhome_module_keys['hc_mode']['value'] == 1:
            return HVAC_MODE_COOL
        else:
            return HVAC_MODE_HEAT

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE

    @property
    def name(self):
        """Return the name of the thermostat."""
        if self.prefix is None:
            return 'GeneralTermostat'
        else:
            return str(self.prefix) + 'GeneralTermostat'

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the thermostat temperature."""
        return self.uhome.uhome_module_keys['average_room_temperature']['value']

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self.uhome.uhome_module_keys['holiday_setpoint']['value']

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return '0.5'

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature we try to reach."""
        return self.uhome.uhome_thermostats[1].uhome_thermostat_keys['max_setpoint']['value']

    @property
    def target_temperature_low(self):
        """Return the lowbound target temperature we try to reach."""
        return self.uhome.uhome_thermostats[1].uhome_thermostat_keys['min_setpoint']['value']

    @property
    def hvac_mode(self):
        if self.uhome.uhome_module_keys['hc_mode']['value'] == 1:
            return HVAC_MODE_COOL
        else:
            return HVAC_MODE_HEAT

    @property
    def hvac_modes(self):
        """List of available operation modes."""
        return [HVAC_MODE_AUTO, HVAC_MODE_HEAT, HVAC_MODE_COOL]

    def set_hvac_mode(self, hvac_mode):
        """Set operation mode."""
#        for thermostat in self.uhome.uhome_thermostats:
#            self.uhome.set_hc_mode(thermostat, hvac_mode)
        value = '1'
        name= 'allow_hc_mode_change'
        self.uhome.set_module_value(name, value)
        value = None
        name= None
        if hvac_mode == HVAC_MODE_HEAT:
           name = 'hc_mode'
           value = 0
        elif hvac_mode == HVAC_MODE_COOL:
           name = 'hc_mode'
           value = 1
        else:
           _LOGGER.error("Error setting hvac mode, mode " + hvac_mode + " unknown")

        if value is not None:
            self.uhome.set_module_value(name, value)
        value = '0'
        name= 'allow_hc_mode_change'
        self.uhome.set_module_value(name, value)
        self._hvac_mode = hvac_mode

    @property
    def hvac_action(self):
        """Return the current running hvac operation if supported.
        Need to be one of CURRENT_HVAC_*.
        """
        work_on = self.uhome.uhome_thermostats[1].uhome_thermostat_keys['room_in_demand']['value']
        if work_on == 1:
            if self._hvac_mode == HVAC_MODE_HEAT:
                return CURRENT_HVAC_HEAT
            else:
                return CURRENT_HVAC_COOL
        else:
            return CURRENT_HVAC_OFF

    @property
    def preset_mode(self):
        """Return current operation."""
        if self.uhome.uhome_module_keys['holiday_mode']['value'] == 1:
            return PRESET_AWAY
        else:
            if self.uhome.uhome_module_keys['forced_eco_mode']['value'] == 1:
                return PRESET_ECO
            else:
                return PRESET_COMFORT

    @property
    def preset_modes(self):
        """List of available operation modes."""
        return [PRESET_NONE, PRESET_COMFORT, PRESET_ECO, PRESET_AWAY, PRESET_HOME]

    def set_preset_mode(self, preset_mode):
        """Set operation mode."""
        value = '1'
        name= 'allow_hc_mode_change'
        self.uhome.set_module_value(name, value)
        value = None
        name= None
        if preset_mode == PRESET_COMFORT:
           name = 'forced_eco_mode'
           value = 0
        elif preset_mode == PRESET_ECO:
           name = 'forced_eco_mode'
           value = 1
        elif preset_mode == PRESET_AWAY:
           name = 'holiday_mode'
           value = 1
        elif preset_mode == PRESET_HOME:
           name = 'holiday_mode'
           value = 0
        elif preset_mode == PRESET_NONE:
           name = None
        else:
           _LOGGER.error("Error setting preset mode, mode " + preset_mode + " unknown")

        if value is not None:
            self.uhome.set_module_value(name, value)
        value = '0'
        name= 'allow_hc_mode_change'
        self.uhome.set_module_value(name, value)
        self._preset_mode = preset_mode

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_TENTHS

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            value = '1'
            name= 'setpoint_write_enable'
            self.uhome.set_module_value(name, value)
            name = 'holiday_setpoint'
            value = kwargs.get(ATTR_TEMPERATURE)
            self.uhome.set_module_value(name, value)
            value = '0'
            name= 'setpoint_write_enable'
            self.uhome.set_module_value(name, value)

    def update(self):
        """Fetch new state data for the thermostat.
        This is the only method that should fetch new data for Home Assistant.
        """
        self.uhome.update_keys(self.uhome.uhome_module_keys)
