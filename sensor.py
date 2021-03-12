"""Support for reading data from a serial port."""
import asyncio
import json
import logging

from serial import SerialException
import serial_asyncio
import voluptuous as vol


from homeassistant.const import CONF_NAME, CONF_VALUE_TEMPLATE, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, RCSLINK_SENSOR
from .exceptions import RCSLinkGatewayException

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensors."""
    sensor = RCSLinkDataSensor()
    hass.data[DOMAIN][RCSLINK_SENSOR] = sensor
    async_add_entities([sensor], True)


class RCSLinkDataSensor(Entity):
    """Representation of a RCSLink sensor."""
     
    def __init__(self):
        """Initialization"""
        self._gateway = None
        self._name = 'RCSLinkDataSensor'
        self._attributes = None
        self._state = None

    def notify(self, line):
        try:
            data = json.loads(line)
        except ValueError:
            pass
        else:
            if isinstance(data, dict):
                self._attributes = data
            self._state = line
            self.async_write_ha_state()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def device_state_attributes(self):
        """Return the attributes of the entity (if any JSON present)."""
        return self._attributes

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
