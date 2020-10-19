"""Constants."""
# HC_MODEs
UHOME_MODE_HEAT = '0'
UHOME_MODE_COOL = '1'

# PRESET_MODEs
UHOME_MODE_ECO = "1"
UHOME_MODE_COMFORT = "0"

# Units
UNIT_BATTERY = '%'
UNIT_HUMIDITY = '%'

# U@Home
# Offset: 0
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

# Controllers
# Offset: 60 + 500 x c
UHOME_CONTROLLER_KEYS = {
    'output_module':                   {'addr': 0, 'value': 0},
    'rh_deadzone':                     {'addr': 1, 'value': 0},
    'controller_sv_version':           {'addr': 2, 'value': 0},
    'thermostat_presence':             {'addr': 3, 'value': 0},
    'supply_high_alarm':               {'addr': 4, 'value': 0},
    'supply_low_alarm':                {'addr': 5, 'value': 0},
    'average_room_temperature_NO':     {'addr': 6, 'value': 0},
    'measured_outdoor_temperature':    {'addr': 7, 'value': 0},
    'supply_temp':                     {'addr': 8, 'value': 0},
    'dehumidifier_status':             {'addr': 9, 'value': 0},
    'outdoor_sensor_presence':         {'addr': 10, 'value': 0},
}

# Thermostats
# Offset: 80 + 500 x c + 40 x t
UHOME_THERMOSTAT_KEYS = {
    'eco_profile_active_cf':           {'addr': 0, 'value': 0},
    'dehumidifier_control_activation': {'addr': 1, 'value': 0},
    'rh_control_activation':           {'addr': 2, 'value': 0},
    'eco_profile_number':              {'addr': 3, 'value': 0},
    'setpoint_write_enable':           {'addr': 4, 'value': 0},
    'cooling_allowed':                 {'addr': 5, 'value': 0},
    'rh_setpoint':                     {'addr': 6, 'value': 0},
    'min_setpoint':                    {'addr': 7, 'value': 0},
    'max_setpoint':                    {'addr': 8, 'value': 0},
    'min_floor_temp':                  {'addr': 9, 'value': 0},
    'max_floor_temp':                  {'addr': 10, 'value': 0},
    'room_setpoint':                   {'addr': 11, 'value': 0},
    'eco_offset':                      {'addr': 12, 'value': 0},
    'eco_profile_active':              {'addr': 13, 'value': 0},
    'home_away_mode_status':           {'addr': 14, 'value': 0},
    'room_in_demand':                  {'addr': 15, 'value': 0},
    'rh_limit_reached':                {'addr': 16, 'value': 0},
    'floor_limit_status':              {'addr': 17, 'value': 0},
    'technical_alarm':                 {'addr': 18, 'value': 0},
    'tamper_indication':               {'addr': 19, 'value': 0},
    'rf_alarm':                        {'addr': 20, 'value': 0},
    'battery_alarm':                   {'addr': 21, 'value': 0},
    'rh_sensor':                       {'addr': 22, 'value': 0},
    'thermostat_type':                 {'addr': 23, 'value': 0},
    'regulation_mode':                 {'addr': 24, 'value': 0},
    'room_temperature':                {'addr': 25, 'value': 0},
    'room_temperature_ext':            {'addr': 26, 'value': 0},
    'rh_value':                        {'addr': 27, 'value': 0},
    'ch_linked_to_th':                 {'addr': 28, 'value': 0},
    'room_name':                       {'addr': 29, 'value': 0},
    'utilization_factor_24h':          {'addr': 30, 'value': 0},
    'utilization_factor_7d':           {'addr': 31, 'value': 0},
    'reg_mode':                        {'addr': 32, 'value': 0},
    'channel_average':                 {'addr': 33, 'value': 0},
    'radiator_heating':                {'addr': 34, 'value': 0}
}
