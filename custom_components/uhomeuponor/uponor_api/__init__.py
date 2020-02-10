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

    def __init__(self, server):
        self.server = server
        self.uhome = UponorUhome(self)
        self.controllers = []
        self.thermostats = []

        self.max_update_interval = timedelta(seconds=10)
        self.max_values_batch = 40

        self.server_uri = f"http://{self.server}/api"

    def rescan(self):
        # Initialize
        self.uhome.update()
        self.init_controllers()
        self.init_thermostats()

    def init_controllers(self):
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
            
        _LOGGER.debug("Identified %d controllers", len(self.controllers))

        # Update all controllers
        self.update_devices(self.controllers)

    def init_thermostats(self):
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
            
        _LOGGER.debug("Identified %d thermostats on %d controllers", len(self.thermostats), len(self.controllers))

        # Update all thermostats
        self.update_devices(self.thermostats)

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

    def do_rest_call(self, requestObject):
        data = json.dumps(requestObject)

        response = None
        try:
            response = requests.post(self.server_uri, data=data)
        except requests.exceptions.RequestException as ex:
            raise UponorAPIException("API call error", ex)

        if response.status_code != 200:
            raise UponorAPIException("Unsucessful API call")

        response_data = json.loads(response.text)
        
        _LOGGER.debug("Issued API request type '%s' for %d objects, return code %d", requestObject['method'], len(requestObject['params']['objects']), response.status_code)

        return response_data

    def update_devices(self, *devices):
        """Updates all values of all devices provided by making API calls. Only devices not updated recently will be considered"""
        devices = flatten(devices)
        
        # Filter devices to include devices if either:
        # - Device has never been updated
        # - Device was last updated max_update_interval time ago
        devices_to_update = [device for device in devices if (device.last_update is None or (datetime.now() - device.last_update) > self.max_update_interval)]

        values = []
        for device in devices_to_update:
            values.extend(device.properties_byid.values())

        _LOGGER.debug("Requested update %d values of %d devices, skipped %d devices", len(values), len(devices_to_update), len(devices) - len(devices_to_update))

        # Update all values, but at most N at a time
        for value_list in chunks(values, self.max_values_batch):
            self.update_values(value_list)

        for device in devices_to_update:
            device.last_update = datetime.now()

    def update_values(self, *values):
        """Updates all values provided by making API calls"""
        values = flatten(values)

        if len(values) == 0:
            return

        _LOGGER.debug("Requested update of %d values", len(values))

        value_dict = {}
        for value in values:
            value_dict[value.id] = value

        req = self.create_request("read")
        for value in values:
            obj = {'id': str(value.id), 'properties': {'85': {}}}
            self.add_request_object(req, obj)
            
        response_data = self.do_rest_call(req)

        for obj in response_data['result']['objects']:
            try:
                data_id = int(obj['id'])
                data_val = obj['properties']['85']['value']
            except:
                continue

            value = value_dict[data_id]
            value.value = data_val

    def set_values(self, *value_tuples):
        """Writes values to UHome, accepts tuples of (UponorValue, New Value)"""
        
        _LOGGER.debug("Requested write to %d values", len(value_tuples))

        req = self.create_request("write")

        for tpl in value_tuples:
            obj = {'id': str(tpl[0].id), 'properties': {'85': {'value': str(tpl[1])}}}
            self.add_request_object(req, obj)
        
        self.do_rest_call(req)
        
        # Apply new values, after the API call succeeds
        for tpl in value_tuples:
            tpl[0].value = tpl[1]

class UponorValue(object):
    """Single value in the Uponor API"""

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.value = 0

class UponorBaseDevice(ABC):
    """Base device class"""

    def __init__(self, uponor_client, id_offset, properties, identity_string):
        self.uponor_client = uponor_client
        self.id_offset = id_offset
        self.properties_byname = {}
        self.properties_byid = {}
        self.last_update = None
        self.identity_string = identity_string

        for key_name, key_data in properties.items():
            value = UponorValue(id_offset + key_data['addr'], key_name)
            self.properties_byid[value.id] = value
            self.properties_byname[value.name] = value
    
    def by_id(self, id):
        return self.properties_byid[id]

    def by_name(self, name):
        return self.properties_byname[name]

    def update(self):
        _LOGGER.debug("Updating %s, device '%s'", self.__class__.__name__, self.identity_string)

        self.uponor_client.update_devices(self)

    @abstractmethod
    @property
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
        # A Thermostat is valid if its current temperature is <100C*
        return self.by_name('room_temperature').value < 100

    def set_name(self, name):
        """Updates the thermostats room name to a new value"""
        self.uponor_client.set_values((self.by_name('room_name'), name))

    def set_setpoint(self, temperature):
        """Updates the thermostats setpoint to a new value"""
        self.uponor_client.set_values(
                (self.by_name('setpoint_write_enable'), 0),
                (self.by_name('room_setpoint'), temperature)
            )

    def set_hvac_mode(self, value):
        """Updates the thermostats mode to a new value"""
        self.uponor_client.set_values(
                (self.by_name('setpoint_write_enable'), 0),
                (self.uhome.by_name('hc_mode'), value)
            )
