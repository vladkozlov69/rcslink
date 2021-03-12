"""Support for RCSLink services."""
import logging

import homeassistant.helpers.config_validation as cv

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
