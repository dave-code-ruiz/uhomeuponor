"""Platform for sensor integration."""

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION, CONF_NAME, CONF_HOST, CONF_PREFIX, TEMP_CELSIUS
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from logging import getLogger
from custom_components.uhomeuponor import (Uhome)

import requests
import voluptuous as vol
import json

ATTR_REMOTE_ACCESS_ALARM = "remote_access_alarm"
ATTR_DEVICE_LOST_ALARM = "device_lost_alarm"
ATTR_TECHNICAL_ALARM = "technical_alarm"
ATTR_RF_SIGNAL_ALARM = "rf_alarm"
ATTR_BATTERY_ALARM = "battery_alarm"

_LOGGER = getLogger(__name__)

DEFAULT_NAME = 'Uhome Uponor'


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PREFIX): cv.string,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    prefix = config.get(CONF_PREFIX)

    uhome = Uhome(ip=host)
    try:
        uhome.update()
    except (ValueError, TypeError) as err:
        _LOGGER.error("Received error from UHOME: %s", err)
        return False

    add_entities([UHomeSensor(host, prefix, uhome, thermostat)
                  for thermostat in uhome.uhome_thermostats], True)

    add_entities([UHomeRHSensor(host, prefix, uhome, thermostat)
                  for thermostat in uhome.uhome_thermostats], True)

    add_entities([UHomeSensorAlarm(host, prefix, uhome)])


    _LOGGER.info("finish setup platform sensor Uhome Uponor")

class UHomeRHSensor(Entity, Uhome):
    """Representation of a Sensor."""

    def __init__(self, host, prefix, uhome, thermostat):
        """Initialize the sensor."""
        self.host = host
        self.prefix = prefix
        self.uhome = uhome
        self.thermostat = thermostat

        self.identity = thermostat.identity + "_rh"
        if not prefix is None:
            self.identity = str(prefix) + self.identity

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self.identity

    @property
    def name(self):
        """Return the name of the sensor."""
        if self.prefix is None:
            return "Humidity_" + str(self.thermostat.uhome_thermostat_keys['room_name']['value'])
        else:
            return str(self.prefix) + "Humidity_" + str(self.thermostat.uhome_thermostat_keys['room_name']['value'])

    @property
    def state(self):
        """Return the state of the sensor."""
        value = self.thermostat.uhome_thermostat_keys['rh_value']['value']
        return value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return '%'

    @property
    def icon(self):
        """Return sensor specific icon."""
        return 'mdi:water-percent'

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        attr = ""
        attr = str(attr) + "rh_control_activation: " + str(self.thermostat.uhome_thermostat_keys['rh_control_activation']['value']) + '#'
        attr = str(attr) + "rh_setpoint: " + str(self.thermostat.uhome_thermostat_keys['rh_setpoint']['value']) + '#'
        attr = str(attr) + "rh_limit_reached: " + str(self.thermostat.uhome_thermostat_keys['rh_limit_reached']['value']) + '#'
        attr = str(attr) + "rh_sensor: " + str(self.thermostat.uhome_thermostat_keys['rh_sensor']['value']) + '#'
        attr = str(attr) + "rh_value: " + str(self.thermostat.uhome_thermostat_keys['rh_value']['value']) + '#'
        return {
            ATTR_ATTRIBUTION: attr,
        }

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self.uhome.update_keys(self.thermostat.uhome_thermostat_keys)

class UHomeSensor(Entity, Uhome):
    """Representation of a Sensor."""

    def __init__(self, host, prefix, uhome, thermostat):
        """Initialize the sensor."""
        self.host = host
        self.prefix = prefix
        self.uhome = uhome
        self.thermostat = thermostat
        self.identity = thermostat.identity + "_temp"
        if not prefix is None:
            self.identity = str(prefix) + self.identity

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self.identity

    @property
    def name(self):
        """Return the name of the sensor."""
        if self.prefix is None:
            return str(self.thermostat.uhome_thermostat_keys['room_name']['value'])
        else:
            return str(self.prefix) + str(self.thermostat.uhome_thermostat_keys['room_name']['value'])

    @property
    def state(self):
        """Return the state of the sensor."""
        value = self.thermostat.uhome_thermostat_keys['room_temperature']['value']
        return value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def icon(self):
        """Return sensor specific icon."""
        return 'mdi:thermometer'

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        attr = None
        for key_name, key_data in self.thermostat.uhome_thermostat_keys.items():
            attr = str(attr) + str(key_name) + ': ' + str(key_data['value']) + '#'

        for uc in self.uhome.uhome_controllers:
            for key_name, key_data in uc.uhome_controller_keys.items():
                attr = str(attr) + str(key_name) + ': ' + str(key_data['value']) + '#'

        for key_name, key_data in self.uhome.uhome_module_keys.items():
            attr = str(attr) + str(key_name) + ': ' + str(key_data['value']) + '#'

        return {
            ATTR_ATTRIBUTION: attr,
        }

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self.uhome.update_keys(self.uhome.uhome_module_keys)
        self.uhome.update_keys(self.thermostat.uhome_thermostat_keys)

class UHomeSensorAlarm(Entity, Uhome):
    """Representation of a Sensor."""

    def __init__(self, host, prefix, uhome):
        """Initialize the sensor."""
        self.host = host
        self.prefix = prefix
        self.uhome = uhome
        self.identity = "sensoralarm"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self.identity

    @property
    def name(self):
        """Return the name of the sensor."""
        if self.prefix is None:
            return "SensorAlarm"
        else:
            return str(self.prefix) + "SensorAlarm"

    @property
    def state(self):
        """Return the state of the sensor."""
        value = "off"
        for thermostat in self.uhome.uhome_thermostats:
            if thermostat.uhome_thermostat_keys[ATTR_TECHNICAL_ALARM]['value'] != 0:
                value = ATTR_TECHNICAL_ALARM + " in " + thermostat.uhome_thermostat_keys['room_name']['value']
            if thermostat.uhome_thermostat_keys[ATTR_RF_SIGNAL_ALARM]['value'] != 0:
                value = ATTR_RF_SIGNAL_ALARM + " in " + thermostat.uhome_thermostat_keys['room_name']['value']
            if thermostat.uhome_thermostat_keys[ATTR_BATTERY_ALARM]['value'] != 0:
                value = ATTR_BATTERY_ALARM + " in " + thermostat.uhome_thermostat_keys['room_name']['value']
        if self.uhome.uhome_module_keys[ATTR_REMOTE_ACCESS_ALARM]['value'] != 0:
            value = ATTR_REMOTE_ACCESS_ALARM
        if self.uhome.uhome_module_keys[ATTR_DEVICE_LOST_ALARM]['value'] != 0:
            value = ATTR_DEVICE_LOST_ALARM
        return value

    @property
    def icon(self):
        """Return sensor specific icon."""
        return 'mdi:alert'

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self.uhome.update_keys(self.uhome.uhome_module_keys)
