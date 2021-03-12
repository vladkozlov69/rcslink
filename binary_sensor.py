"""Platform for sensor integration."""

from homeassistant.helpers.entity import Entity
from datetime import timedelta
import logging

from random import randrange

from .const import DOMAIN, RCSLINK_GATEWAY

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
    BinarySensorEntity,
)

_LOGGER = logging.getLogger(__name__)

SENSOR_ENABLED_STATUS = 'on'
SENSOR_NAME = 'RCSLink Port'
SENSOR_STATUS = 'RCSLink status'
SENSOR_ID = 'rcslink.status'


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    add_entities([RCSLinkSensor(hass)])


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensors."""
    async_add_entities([RCSLinkSensor(hass)])


class RCSLinkSensor(BinarySensorEntity):
    """Representation of a Sensor."""
    _port_status = 'none'
    _hass = None

    def __init__(self, hass):
        """Initialize the sensor."""
        self._state = None
        self._hass = hass

    def get_gateway(self):
        """Returns the gateway instance from hass scope"""
        return self._hass.data[DOMAIN][RCSLINK_GATEWAY]   

    @property
    def name(self):
        """Return the name of the sensor."""
        return SENSOR_NAME

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return SENSOR_ENABLED_STATUS == self._port_status

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_CONNECTIVITY

    @property
    def unique_id(self):
        """Return a unique ID."""
        return "SENSOR_ID"

    @property
    def device_state_attributes(self):
        """Return device specific state attributes.
        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        return {SENSOR_STATUS: self._port_status}

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        gateway = self.get_gateway()
        if(gateway is not None):
            self._port_status = gateway.get_port_state()
