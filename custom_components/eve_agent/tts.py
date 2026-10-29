"""EVE speech synthesis and the tts.eve_say compatibility action."""

import probatio

from homeassistant.components import tts
from homeassistant.components.tts.const import DATA_COMPONENT
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv, service

from .api import EveError
from .const import DOMAIN

SERVICE_SAY = "eve_say"
SAY_SCHEMA = probatio.Schema({
    probatio.Required("entity_id"): probatio.All(cv.entities_domain("media_player"), probatio.Length(min=1)),
    probatio.Required("message"): cv.string,
    probatio.Optional("tts_entity_id"): cv.entity_domain("tts"),
    probatio.Optional("cache", default=False): cv.boolean,
    probatio.Optional("language"): cv.string,
    probatio.Optional("options"): dict,
})


@callback
def _async_register_say_service(hass):
    if hass.services.has_service("tts", SERVICE_SAY):
        return

    async def say(call):
        component = hass.data.get(DATA_COMPONENT)
        entities = (
            [entity for entity in component.entities if isinstance(entity, EveTTS)]
            if component else []
        )
        if entity_id := call.data.get("tts_entity_id"):
            entity = next((entity for entity in entities if entity.entity_id == entity_id), None)
            if entity is None:
                raise ServiceValidationError("Die gewählte EVE-TTS-Entität ist nicht geladen.")
        else:
            if not entities:
                raise ServiceValidationError("Keine EVE-TTS-Entität geladen. EVE-Integration prüfen.")
            if len(entities) != 1:
                raise ServiceValidationError("Mehrere EVE-TTS-Entitäten geladen. tts_entity_id angeben.")
            entity = entities[0]
        if not entity.available:
            raise ServiceValidationError("Die gewählte EVE-TTS-Entität ist nicht verfügbar.")

        data = {
            key: call.data[key]
            for key in ("message", "cache", "language", "options") if key in call.data
        }
        data["media_player_entity_id"] = call.data["entity_id"]
        await hass.services.async_call(
            "tts", "speak", data, target={"entity_id": entity.entity_id},
            blocking=True, context=call.context,
        )

    hass.services.async_register("tts", SERVICE_SAY, say, schema=SAY_SCHEMA)
    # The action belongs to the TTS domain, so HA cannot load its description
    # from eve_agent/services.yaml. Register it like HA's legacy say actions.
    service.async_set_service_schema(hass, "tts", SERVICE_SAY, {
        "name": "Say a TTS message with EVE",
        "description": "Speak a message on a media player using EVE.",
        "fields": {
            "entity_id": {
                "name": "Media player", "required": True,
                "selector": {"entity": {"domain": "media_player", "multiple": True}},
            },
            "message": {"name": "Message", "required": True, "selector": {"text": {}}},
            "tts_entity_id": {
                "name": "EVE TTS entity",
                "description": "Required when multiple EVE TTS entities are loaded.",
                "selector": {"entity": {"domain": "tts", "integration": DOMAIN}},
            },
            "cache": {"name": "Cache", "default": False, "selector": {"boolean": {}}},
            "language": {"name": "Language", "selector": {"text": {}}},
            "options": {"name": "Options", "selector": {"object": {}}},
        },
    })


async def async_setup_entry(hass, entry, async_add_entities):
    _async_register_say_service(hass)
    async_add_entities([EveTTS(entry)])


class EveTTS(tts.TextToSpeechEntity):
    _attr_name = "EVE TTS"
    _attr_has_entity_name = True

    def __init__(self, entry):
        self.runtime = entry.runtime_data
        self._attr_unique_id = entry.entry_id + "_tts"
        self._attr_supported_languages = self.runtime.info["tts"]["languages"]
        self._attr_default_language = self._attr_supported_languages[0]

    async def async_get_tts_audio(self, message, language, options):
        try:
            audio = await self.runtime.client.synthesize(message, language)
        except EveError as exc:
            raise HomeAssistantError(str(exc)) from exc
        return "wav", audio
