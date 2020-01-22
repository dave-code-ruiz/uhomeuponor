"""UHome Uponor Smatrix sensor and climate integration."""
import logging
import requests
import json

_LOGGER = logging.getLogger(__name__)

UHOME_MODULE_KEYS = {
    'module_id':                       {'addr': 20, 'value': 0},
    'cooling_available':               {'addr': 21, 'value': 0},
    'holiday_mode':                    {'addr': 22, 'value': 0},
    'forced_eco_mode':                 {'addr': 23, 'value': 0},
    'hc_mode':                         {'addr': 24, 'value': 0},
    'hc_masterslave':                  {'addr': 25, 'value': 0},
    'ts_sv_version':                   {'addr': 26, 'value': 0},
    'holiday_setpoint':                {'addr': 27, 'value': 0},
    'average_temp_low':                {'addr': 28, 'value': 0},
    'low_temp_alarm_limit':            {'addr': 29, 'value': 0},
    'low_temp_alarm_hysteresis':       {'addr': 30, 'value': 0},
    'remote_access_alarm':             {'addr': 31, 'value': 0},
    'device_lost_alarm':               {'addr': 32, 'value': 0},
    'no_comm_controller1':             {'addr': 33, 'value': 0},
    'no_comm_controller2':             {'addr': 34, 'value': 0},
    'no_comm_controller3':             {'addr': 35, 'value': 0},
    'no_comm_controller4':             {'addr': 36, 'value': 0},
    'average_room_temperature':        {'addr': 37, 'value': 0},
    'controller_presence':             {'addr': 38, 'value': 0},
    'allow_hc_mode_change':            {'addr': 39, 'value': 0},
    'hc_master_type':                  {'addr': 40, 'value': 0},
}


class Uhome(object):
    """
    Class Uhome used to represent a U@home R-167 unit.
    Attributes
    ----------
    uhome_module_keys : dict
        A dictionary with all of the module keys, with address and value.
    uhome_controllers : list of UhomeController
        A list of discovered controllers. List items are UhomeController objects.
    uhome_thermostats : list of UhomeThermostat
        A list of discovered thermostats. List items are UhomeThermostat objects.
    ip : str
        The ip address of U@home unit.
    """

    def __init__(self, ip):
        self.IP = ip
        self.uhome_module_keys = UHOME_MODULE_KEYS
        self.uhome_controllers = []
        self.uhome_thermostats = []
        self.init_controllers()
        self.init_thermostats()

    def update(self):
        """
        Updates all of the keys for module, controllers and thermostats.
        """

        # update module keys
        self.update_keys(self.uhome_module_keys)
        # update controller keys
        for uc in self.uhome_controllers:
            self.update_keys(uc.uhome_controller_keys)
        # update thermostat keys
        for t in self.uhome_thermostats:
            self.update_keys(t.uhome_thermostat_keys)

    def init_thermostats(self):
        """
        Discover registered thermostats connected to the controllers.
        Method loops through 12 possible thermostats per controller and
        assumes that value of key "room_setpoint" is in range between 0 and 50.
        """

        self.uhome_thermostats = []
        data = '{"jsonrpc": "2.0", "id": 8, "method": "read", "params": {"objects": ['
        for uc in self.uhome_controllers:
            # up to 12 thermostats per controller
            for i in range(0, 12):
                # using room_setpoint to determine if thermostat is present
                if i != 0 and uc.index != 0:
                    data = data + ','
                data = data + '{"id": "' + str(UHOME_THERMOSTAT_KEYS['room_setpoint']['addr'] + (500 * uc.index) + (40 * i)) + '", "properties": {"85": {}}}'
        data = data + ']}}'
        response_data = self.do_rest_call(data)
        for uc in self.uhome_controllers:
            for i in range(0, 12):
                try:
                    ix = i+(uc.index*12)
                    rs = response_data['result']['objects'][ix]['properties']['85']['value']
                    if 0 < rs < 50:
                        self.uhome_thermostats.append(UhomeThermostat(uc.index, i))
                except:
                    break
                    pass

    def init_controllers(self):
        """
        Discover registered controllers.
        Method loops through 4 possible controllers and
        assumes that value of key "controller_sv_version" is not "0.00".
        """

        self.uhome_controllers = []
        # up to 4 controllers are supported
        data = '{"jsonrpc": "2.0", "id": 8, "method": "read", "params": {"objects": ['
        for i in range(0, 4):
            # using software version to determine if a controller is present
            if i != 0:
                data = data + ','
            data = data + '{"id": "' + str(UHOME_CONTROLLER_KEYS['controller_sv_version']['addr']+(500 * i)) + '", "properties": {"85": {}}}'
        data = data + ']}}'

        response_data = self.do_rest_call(data)

        for i in range(0, 4):
            try:
                sw = response_data['result']['objects'][i]['properties']['85']['value']
                if sw != '0.00':
                    self.uhome_controllers.append(UhomeController(i))
            except:
                break
                pass


    def set_thermostat_value(self, thermostat, name, value):
        for key_name, key_data in thermostat.uhome_thermostat_keys.items():
            if key_name == name:
                key_data['value'] = value
                data = '{"jsonrpc": "2.0", "id": 9, "method": "write", "params": {"objects": [{"id": "' + \
                    str(key_data['addr']) + '", "properties": {"85": {"value":' + \
                    str(key_data['value']) + ':}}}]}}'
                response_data = self.do_rest_call(data)
                try:
                    _LOGGER.info("value set to " + str(value)  + " via Rest Full Api for key " + str(name) + " and thermostat " + str(thermostat.uhome_thermostat_keys['room_name']['value'])  + ", response: " + str(response_data['result']))
                except KeyError:
                    pass
                except IndexError:
                    pass
                except:
                    break
                    pass

    def set_module_value(self, name, value):
        for key_name, key_data in self.uhome_module_keys.items():
            if key_name == name:
                key_data['value'] = value
                data = '{"jsonrpc": "2.0", "id": 9, "method": "write", "params": {"objects": [{"id": "' + \
                    str(key_data['addr']) + '", "properties": {"85": {"value":' + \
                    str(key_data['value']) + ':}}}]}}'
                response_data = self.do_rest_call(data)
                try:
                    _LOGGER.info("value set to " + str(value)  + " via Rest Full Api for key " + str(name) + ", response: " + str(response_data['result']))
                except KeyError:
                    pass
                except IndexError:
                    pass
                except:
                    break
                    pass

    def do_rest_call(self, data):
        uri = 'http://' + self.IP + '/api'
        response_data = ''
        try:
            response = requests.post(uri, data=data)
            response_data = json.loads(response.text)
        except requests.exceptions.ConnectionError:
            print("Connection to Uhome unit on IP address: " + self.IP + " failed.")

        return response_data

#    def update_keys(self, keys):
#        for ix, (key_name, key_data) in enumerate(keys.items()):
#            data = '{"jsonrpc": "2.0", "id": 8, "method": "read", "params": {"objects": [{"id": "' + \
#                   str(key_data['addr']) + '", "properties": {"85": {}}}]}}'
#            response_data = self.do_rest_call(data)
#            try:
#                _LOGGER.info("data:" + str(ix))
#                key_data['value'] = response_data['result']['objects'][0]['properties']['85']['value']
#            except KeyError:
#                pass
#            except IndexError:
#                pass
#            except:
#                break
#                pass

    def update_keys(self, keys):
        data = '{"jsonrpc": "2.0", "id": 8, "method": "read", "params": {"objects": ['
        for ix, (key_name, key_data) in enumerate(keys.items()):
            if ix != 0:
                data = data + ','
            data = data + '{"id": "' + str(key_data['addr']) + '", "properties": {"85": {}}}'
        data = data + ']}}'
        response_data = self.do_rest_call(data)
#        _LOGGER.info("data:" + str(data) + " response:" + str(response_data))
        for ix, (key_name, key_data) in enumerate(keys.items()):
            try:
                key_data['value'] = response_data['result']['objects'][ix]['properties']['85']['value']
            except KeyError:
                pass
            except IndexError:
                pass
            except:
                break
                pass


UHOME_CONTROLLER_KEYS = {
    'output_module':                   {'addr': 60, 'value': 0},
    'rh_deadzone':                     {'addr': 61, 'value': 0},
    'controller_sv_version':           {'addr': 62, 'value': 0},
    'thermostat_presence':             {'addr': 63, 'value': 0},
    'supply_high_alarm':               {'addr': 64, 'value': 0},
    'supply_low_alarm':                {'addr': 65, 'value': 0},
    'average_room_temperature_NO':     {'addr': 66, 'value': 0},
    'measured_outdoor_temperature':    {'addr': 67, 'value': 0},
    'supply_temp':                     {'addr': 68, 'value': 0},
    'dehumidifier_status':             {'addr': 69, 'value': 0},
    'outdoor_sensor_presence':         {'addr': 70, 'value': 0},
}


class UhomeController(object):
    """
    Class UhomeController used to represent a controller registered in U@home R-167 unit.
    This is typically a Uponor X-165 unit.
    Attributes
    ----------
    uhome_controller_keys : dict
        A dictionary with all of the controller keys, with address and value.
    index : int
        An index of the controller (0-3)
    """

    def __init__(self, index):
        self.uhome_controller_keys = {}
        self.index = index
        for key_name, key_data in UHOME_CONTROLLER_KEYS.items():
            # address in calculated with following: addr + (500 x controller_index)
            self.uhome_controller_keys[key_name] = {'addr': (key_data['addr'] + (500 * index)), 'value': 0}


UHOME_THERMOSTAT_KEYS = {
    'eco_profile_active_cf':           {'addr': 80, 'value': 0},
    'dehumidifier_control_activation': {'addr': 81, 'value': 0},
    'rh_control_activation':           {'addr': 82, 'value': 0},
    'eco_profile_number':              {'addr': 83, 'value': 0},
    'setpoint_write_enable':           {'addr': 84, 'value': 0},
    'cooling_allowed':                 {'addr': 85, 'value': 0},
    'rh_setpoint':                     {'addr': 86, 'value': 0},
    'min_setpoint':                    {'addr': 87, 'value': 0},
    'max_setpoint':                    {'addr': 88, 'value': 0},
    'min_floor_temp':                  {'addr': 89, 'value': 0},
    'max_floor_temp':                  {'addr': 90, 'value': 0},
    'room_setpoint':                   {'addr': 91, 'value': 0},
    'eco_offset':                      {'addr': 92, 'value': 0},
    'eco_profile_active':              {'addr': 93, 'value': 0},
    'home_away_mode_status':           {'addr': 94, 'value': 0},
    'room_in_demand':                  {'addr': 95, 'value': 0},
    'rh_limit_reached':                {'addr': 96, 'value': 0},
    'floor_limit_status':              {'addr': 97, 'value': 0},
    'technical_alarm':                 {'addr': 98, 'value': 0},
    'tamper_indication':               {'addr': 99, 'value': 0},
    'rf_alarm':                        {'addr': 100, 'value': 0},
    'battery_alarm':                   {'addr': 101, 'value': 0},
    'rh_sensor':                       {'addr': 102, 'value': 0},
    'thermostat_type':                 {'addr': 103, 'value': 0},
    'regulation_mode':                 {'addr': 104, 'value': 0},
    'room_temperature':                {'addr': 105, 'value': 0},
    'room_temperature_ext':            {'addr': 106, 'value': 0},
    'rh_value':                        {'addr': 107, 'value': 0},
    'ch_linked_to_th':                 {'addr': 108, 'value': 0},
    'room_name':                       {'addr': 109, 'value': 0},
    'utilization_factor_24h':          {'addr': 110, 'value': 0},
    'utilization_factor_7d':           {'addr': 111, 'value': 0},
    'reg_mode':                        {'addr': 112, 'value': 0},
    'channel_average':                 {'addr': 113, 'value': 0},
    'radiator_heating':                {'addr': 114, 'value': 0}
}


class UhomeThermostat(object):
    """
    Class UhomeThermostat used to represent a thermostat registered to a controller.
    This is typically a Uponor T-169 unit.
    Attributes
    ----------
    uhome_thermostat_keys : dict
        A dictionary with all of the thermostat keys, with address and value.
    uc_index : int
        Index of the controller the thermostat is registered to.
    index : int
        Index of the thermostat (0-11)
    """

    def __init__(self, uc_index, index):
        self.uhome_thermostat_keys = {}
        self.uc_index = uc_index
        self.index = index
        self.identity = "controller" + str(uc_index) + "_thermostat" + str(index)
        for key_name, key_data in UHOME_THERMOSTAT_KEYS.items():
            # address in calculated with following: addr + (500 x controller_index) + (40 x thermostat_index)
            self.uhome_thermostat_keys[key_name] = {'addr': (key_data['addr'] + (500 * uc_index) + (40 * index)), 'value': 0}

