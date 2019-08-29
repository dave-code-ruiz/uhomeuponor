# Uhome Uponor

Uhome Uponor is a python custom_component for connect Home Assistant with Uponor Smatrix Wave PLUS Smart Home Gateway, R-167 aka U@home. The module uses units REST API for discovery of controllers and thermostats.

Usage
=====

Copy content of custom_components directory in your HA custom_components directory and change configuration.yaml:

    sensor:
    - platform: uhomeuponor
      prefix: [your prefix name]        [prefix name for climate and sensor components, is optional tag]
      host: 192.168.x.x
  
Currently module create one sensor and one climate for each thermostat. 

Adding support for setting modes and preset values is on TODO list.

Thanks to @almirdelkic for API code:

List of keys
============

**MODULE KEYS**

Located in ``uhome_module_keys`` dict of your Uhome object.

* module_id
* cooling_available
* holiday_mode
* forced_eco_mode //Home/Away
* hc_mode
* hc_masterslave
* ts_sv_version
* holiday_setpoint  //Note that the setpoint for the rooms doesn’t change when holiday mode is enabled.
* average_temp_low		//No value?
* low_temp_alarm_limit
* low_temp_alarm_hysteresis
* remote_access_alarm		//No value?
* device_lost_alarm		//No value?
* no_comm_controller1
* no_comm_controller2
* no_comm_controller3
* no_comm_controller4
* average_room_temperature
* controller_presence
* allow_hc_mode_change
* hc_master_type

**CONTROLLER KEYS**

Located in ``uhome_controller_keys`` dict of your UhomeController objects.

* output_module
* rh_deadzone
* controller_sv_version
* thermostat_presence
* supply_high_alarm
* supply_low_alarm
* average_room_temperature_NO
* measured_outdoor_temperature
* supply_temp
* dehumidifier_status
* outdoor_sensor_presence

**THERMOSTAT KEYS**

Located in ``uhome_thermostat_keys`` dict of your UhomeThermostat objects.

* eco_profile_active_cf //Read only? Seem to be set by home/Away.
* dehumidifier_control_activation
* rh_control_activation
* eco_profile_number
* setpoint_write_enable //Use room thermostat (0) or app (1)
* cooling_allowed // Is an OFF or BLOCK mode
* rh_setpoint
* min_setpoint //Min value on thermostat
* max_setpoint //Max value on thermostat
* min_floor_temp
* max_floor_temp
* room_setpoint //Desired temperature in room
* eco_offset
* eco_profile_active //Read only? Seem to be set by home/Away.
* home_away_mode_status //Read only? I can’t get this to change at all…
* room_in_demand // (0) Off (1) Working
* rh_limit_reached
* floor_limit_status
* technical_alarm
* tamper_indication
* rf_alarm
* battery_alarm
* rh_sensor
* thermostat_type
* regulation_mode
* room_temperature //Actual temperature
* room_temperature_ext
* rh_value
* ch_linked_to_th
* room_name // This could be usefull…
* utilization_factor_24h
* utilization_factor_7d
* reg_mode
* channel_average
* radiator_heating

Hardware compatibility list
===========================

The module has been testet with following hardware:

* X-165 (controller)
* M-160 (slave module)
* I-167 (panel)
* R-167 (U@home module)
* T-169 (thermostat)

If you test it with other units, please let me know or even better update the list above.

Documentation
=============

https://github.com/almirdelkic/uhome/blob/master/docs/index.txt
