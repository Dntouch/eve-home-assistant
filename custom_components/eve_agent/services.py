"""Structured events from explicit Home Assistant automation calls."""
import uuid

import voluptuous as vol

from homeassistant.core import SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv, service

from .api import EveError
from .const import DOMAIN


def _identifier(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise vol.Invalid("Expected a nonempty string of at most 128 characters")
    return value


SEND_EVENT_SCHEMA = vol.Schema({
    vol.Required("config_entry_id"): cv.string,
    vol.Required("event_type"): _identifier,
    vol.Optional("data", default=dict): dict,
    vol.Optional("event_id"): _identifier,
})


def async_register_services(hass):
    async def send_event(call):
        entry = service.async_get_config_entry(hass, DOMAIN, call.data["config_entry_id"])
        runtime = entry.runtime_data
        if runtime.info.get("events") is not True:
            raise ServiceValidationError(
                "Der EVE-Server unterstützt keine Ereignisse. EVE aktualisieren und die Integration neu laden.")
        try:
            result = await runtime.client.send_event(
                call.data["event_type"], call.data["data"],
                call.data.get("event_id") or str(uuid.uuid4()),
            )
        except EveError as exc:
            raise HomeAssistantError(str(exc)) from exc
        return result if call.return_response else None

    hass.services.async_register(
        DOMAIN, "send_event", send_event, schema=SEND_EVENT_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
