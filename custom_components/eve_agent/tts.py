from homeassistant.components import tts
from homeassistant.exceptions import HomeAssistantError

from .api import EveError


async def async_setup_entry(hass, entry, async_add_entities):
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
