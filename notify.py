"""Support for RCSLink services."""
import logging

from .const import DOMAIN, RCSLINK_GATEWAY, RCSLINK_SENDER
from .exceptions import RCSLinkGatewayException

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.storage import Store
from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)

CODE_STORAGE_VERSION = 1
CODE_SAVE_DELAY = 1


def get_rcslink_service(hass):
    """Get the RCSLink service."""

    if RCSLINK_GATEWAY not in hass.data[DOMAIN]:
        _LOGGER.error("RCSLink gateway not found, cannot initialize service")
        raise RCSLinkGatewayException("RCSLink gateway not found")

    gateway = hass.data[DOMAIN][RCSLINK_GATEWAY]

    if RCSLINK_SENDER not in hass.data[DOMAIN]:
        service = RCSLinkService(
            gateway,
            Store(hass, CODE_STORAGE_VERSION, 'rcslink_codes'))
        hass.data[DOMAIN][RCSLINK_SENDER] = service

    return hass.data[DOMAIN][RCSLINK_SENDER]


class RCSLinkService(Entity):
    """Implement the sender service for RCSLink."""

    def __init__(self, gateway, codes):
        """Initialize the service."""
        self._gateway = gateway
        self._code_storage = codes
        self._codes = set()
        # hass.data[DOMAIN]['sender'] = self

    async def async_added_to_hass(self):
        _LOGGER.info('async_added_to_hass')
        self._codes.update(await self._code_storage.async_load() or set())
        await self.refresh_codes()

    async def send(self, code):
        """Send RC code."""
        await self._gateway.send('SEND ' + code)

    async def register(self, code):
        """Send RC code."""
        await self.add_code(code)
        # self._gateway.send('REGISTER ' + code)
        await self.refresh_codes()

    async def add_code(self, code):
        self._codes.update([code])
        self._code_storage.async_delay_save(self.get_codes_list,
                                            CODE_SAVE_DELAY)

    async def refresh_codes(self):
        """Sends all codes to device"""
        for code in self._codes:
            await self._gateway.send('REGISTER ' + code)

    async def forget(self, code):
        """Send RC code."""
        await self._gateway.send('DELETE ' + code)

    async def dump(self):
        """Lists RC codes."""
        await self._gateway.send('LIST')

    async def debug(self):
        """Lists RC codes."""
        await self._gateway.send('DEBUG')

    async def learn(self):
        """Lists RC codes."""
        await self._gateway.send('LEARN')

    @callback
    def get_codes_list(self):
        """Return a dictionary of codes."""
        return list(self._codes)
