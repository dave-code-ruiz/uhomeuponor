"""Uponor U@Home integration
Exposes Sensors for Uponor devices, such as:

- Temperature (UponorThermostatTemperatureSensor)
- Humidity (UponorThermostatHumiditySensor)
- Battery (UponorThermostatBatterySensor)
"""

import voluptuous as vol

from requests.exceptions import RequestException

from homeassistant.exceptions import PlatformNotReady
from homeassistant.components.sensor import (PLATFORM_SCHEMA, SensorDeviceClass, SensorStateClass)
from homeassistant.const import (CONF_HOST, CONF_PREFIX, ATTR_ATTRIBUTION, UnitOfTemperature)
import homeassistant.helpers.config_validation as cv
from logging import getLogger
from homeassistant.components.sensor import SensorEntity

from .uponor_api import UponorClient
from .uponor_api.const import (DOMAIN, UNIT_BATTERY, UNIT_HUMIDITY)

_LOGGER = getLogger(__name__)

DEFAULT_NAME = 'Uhome Uponor'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PREFIX): cv.string,
})


async def async_setup_entry(hass, config_entry, async_add_entities):
    _LOGGER.info("init setup sensor platform for id: %s data: %s, options: %s", config_entry.entry_id, config_entry.data, config_entry.options)
    config = config_entry.data
    return await async_setup_sensor(
        hass, config, async_add_entities, discovery_info=None
    )
    
async def async_setup_sensor(
     hass, config, async_add_entities, discovery_info=None
 ) -> bool:
     
     host = config[CONF_HOST]
     prefix = config[CONF_PREFIX]

     _LOGGER.info("init setup host %s", host)

     uponor = await hass.async_add_executor_job(lambda: UponorClient(hass=hass, server=host))
     try:
         await uponor.rescan()
     except (ValueError, RequestException) as err:
         _LOGGER.error("Received error from UHOME: %s", err)
         raise PlatformNotReady

     async_add_entities([UponorThermostatTemperatureSensor(prefix, uponor, thermostat)
                   for thermostat in uponor.thermostats], True)

     async_add_entities([UponorThermostatHumiditySensor(prefix, uponor, thermostat)
                   for thermostat in uponor.thermostats], True)

     async_add_entities([UponorThermostatBatterySensor(prefix, uponor, thermostat)
                   for thermostat in uponor.thermostats], True)

     _LOGGER.info("finish setup sensor platform for Uhome Uponor")
     return True

class UponorThermostatTemperatureSensor(SensorEntity):
    """HA Temperature sensor entity. Utilizes Uponor U@Home API to interact with U@Home"""

    def __init__(self, prefix, uponor_client, thermostat):
        self._available = False
        self.prefix = prefix
        self.uponor_client = uponor_client
        self.thermostat = thermostat
        self.device_name = f"{prefix or ''}{thermostat.by_name('room_name').value}"
        self.device_id = f"{prefix or ''}controller{thermostat.controller_index}_thermostat{thermostat.thermostat_index}"
        self.identity = f"{prefix or ''}controller{thermostat.controller_index}_thermostat{thermostat.thermostat_index}_temp"

    @property
    def device_info(self) -> dict:
        """Return info for device registry."""
        return {
            "identifiers": {(DOMAIN, self.device_id)},
            "name": self.device_name,
        }

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

    @property
    def available(self):
        return self._available

    # ** DEBUG PROPERTY  **
    # @property
    # def extra_state_attributes(self):
    #     """Return the device state attributes."""
    #     attr = self.thermostat.attributes() + self.uponor_client.uhome.attributes()
    #     return {
    #         ATTR_ATTRIBUTION: attr,
    #     }

    # ** Static **
    @property
    def unit_of_measurement(self):
        return UnitOfTemperature.CELSIUS

    @property
    def device_class(self):
        return SensorDeviceClass.TEMPERATURE

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    # ** State **
    @property
    def state(self):
        return self.thermostat.by_name('room_temperature').value

    # ** Actions **
    async def async_update(self):
        # Update thermostat
        try:
            await self.thermostat.async_update()
            valid = self.thermostat.is_valid()
            self._available = valid
            if not valid:
                _LOGGER.debug("The thermostat temperature sensor '%s' had invalid data, and is therefore unavailable", self.identity)
        except Exception as ex:
            self._available = False
            _LOGGER.error("Uponor thermostat temperature sensor was unable to update: %s", ex)

class UponorThermostatHumiditySensor(SensorEntity):
    """HA Humidity sensor entity. Utilizes Uponor U@Home API to interact with U@Home"""

    def __init__(self, prefix, uponor_client, thermostat):
        self._available = False
        self.prefix = prefix
        self.uponor_client = uponor_client
        self.thermostat = thermostat
        self.device_name = f"{prefix or ''}{thermostat.by_name('room_name').value}"
        self.device_id = f"{prefix or ''}controller{thermostat.controller_index}_thermostat{thermostat.thermostat_index}"
        self.identity = f"{prefix or ''}controller{thermostat.controller_index}_thermostat{thermostat.thermostat_index}_rh"

    @property
    def device_info(self) -> dict:
        """Return info for device registry."""
        return {
            "identifiers": {(DOMAIN, self.device_id)},
            "name": self.device_name,
        }

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

    @property
    def available(self):
        return self._available

    # ** Static **
    @property
    def unit_of_measurement(self):
        return UNIT_HUMIDITY

    @property
    def device_class(self):
        return SensorDeviceClass.HUMIDITY

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    # ** State **
    @property
    def state(self):
        return self.thermostat.by_name('rh_value').value

    # ** Actions **
    async def async_update(self):
        # Update thermostat
        try:
            await self.thermostat.async_update()
            valid = self.thermostat.is_valid()
            self._available = valid

            if not valid:
                _LOGGER.debug("The thermostat humidity sensor '%s' had invalid data, and is therefore unavailable", self.identity)
        except Exception as ex:
            self._available = False
            _LOGGER.error("Uponor thermostat humidity sensor was unable to update: %s", ex)

class UponorThermostatBatterySensor(SensorEntity):
    """HA Battery sensor entity. Utilizes Uponor U@Home API to interact with U@Home"""

    def __init__(self, prefix, uponor_client, thermostat):
        self._available = False
        self.prefix = prefix
        self.uponor_client = uponor_client
        self.thermostat = thermostat
        self.device_name = f"{prefix or ''}{thermostat.by_name('room_name').value}"
        self.device_id = f"{prefix or ''}controller{thermostat.controller_index}_thermostat{thermostat.thermostat_index}"
        self.identity = f"{prefix or ''}controller{thermostat.controller_index}_thermostat{thermostat.thermostat_index}_batt"

    @property
    def device_info(self) -> dict:
        """Return info for device registry."""
        return {
            "identifiers": {(DOMAIN, self.device_id)},
            "name": self.device_name,
        }

    # ** Generic **
    @property
    def name(self):
        return f"{self.prefix or ''}{self.thermostat.by_name('room_name').value} Battery"

    @property
    def unique_id(self):
        return self.identity

    @property
    def available(self):
        return self._available

    # ** Static **
    @property
    def unit_of_measurement(self):
        return UNIT_BATTERY

    @property
    def device_class(self):
        return SensorDeviceClass.BATTERY

    # ** State **
    @property
    def state(self):
        # If there is a battery alarm, report a low level - else report 100%
        if self.thermostat.by_name('battery_alarm').value == 1:
            return 10

        return 100

    # ** Actions **
    async def async_update(self):
        # Update thermostat
        try:
            await self.thermostat.async_update()
            valid = self.thermostat.is_valid()
            self._available = valid

            if not valid:
                _LOGGER.debug("The thermostat battery sensor '%s' had invalid data, and is therefore unavailable", self.identity)
        except Exception as ex:
            self._available = False
            _LOGGER.error("Uponor thermostat battery sensor was unable to update: %s", ex)
