
Usage
=====

Copy content of custom_components directory in your HA custom_components directory and change configuration.yaml:

    climate:
    - platform: uhomeuponor
      prefix: [your prefix name]        [prefix name for climate and sensor components, is optional tag]
      host: 192.168.x.x
  
    sensor:
    - platform: uhomeuponor
      prefix: [your prefix name]        [prefix name for climate and sensor components, is optional tag]
      host: 192.168.x.x
  
Currently module create one sensor and one climate for each thermostat. 
