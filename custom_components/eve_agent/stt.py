import logging
from homeassistant.components import stt

from .api import EveError

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([EveSTT(entry)])


class EveSTT(stt.SpeechToTextEntity):
    _attr_name = "EVE STT"
    _attr_has_entity_name = True

    def __init__(self, entry):
        self.runtime = entry.runtime_data
        self._attr_unique_id = entry.entry_id + "_stt"

    @property
    def supported_languages(self):
        return self.runtime.info["stt"]["languages"]

    @property
    def supported_formats(self):
        return [stt.AudioFormats.WAV]

    @property
    def supported_codecs(self):
        return [stt.AudioCodecs.PCM]

    @property
    def supported_bit_rates(self):
        return [stt.AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self):
        return [stt.AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self):
        return [stt.AudioChannels.CHANNEL_MONO]

    async def async_process_audio_stream(self, metadata, stream):
        try:
            text = await self.runtime.client.transcribe(stream, metadata.language)
        except EveError as exc:
            _LOGGER.error("EVE STT: %s", exc)
            return stt.SpeechResult(None, stt.SpeechResultState.ERROR)
        return stt.SpeechResult(text, stt.SpeechResultState.SUCCESS)
