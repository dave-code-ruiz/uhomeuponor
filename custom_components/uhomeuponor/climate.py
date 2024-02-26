"""Uponor U@Home integration
Exposes Climate control entities for Uponor thermostats

- UponorThermostat
"""

import voluptuous as vol

from requests.exceptions import RequestException

from homeassistant.exceptions import PlatformNotReady
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVACMode, PRESET_COMFORT, PRESET_ECO, HVACAction, ClimateEntityFeature)
from homeassistant.const import (ATTR_TEMPERATURE, CONF_HOST, CONF_PREFIX, PRECISION_TENTHS, UnitOfTemperature)
from logging import getLogger

from .uponor_api import UponorClient
from .uponor_api.const import (DOMAIN, UHOME_MODE_HEAT, UHOME_MODE_COOL, UHOME_MODE_ECO, UHOME_MODE_COMFORT)

CONF_SUPPORTS_HEATING = "supports_heating"
CONF_SUPPORTS_COOLING = "supports_cooling"

ATTR_TECHNICAL_ALARM = "technical_alarm"
ATTR_RF_SIGNAL_ALARM = "rf_alarm"
ATTR_BATTERY_ALARM = "battery_alarm"

_LOGGER = getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    _LOGGER.info("init setup climate platform for id: %s data: %s, options: %s", config_entry.entry_id, config_entry.data, config_entry.options)
    config = config_entry.data
    return await async_setup_climate(
        hass, config, async_add_entities, discovery_info=None
    )

async def async_setup_climate(
     hass, config, async_add_entities, discovery_info=None
 ) -> bool:
     """Set up climate for device."""
     host = config[CONF_HOST]
     prefix = config[CONF_PREFIX]
     supports_heating = config[CONF_SUPPORTS_HEATING] or True
     supports_cooling = config[CONF_SUPPORTS_COOLING] or True

     _LOGGER.info("init setup host %s", host)

     uponor = await hass.async_add_executor_job(lambda: UponorClient(hass=hass, server=host))
     try:
         await uponor.rescan()
     except (ValueError, RequestException) as err:
         _LOGGER.error("Received error from UHOME: %s", err)
         raise PlatformNotReady
    
     async_add_entities([UponorThermostat(prefix, uponor, thermostat, supports_heating, supports_cooling)
                   for thermostat in uponor.thermostats], True)
    
     _LOGGER.info("finish setup climate platform for Uhome Uponor")
     return True

class UponorThermostat(ClimateEntity):
    """HA Thermostat climate entity. Utilizes Uponor U@Home API to interact with U@Home"""

    def __init__(self, prefix, uponor_client, thermostat, supports_heating, supports_cooling):
        self._available = False
        self.prefix = prefix
        self.uponor_client = uponor_client
        self.thermostat = thermostat
        self.supports_heating = supports_heating
        self.supports_cooling = supports_cooling
        self.device_name = f"{prefix or ''}{thermostat.by_name('room_name').value}"
        self.device_id = f"{prefix or ''}controller{str(thermostat.controller_index)}_thermostat{str(thermostat.thermostat_index)}"
        self.identity = f"{prefix or ''}controller{str(thermostat.controller_index)}_thermostat{str(thermostat.thermostat_index)}_thermostat"

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
    def available(self):
        return self._available

    # ** Static **
    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    @property
    def precision(self):
        return PRECISION_TENTHS

    @property
    def target_temperature_step(self):
        return '0.5'

    @property
    def supported_features(self):
        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE

    @property
    def hvac_modes(self):
        modes = []

        if self.supports_heating:
            modes.append(HVACMode.HEAT)

        if self.supports_cooling:
            modes.append(HVACMode.COOL)

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
    def extra_state_attributes(self):
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
            return HVACMode.COOL

        return HVACMode.HEAT

    @property
    def hvac_action(self):
        if self.thermostat.by_name('room_in_demand').value == 0:
            return HVACAction.IDLE
        
        if self.hvac_mode == HVACMode.HEAT:
            return HVACAction.HEATING
        else:
            return HVACAction.COOLING

    # ** Actions **
    async def async_update(self):
        # Update Uhome (to get HC mode) and thermostat
        try:
            await self.uponor_client.update_devices(self.uponor_client.uhome, self.thermostat)
            valid = self.thermostat.is_valid()
            self._available = valid
            if not valid:
                _LOGGER.debug("The thermostat '%s' had invalid data, and is therefore unavailable", self.identity)
        except Exception as ex:
            self._available = False
            _LOGGER.error("Uponor thermostat was unable to update: %s", ex)

    def set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.HEAT:
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
