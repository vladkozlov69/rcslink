
import logging
import voluptuous as vol

from homeassistant import config_entries, data_entry_flow
from .const import DOMAIN, CONF_SERIAL_PORT

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SERIAL_PORT): str
    }
)

_LOGGER = logging.getLogger(__name__)


class RCSLinkConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """RCSLink config flow."""

    async def async_step_import(self, user_input=None):
        """Import a config entry."""
        if self._async_current_entries():
            for entry in self._async_current_entries(include_ignore=True):
                if user_input is not None:
                    self.hass.config_entries.async_update_entry(
                        entry, data=user_input
                    )
                    raise data_entry_flow.AbortFlow("already_configured")
        else:
            return self.async_create_entry(title="RCSLink Config",
                                           data=user_input)
