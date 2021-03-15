"""Support for RCSLink services."""
import logging

from .const import DOMAIN, RCSLINK_GATEWAY
from .exceptions import RCSLinkGatewayException

_LOGGER = logging.getLogger(__name__)


def get_rcslink_service(hass):
    """Get the RCSLink service."""

    if RCSLINK_GATEWAY not in hass.data[DOMAIN]:
        _LOGGER.error("RCSLink gateway not found, cannot initialize service")
        raise RCSLinkGatewayException("RCSLink gateway not found")

    gateway = hass.data[DOMAIN][RCSLINK_GATEWAY]

    return RCSLinkService(gateway)


class RCSLinkService:
    """Implement the sender service for RCSLink."""

    def __init__(self, gateway):
        """Initialize the service."""
        self.gateway = gateway

    def send(self, code):
        """Send RC code."""
        self.gateway.send(code)

    def register(self, code):
        """Send RC code."""
        self.gateway.send('REGISTER ' + code)

    def forget(self, code):
        """Send RC code."""
        self.gateway.send('DELETE ' + code)

    def dump(self):
        """Lists RC codes."""
        self.gateway.send('LIST')

    def learn(self):
        """Lists RC codes."""
        self.gateway.send('LEARN')
