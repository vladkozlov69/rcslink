"""The RCSLink component."""

import asyncio
import logging
import serial_asyncio

import voluptuous as vol

from homeassistant.core import callback

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import EVENT_HOMEASSISTANT_STOP

from .const import DOMAIN, RCSLINK_GATEWAY, CONF_SERIAL_PORT, CONF_BAUDRATE, CONF_NAME, CONF_BYTESIZE, CONF_PARITY, CONF_STOPBITS, CONF_XONXOFF, CONF_RTSCTS, CONF_DSRDTR, CONF_VALUE_TEMPLATE, ATTR_CODE

from .gateway import create_rcslink_gateway
from .notify import get_rcslink_service

DEFAULT_NAME = "Serial Sensor"
DEFAULT_BAUDRATE = 9600
DEFAULT_BYTESIZE = serial_asyncio.serial.EIGHTBITS
DEFAULT_PARITY = serial_asyncio.serial.PARITY_NONE
DEFAULT_STOPBITS = serial_asyncio.serial.STOPBITS_ONE
DEFAULT_XONXOFF = False
DEFAULT_RTSCTS = False
DEFAULT_DSRDTR = False

RCS_SEND_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CODE): cv.string
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_SERIAL_PORT): cv.string,
        vol.Optional(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): cv.positive_int,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
        vol.Optional(CONF_BYTESIZE, default=DEFAULT_BYTESIZE): vol.In(
            [
                serial_asyncio.serial.FIVEBITS,
                serial_asyncio.serial.SIXBITS,
                serial_asyncio.serial.SEVENBITS,
                serial_asyncio.serial.EIGHTBITS,
            ]
        ),
        vol.Optional(CONF_PARITY, default=DEFAULT_PARITY): vol.In(
            [
                serial_asyncio.serial.PARITY_NONE,
                serial_asyncio.serial.PARITY_EVEN,
                serial_asyncio.serial.PARITY_ODD,
                serial_asyncio.serial.PARITY_MARK,
                serial_asyncio.serial.PARITY_SPACE,
            ]
        ),
        vol.Optional(CONF_STOPBITS, default=DEFAULT_STOPBITS): vol.In(
            [
                serial_asyncio.serial.STOPBITS_ONE,
                serial_asyncio.serial.STOPBITS_ONE_POINT_FIVE,
                serial_asyncio.serial.STOPBITS_TWO,
            ]
        ),
        vol.Optional(CONF_XONXOFF, default=DEFAULT_XONXOFF): cv.boolean,
        vol.Optional(CONF_RTSCTS, default=DEFAULT_RTSCTS): cv.boolean,
        vol.Optional(CONF_DSRDTR, default=DEFAULT_DSRDTR): cv.boolean,
    }
)


_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

@asyncio.coroutine
def async_setup(hass, config):
    """Import integration from config."""
    # if DOMAIN in config:
    #     hass.async_create_task(
    #         hass.config_entries.flow.async_init(
    #             DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
    #         )
    #     )
    return True


async def async_setup_entry(hass, config_entry):
    """Set up the RCS Link component."""

    @callback
    def handle_send_code(call):
        """Handle the sending service call."""
        code = call.data.get(ATTR_CODE)
        get_rcslink_service(hass).send(code)

    hass.data.setdefault(DOMAIN, {})

    _LOGGER.debug("Before create_rcslink_gateway")

    gateway = create_rcslink_gateway(config_entry, hass)

    _LOGGER.debug("After create_rcslink_gateway")

    if not gateway:
        return False

    hass.data[DOMAIN][RCSLINK_GATEWAY] = gateway

    hass.services.async_register(DOMAIN, 'send', handle_send_code,
                                 schema=RCS_SEND_SERVICE_SCHEMA)

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "binary_sensor")
    )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
    )

    await gateway.async_added_to_hass()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, gateway.stop_serial_read)

    return True
