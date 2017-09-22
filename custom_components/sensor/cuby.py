"""
Support the sensors of a Cuby HVAC controler.

For more details about this component, please refer to the product site at
https://cuby.mx/
"""
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (TEMP_FAHRENHEIT, CONF_MONITORED_CONDITIONS)
from homeassistant.helpers.entity import Entity
from homeassistant.loader import get_component
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['cuby']

# These are the available sensors
SENSOR_TYPES = ['temperature',
                'humidity']

# Sensor units - these do not currently align with the API documentation
SENSOR_UNITS = {'temperature': TEMP_FAHRENHEIT,
                'humidity': '%'}

# Which sensors to format numerically
FORMAT_NUMBERS = ['temperature', 'humidity']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_MONITORED_CONDITIONS, default=SENSOR_TYPES):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})

# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the available Cuby device sensors."""
    cuby = get_component('cuby')
    # Default needed in case of discovery
    sensors = config.get(CONF_MONITORED_CONDITIONS, SENSOR_TYPES)

    for device in cuby.CUBY.devices.values():
        for variable in sensors:
            add_devices(
                [CubySensor(cuby.CUBY, device, variable)], True)

class CubySensor(Entity):
    """Representation of a single sensor in a Cuby device."""

    def __init__(self, c, device, sensor_name):
        """Initialize a Cuby sensor."""
        self._cuby = c
        self._device_id = device['id']
        self._sensor_name = sensor_name
        self._name = '{} {}'.format("CubyDev", sensor_name)
        self._unique_id = 'cuby_sensor {}'.format(self._name)
        self._state = None

    @property
    def name(self):
        """Return the name of the Cuby device and this sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID for this sensor."""
        return self._unique_id

    @property
    def state(self):
        """Return the current state, eg. value, of this sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the sensor units."""
        return SENSOR_UNITS.get(self._sensor_name, None)

    def update(self):
        """Request an update from the Cuby API."""
        _LOGGER.debug("Requesting update from sensor...")
        self._cuby.refresh_devices()

        state = \
            float(self._cuby.devices[self._device_id][self._sensor_name])

        if self._sensor_name in FORMAT_NUMBERS:
            self._state = '{0:.1f}'.format(state)
        else:
            self._state = state
