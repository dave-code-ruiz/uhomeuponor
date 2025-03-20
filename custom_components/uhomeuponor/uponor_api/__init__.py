"""UHome Uponor API client"""

import logging
import requests
import json

from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from .const import *
from .utilities import *

_LOGGER = logging.getLogger(__name__)

class UponorAPIException(Exception):
    def __init__(self, message, inner_exception=None):
        if inner_exception:
            super().__init__(f"{message}: {inner_exception}")
        else:
            super().__init__(message)
        self.inner_exception = inner_exception

class UponorClient(object):
    """API Client for Uponor U@Home API"""

    def __init__(self, hass, server):
        self.hass = hass
        self.server = server
        self.uhome = UponorUhome(self)
        self.controllers = []
        self.thermostats = []

        self.max_update_interval = timedelta(seconds=60)
        self.max_values_batch = 40

        self.server_uri = f"http://{self.server}/api"

    async def rescan(self):
        # Initialize
        await self.uhome.async_update()
        await self.init_controllers()
        await self.init_thermostats()

    async def init_controllers(self):
        """
        Identifies present controllers from U@Home.
        """

        self.controllers.clear()

        # A value of 3 (0011) will indicate that controllers 0 (0001) and 1 (0010) are present
        bitMask = self.uhome.by_name("controller_presence").value

        for i in range(0, 4):
            mask = 1 << i

            if bitMask & mask:
                # Controller i is present
                self.controllers.append(UponorController(self, i))
            
        #_LOGGER.debug("Identified %d controllers", len(self.controllers))

        # Update all controllers
        await self.update_devices(self.controllers)

    async def init_thermostats(self):
        """
        Identifies present thermostats from U@Home.
        """

        self.thermostats.clear()

        # A value of 31 (0000 0001 1111) will indicate that thermostats 0 (0000 0000 0001) through 4 (0000 0001 0000) are present
        for controller in self.controllers:
            bitMask = controller.by_name('thermostat_presence').value

            for i in range(0, 12):
                mask = 1 << i

                if bitMask & mask:
                    # Thermostat i is present
                    self.thermostats.append(UponorThermostat(self, controller.controller_index, i))
            
        #_LOGGER.debug("Identified %d thermostats on %d controllers", len(self.thermostats), len(self.controllers))

        # Update all thermostats
        await self.update_devices(self.thermostats)

    def create_request(self, method):
        req = {
            'jsonrpc': "2.0",
            'id': 8,
            'method': method,
            'params': {
                'objects': []
            }
        }

        return req

    def add_request_object(self, req, obj):
        req['params']['objects'].append(obj)

    async def do_rest_call(self, requestObject):
        data = json.dumps(requestObject)

        response = None
        try:
            response = await self.hass.async_add_executor_job(lambda: requests.post(self.server_uri, data=data))
        except requests.exceptions.RequestException as ex:
            raise UponorAPIException("API call error", ex)

        if response.status_code != 200:
            raise UponorAPIException("Unsucessful API call")

        response_data = json.loads(response.text)
        
        #_LOGGER.debug("Issued API request type '%s' for %d objects, return code %d", requestObject['method'], len(requestObject['params']['objects']), response.status_code)

        return response_data
    
    async def update_devices(self, *devices):
        """Updates all values of all devices provided by making API calls. Only devices not updated recently will be considered"""
        devices = flatten(devices)
        
        # Filter devices to include devices if either:
        # - Device has never been updated
        # - Device was last updated max_update_interval time ago
        devices_to_update = [device for device in devices if (not device.pending_update and (device.last_update is None or (datetime.now() - device.last_update) > self.max_update_interval))]

        if len(devices_to_update) == 0:
            return

        values = []
        for device in devices_to_update:
            values.extend(device.properties_byid.values())
            device.pending_update = True

        #Create dict for all devices
        allvalues = []
        for device in self.thermostats:
            allvalues.extend(device.properties_byid.values())
        allvalues = flatten(allvalues)
        allvalue_dict = {}
        for value in allvalues:
            allvalue_dict[value.id] = value

        #_LOGGER.debug("Requested update %d values of %d devices, skipped %d devices", len(values), len(devices_to_update), len(devices) - len(devices_to_update))

        try:
            # Update all values, but at most N at a time
            for value_list in chunks(values, self.max_values_batch):
                await self.update_values(allvalue_dict, value_list)
        except Exception as e:
            _LOGGER.exception(e)
            for device in devices_to_update:
                device.pending_update = False
            raise

        for device in devices_to_update:
            device.last_update = datetime.now()
            device.pending_update = False

    async def update_values(self, allvalue_dict, *values):
        """Updates all values provided by making API calls"""
        values = flatten(values)

        if len(values) == 0:
            return

        #_LOGGER.debug("Requested update of %d values", len(values))

        value_dict = {}
        for value in values:
            value_dict[value.id] = value

        req = self.create_request("read")
        for value in values:
            obj = {'id': str(value.id), 'properties': {str(value.property): {}}}
            self.add_request_object(req, obj)

        response_data = await self.do_rest_call(req)

        if self.validate_values(response_data, allvalue_dict):
            for obj in response_data['result']['objects']:
                try:
                    data_id = int(obj['id'])
                    value = value_dict[data_id]
                    data_val = obj['properties'][value.property]['value']
                except Exception as e:
                    continue

                value.value = data_val

    def getStepValue(self, id, therm):
        #Obtain addr of THERMOSTAT_KEY, thermostatindex and controllerindex
        #Obtain step jump between thermostats (40,80,..)
        c=0
        t=0
        step=0
        for i in range(4):
            if id > 500:
                id=id-500
                c=c+1
        id=id-80
        for i in range(9):
            if id > 40:
                id=id-40
                t=t+1
        data_addr=id, t, c
        if data_addr[0] in (11,25,28):
            nextt=0
            for t in therm:
               if nextt==1:
                   nextt=t
               if t[0] == data_addr[1] and t[1] == data_addr[2]:
                   nextt=1
            if nextt != 0 and nextt !=1 and nextt[1] == data_addr[2]:
                step=(nextt[0]-data_addr[1])*40
        return step

    def validate_values(self,response_data,allvalue_dict):

        #Function to detect same values errors
        #api sometimes generate response errors that show values of the next thermostat
        #this function evaluate response and detect if values are values of the next thermostat, in that case, values do not sets
        samevalue = 0
        therm=[]
        for thermostat in self.thermostats:
            therm.append([thermostat.thermostat_index,thermostat.controller_index])
        for obj in response_data['result']['objects']:
            try:
                data_id = int(obj['id'])
                value = allvalue_dict[data_id]
                data_val = obj['properties'][value.property]['value']
                step=self.getStepValue(data_id,therm)
                #only is necesary validate values in addrs 11,25,28, rest of values do not change
                if step != 0:
                    if allvalue_dict[data_id]:
                        oldvalue=allvalue_dict[data_id]
                    if allvalue_dict[data_id+step]:
                        nextvalue=allvalue_dict[data_id+step]
                        if nextvalue.value == data_val:
                            samevalue=samevalue+1
                        else:
                            res=nextvalue.value-oldvalue.value
                            if res > 0:
                                if res >= 1 and str(data_id)[len(str(data_id))-1:len(str(data_id))] != '8':
                                    res = res*3/4
                                    if data_val > oldvalue.value+res:
                                        samevalue=samevalue+1
                            else:
                                res=res*-1
                                if res >= 1 and str(data_id)[len(str(data_id))-1:len(str(data_id))] != '8':
                                    res = res*3/4
                                    if data_val < oldvalue.value-res:
                                        samevalue=samevalue+1
                    #_LOGGER.debug("Response values, id %d, value %s, samevalue %d, old %s, idnext %s, next %s",data_id,data_val,samevalue,oldvalue.value,data_id+step,nextvalue.value)

            except Exception as e:
                if '85' not in str(e) and '662' not in str(e):
                    _LOGGER.debug("Response error %s obj %s",e,obj)
                continue

        if samevalue == 3:
            _LOGGER.warning("Response error in API, wrong value, not updated sensor")
            _LOGGER.debug("Response error in API, same value in different thermostat not updated in this response API: %s ",response_data['result']['objects'])
            return False
        else:
            return True

    async def set_values(self, *value_tuples):
        """Writes values to UHome, accepts tuples of (UponorValue, New Value)"""
        
        #_LOGGER.debug("Requested write to %d values", len(value_tuples))

        req = self.create_request("write")

        for tpl in value_tuples:
            obj = {'id': str(tpl[0].id), 'properties': {str(tpl[0].property): {'value': str(tpl[1])}}}
            self.add_request_object(req, obj)

        await self.do_rest_call(req)

        # Apply new values, after the API call succeeds
        for tpl in value_tuples:
            tpl[0].value = tpl[1]

class UponorValue(object):
    """Single value in the Uponor API"""

    def __init__(self, id, name, prop):
        self.id = id
        self.name = name
        self.value = 0
        self.property = prop

class UponorBaseDevice(ABC):
    """Base device class"""

    def __init__(self, uponor_client, id_offset, properties, identity_string):
        self.uponor_client = uponor_client
        self.id_offset = id_offset
        self.properties_byname = {}
        self.properties_byid = {}
        self.properties = properties
        self.last_update = None
        self.pending_update = False
        self.identity_string = identity_string

        for key_name, key_data in properties.items():
            value = UponorValue(id_offset + key_data['addr'], key_name, key_data['property'])
            self.properties_byid[value.id] = value
            self.properties_byname[value.name] = value
    
    def by_id(self, id):
        return self.properties_byid[id]

    def by_name(self, name):
        return self.properties_byname[name]

    def attributes(self):
        attr = None
        for key_name, key_data in self.properties.items():
            attr = str(attr) + str(key_name) + ': ' + str(self.properties_byname[key_name].value) + '#'
        return attr

    async def async_update(self):
        #_LOGGER.debug("Updating %s, device '%s'", self.__class__.__name__, self.identity_string)

        await self.uponor_client.update_devices(self)

    @abstractmethod
    def is_valid(self):
        pass

class UponorUhome(UponorBaseDevice):
    """U@Home API device class, typically an R-167"""
    
    def __init__(self, uponor_client):
        super().__init__(uponor_client, 0, UHOME_MODULE_KEYS, "U@Home")

    def is_valid(self):
        return True

class UponorController(UponorBaseDevice):
    """Controller API device class, typically an X-165"""
    
    def __init__(self, uponor_client, controller_index):
        # Offset: 60 + 500 x c
        super().__init__(uponor_client, 60 + 500 * controller_index, UHOME_CONTROLLER_KEYS, str(controller_index))

        self.controller_index = controller_index

    def is_valid(self):
        return True

class UponorThermostat(UponorBaseDevice):
    """Thermostat API device class, typically an T-169"""
    
    def __init__(self, uponor_client, controller_index, thermostat_index):
        # Offset: 80 + 500 x c + 40 x t
        super().__init__(uponor_client, 80 + 500 * controller_index + 40 * thermostat_index, UHOME_THERMOSTAT_KEYS, f"{controller_index} / {thermostat_index}")
        self.controller_index = controller_index
        self.thermostat_index = thermostat_index

    def is_valid(self):
        # A Thermostat is valid if the temperature is -40<=T<=100 C* and the setpoint is 5<=S<=35 C*
        return -40 <= self.by_name('room_temperature').value and self.by_name('room_temperature').value <= 100 and \
               1 <= self.by_name('room_setpoint').value and self.by_name('room_setpoint').value <= 40

    async def set_name(self, name):
        """Updates the thermostats room name to a new value"""
        await self.uponor_client.set_values((self.by_name('room_name'), name))

    async def set_setpoint(self, temperature):
        """Updates the thermostats setpoint to a new value"""
        await self.uponor_client.set_values(
                (self.by_name('setpoint_write_enable'), 0),
                (self.by_name('room_setpoint'), temperature)
            )

    async def set_hvac_mode(self, value):
        """Updates the thermostats mode to a new value"""
        await self.uponor_client.set_values(
                (self.uponor_client.uhome.by_name('allow_hc_mode_change'), 0),
                (self.uponor_client.uhome.by_name('hc_mode'), value),
            )

    async def set_preset_mode(self, value):
        """Updates the thermostats mode to a new value"""
        await self.uponor_client.set_values((self.uponor_client.uhome.by_name('forced_eco_mode'), value))

    async def set_manual_mode(self):
        await self.uponor_client.set_values(
                (self.uponor_client.uhome.by_name('setpoint_write_enable'), 1),
                (self.uponor_client.uhome.by_name('rh_control_activation'), 1),
                (self.uponor_client.uhome.by_name('dehumidifier_control_activation'), 0),
                (self.uponor_client.uhome.by_name('setpoint_write_enable'), 0),
            )

    async def set_auto_mode(self):
        await self.uponor_client.set_values(
                (self.uponor_client.uhome.by_name('setpoint_write_enable'), 1),
                (self.uponor_client.uhome.by_name('rh_control_activation'), 0),
                (self.uponor_client.uhome.by_name('dehumidifier_control_activation'), 0),
                (self.uponor_client.uhome.by_name('setpoint_write_enable'), 0),
            )
