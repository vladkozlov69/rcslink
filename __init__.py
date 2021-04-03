"""The RCSLink component."""

import logging

import voluptuous as vol

from homeassistant.core import callback

from homeassistant.config_entries import SOURCE_IMPORT

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import EVENT_HOMEASSISTANT_STOP

from .const import DOMAIN, RCSLINK_GATEWAY, CONF_SERIAL_PORT, CONF_BAUDRATE
from .const import ATTR_CODE

from .gateway import create_rcslink_gateway
from .sender import get_rcslink_service
from .sensor import get_rcslink_sensor

RCS_SEND_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CODE): cv.string
    }
)

RCS_EMPTY_SERVICE_SCHEMA = vol.Schema({})

PLATFORM_SCHEMA = [].extend(
    {
        vol.Required(CONF_SERIAL_PORT): cv.string,
        vol.Optional(CONF_BAUDRATE): cv.positive_int,
    }
)


_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


async def async_setup(hass, config):
    """Set up the Freebox integration."""
    if DOMAIN in config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT},
                data=config[DOMAIN]
            )
        )

    return True


async def async_setup_entry(hass, config_entry):
    """Set up the RCS Link component."""

    @callback
    async def handle_send_code(call):
        """Handle the sending service call."""
        code = call.data.get(ATTR_CODE)
        svc = get_rcslink_service(hass)
        await svc.send(code)

    @callback
    async def handle_register_code(call):
        """Handle the register service call."""
        code = call.data.get(ATTR_CODE)
        svc = get_rcslink_service(hass)
        await svc.register(code)

    @callback
    async def handle_remove_code(call):
        """Handle the forget service call."""
        code = call.data.get(ATTR_CODE)
        svc = get_rcslink_service(hass)
        await svc.forget(code)

    @callback
    async def handle_dump_codes(call):
        """Handle the dump service call."""
        svc = get_rcslink_service(hass)
        await svc.dump()

    @callback
    async def handle_learn_codes(call):
        """Handle the learn service call."""
        svc = get_rcslink_service(hass)
        await svc.learn()

    @callback
    async def handle_debug(call):
        """Handle the learn service call."""
        svc = get_rcslink_service(hass)
        await svc.debug()

    @callback
    async def handle_clear(call):
        sensor = get_rcslink_sensor(hass)
        await sensor.clear()

    hass.data.setdefault(DOMAIN, {})

    _LOGGER.debug("Before create_rcslink_gateway")

    gateway = create_rcslink_gateway(config_entry, hass)

    _LOGGER.debug("After create_rcslink_gateway")

    if not gateway:
        return False

    hass.data[DOMAIN][RCSLINK_GATEWAY] = gateway

    hass.services.async_register(DOMAIN, 'send', handle_send_code,
                                 schema=RCS_SEND_SERVICE_SCHEMA)

    hass.services.async_register(DOMAIN, 'register', handle_register_code,
                                 schema=RCS_SEND_SERVICE_SCHEMA)

    hass.services.async_register(DOMAIN, 'forget', handle_remove_code,
                                 schema=RCS_SEND_SERVICE_SCHEMA)

    hass.services.async_register(DOMAIN, 'list', handle_dump_codes,
                                 schema=RCS_EMPTY_SERVICE_SCHEMA)

    hass.services.async_register(DOMAIN, 'learn', handle_learn_codes,
                                 schema=RCS_EMPTY_SERVICE_SCHEMA)

    hass.services.async_register(DOMAIN, 'debug', handle_debug,
                                 schema=RCS_EMPTY_SERVICE_SCHEMA)

    hass.services.async_register(DOMAIN, 'clear', handle_clear,
                                 schema=RCS_EMPTY_SERVICE_SCHEMA)

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry,
                                                      "binary_sensor")
    )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
    )

    await gateway.async_added_to_hass()

    get_rcslink_service(hass)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP,
                               gateway.stop_serial_read)

    return True
