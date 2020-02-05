"""Uponor U@Home integration
Exposes Sensors for Uponor devices, such as:

- Temperature (UponorThermostatTemperatureSensor)
- Humidity (UponorThermostatHumiditySensor)
- Battery (UponorThermostatBatterySensor)
"""

import voluptuous as vol

from requests.exceptions import RequestException

from homeassistant.exceptions import PlatformNotReady
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ATTRIBUTION, 
    CONF_NAME, CONF_HOST, CONF_PREFIX, 
    TEMP_CELSIUS, 
    DEVICE_CLASS_BATTERY, DEVICE_CLASS_HUMIDITY, DEVICE_CLASS_TEMPERATURE)
import homeassistant.helpers.config_validation as cv
from logging import getLogger
from homeassistant.helpers.entity import Entity

from .uponor_api import UponorClient

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
    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    prefix = config.get(CONF_PREFIX)

    uponor = UponorClient(server=host)
    try:
        uponor.rescan()
    except (ValueError, RequestException) as err:
        _LOGGER.error("Received error from UHOME: %s", err)
        raise PlatformNotReady

    add_entities([UponorThermostatTemperatureSensor(prefix, uponor, thermostat)
                  for thermostat in uponor.thermostats], True)

    add_entities([UponorThermostatHumiditySensor(prefix, uponor, thermostat)
                  for thermostat in uponor.thermostats], True)

    add_entities([UponorThermostatBatterySensor(prefix, uponor, thermostat)
                  for thermostat in uponor.thermostats], True)

    _LOGGER.info("finish setup sensor platform for Uhome Uponor")

class UponorThermostatTemperatureSensor(Entity):
    """HA Temperature sensor entity. Utilizes Uponor U@Home API to interact with U@Home"""

    def __init__(self, prefix, uponor_client, thermostat):
        self.prefix = prefix
        self.uponor_client = uponor_client
        self.thermostat = thermostat

        self.identity = f"{prefix or ''}controller{thermostat.controller_index}_thermostat{thermostat.thermostat_index}_temp"

    # ** Generic **
    @property
    def name(self):
        return f"{self.prefix or ''}{self.thermostat.by_name('room_name').value}"

    @property
    def unique_id(self):
        return self.identity

    @property
    def icon(self):
        return 'mdi:thermometer'

    # ** Static **
    @property
    def unit_of_measurement(self):
        return TEMP_CELSIUS

    @property
    def device_class(self):
        return DEVICE_CLASS_TEMPERATURE

    # ** State **
    @property
    def state(self):
        return self.thermostat.by_name('room_temperature').value

    # ** Actions **
    def update(self):
        # Update thermostat
        self.thermostat.update()

class UponorThermostatHumiditySensor(Entity):
    """HA Humidity sensor entity. Utilizes Uponor U@Home API to interact with U@Home"""

    def __init__(self, prefix, uponor_client, thermostat):
        self.prefix = prefix
        self.uponor_client = uponor_client
        self.thermostat = thermostat

        self.identity = f"{prefix or ''}controller{thermostat.controller_index}_thermostat{thermostat.thermostat_index}_rh"

    # ** Generic **
    @property
    def name(self):
        return f"{self.prefix or ''}{self.thermostat.by_name('room_name').value} Humidity"

    @property
    def unique_id(self):
        return self.identity

    @property
    def icon(self):
        return 'mdi:water-percent'

    # ** Static **
    @property
    def unit_of_measurement(self):
        # TODO: Constant
        return '%'

    @property
    def device_class(self):
        return DEVICE_CLASS_HUMIDITY

    # ** State **
    @property
    def state(self):
        return self.thermostat.by_name('rh_value').value

    # ** Actions **
    def update(self):
        # Update thermostat
        self.thermostat.update()

class UponorThermostatBatterySensor(Entity):
    """HA Battery sensor entity. Utilizes Uponor U@Home API to interact with U@Home"""

    def __init__(self, prefix, uponor_client, thermostat):
        self.prefix = prefix
        self.uponor_client = uponor_client
        self.thermostat = thermostat

        self.identity = f"{prefix or ''}controller{thermostat.controller_index}_thermostat{thermostat.thermostat_index}_batt"

    # ** Generic **
    @property
    def name(self):
        return f"{self.prefix or ''}{self.thermostat.by_name('room_name').value} Battery"

    @property
    def unique_id(self):
        return self.identity

    # ** Static **
    @property
    def unit_of_measurement(self):
        # TODO: Constant
        return '%'

    @property
    def device_class(self):
        return DEVICE_CLASS_BATTERY

    # ** State **
    @property
    def state(self):
        # If there is a battery alarm, report a low level - else report 100%
        if self.thermostat.by_name('battery_alarm').value == 1:
            return 10

        return 100

    # ** Actions **
    def update(self):
        # Update thermostat
        self.thermostat.update()
