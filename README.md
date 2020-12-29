# Uhome Uponor integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Uhome Uponor is a python custom_component for connect Home Assistant with Uponor Smatrix Wave PLUS Smart Home Gateway, R-167 aka U@home. The module uses units REST API for discovery of controllers and thermostats.

# Installation

## Using HACS

Add this custom repository to your HACS Community store, as an `Integration`:

> dave-code-ruiz/uhomeuponor

Then find the `Uhome Uponor` integration and install it.

## Manual

Copy content of `custom_components` directory in this repository, into your HA `custom_components` directory.

# Configuration

Change your `configuration.yaml`, and add `climate` and/or `sensor` platforms.

```yaml
climate:
- platform: uhomeuponor
  host: 192.168.x.x
  prefix: [your prefix name]  # Optional, prefix name for climate entities
  supports_heating: True      # Optional, set to False to exclude Heating as an HVAC Mode
  supports_cooling: True      # Optional, set to False to exclude Cooling as an HVAC Mode

sensor:
- platform: uhomeuponor
  host: 192.168.x.x
  prefix: [your prefix name]  # Optional, prefix name for climate entities
```

Currently this module creates the following entities, for each thermostat:

* Climate:
  * A `climate` control entity
* Sensor:
  * A `temperature` sensor
  * A `humidity` sensor
  * A `battery` sensor

## Contributions

Thanks to @almirdelkic for API code.

# New module X-265 / R-208

For new module Uponor X-265 / R-208 visit:

https://github.com/asev/homeassistant-uponor/

# Hardware compatibility list

The module has been tested with following hardware:

* X-165 (controller)
* M-160 (slave module)
* I-167 (panel)
* R-167 (U@home module)
* T-169 (thermostat)

If you test it with other units, please let me know or even better update the list above.

Donate
=============
[![paypal](https://www.paypalobjects.com/en_US/ES/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=5U5L9S4SP79FJ&item_name=Create+more+code+and+components+in+github+and+Home+Assistant&currency_code=EUR&source=url)


<a href="https://www.buymeacoffee.com/davecoderuiz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
