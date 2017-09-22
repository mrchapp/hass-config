"""
Support for Cuby HVAC controllers.

For more details about this component, please refer to the product site at
https://cuby.mx/
"""
import logging
from datetime import timedelta

import requests
import voluptuous as vol

from homeassistant.const import CONF_USERNAME
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers import discovery
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv

import json

_LOGGER = logging.getLogger(__name__)

CUBY = None
CUBY_TYPE = ['sensor']

DOMAIN = 'cuby'

# There is an API access limit set at 1 request per minute; more than that
# gets the IP flagged and may get it banned.
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
    }),
}, extra=vol.ALLOW_EXTRA)

# pylint: disable=unused-argument
def setup(hass, config):
    """Set up the Cuby component."""
    user_id = config[DOMAIN][CONF_USERNAME]
    api_key = config[DOMAIN][CONF_API_KEY]

    global CUBY
    try:
        _LOGGER.debug("Trying to init with " + user_id + " and " + api_key)
        CUBY = Cuby(user_id, api_key)
    except RuntimeError:
        return False

    for component in CUBY_TYPE:
        discovery.load_platform(hass, component, DOMAIN, {}, config)

    return True


class Cuby(object):
    """Handle all communication with the Cuby API."""

    # API documentation at http://weatherlution.com/bloomsky-api/
    API_URL_BASE = 'https://cuby.io/api/v1/users/cuby/'

    def __init__(self, user_id, api_key):
        """Initialize the Cuby."""
        self._user_id = user_id
        self._api_key = api_key
        self.devices = {}
        _LOGGER.debug("Initial Cuby device load...")
        self.refresh_devices()

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def refresh_devices(self):
        """Use the API to retrieve a list of devices."""
        API_URL = self.API_URL_BASE + "data?username=" + self._user_id + "&token=" + self._api_key
        _LOGGER.critical("Fetching Cuby update from URL " + API_URL)
        response = requests.get(
            API_URL, headers={"Authorization": self._api_key}, timeout=10)
        if response.status_code == 401:
            raise RuntimeError("Invalid API_KEY")
        elif response.status_code != 200:
            _LOGGER.error("Invalid HTTP response: %s", response.status_code)
            return
        # Create dictionary keyed off of the device unique id
        response_json = response.json()
        #_LOGGER.debug("Response: " + json.dumps(response_json))
        data = json.loads(response_json['data'])
        _LOGGER.debug("Data: " + json.dumps(data))
        self.devices.update({
            device['id']: device for device in data
        })
