"""Exercise eve_say through Home Assistant's real TTS and service machinery."""

import io
import logging
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock
import wave

from homeassistant.components import tts
from homeassistant.components.tts.const import DATA_COMPONENT, DATA_TTS_MANAGER
from homeassistant.components.tts.services import async_setup_services
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry, entity_registry, selector, service
from homeassistant.helpers.entity_component import EntityComponent
import probatio

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from custom_components.eve_agent.tts import async_setup_entry
from custom_components.eve_agent.api import EveError


class TTSActionTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.hass = HomeAssistant(self.temp.name)
        device_registry.async_setup(self.hass)
        await device_registry.async_load(self.hass, load_empty=True)
        await entity_registry.async_load(self.hass, load_empty=True)
        self.component = EntityComponent(logging.getLogger(__name__), "tts", self.hass)
        self.component.register_shutdown()
        self.hass.data[DATA_COMPONENT] = self.component
        self.hass.data[DATA_TTS_MANAGER] = tts.SpeechManager(self.hass, False, self.temp.name, 60)
        async_setup_services(self.hass)
        output = io.BytesIO()
        with wave.open(output, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(16000)
            audio.writeframes(b"\x00\x00" * 100)
        self.client = SimpleNamespace(synthesize=AsyncMock(return_value=output.getvalue()), converse=AsyncMock())
        self.entity = await self.add_entry("first")
        self.playbacks = []

        async def play(call):
            self.playbacks.append(call)

        self.hass.services.async_register("media_player", "play_media", play)

    async def asyncTearDown(self):
        self.client.converse.assert_not_awaited()
        await self.hass.async_stop(force=True)
        self.temp.cleanup()

    async def add_entry(self, entry_id):
        entry = SimpleNamespace(entry_id=entry_id, runtime_data=SimpleNamespace(
            info={"tts": {"languages": ["de"]}}, client=self.client))
        entities = []
        await async_setup_entry(self.hass, entry, entities.extend)
        await self.component.async_add_entities(entities)
        self.assertIs(self.component.get_entity(entities[0].entity_id), entities[0])
        return entities[0]

    async def say(self, **data):
        await self.hass.services.async_call("tts", "eve_say", data, blocking=True)

    async def test_say_synthesizes_unchanged_text_via_real_tts_speak(self):
        from homeassistant.components.tts.media_source import parse_media_source_id

        context = Context()
        message = "  Hallo\nSonos!  "
        await self.hass.services.async_call("tts", "eve_say", {
            "entity_id": "media_player.sonos", "message": message,
            "options": {"preferred_format": "wav"}}, blocking=True, context=context)
        self.assertEqual(len(self.playbacks), 1)
        playback = self.playbacks[0]
        self.assertIs(playback.context, context)
        self.assertEqual(playback.data["entity_id"], ["media_player.sonos"])
        self.assertTrue(playback.data["announce"])
        parsed = parse_media_source_id(playback.data["media_content_id"])
        self.assertFalse(parsed["options"]["use_file_cache"])
        extension, audio = await tts.async_get_media_source_audio(self.hass, playback.data["media_content_id"])
        self.assertEqual(extension, "wav")
        with wave.open(io.BytesIO(audio)) as wav:
            self.assertEqual(wav.getnframes(), 100)
        self.client.synthesize.assert_awaited_once_with(message, "de")

    async def test_say_preserves_player_list_language_cache_and_options(self):
        from homeassistant.components.tts.media_source import parse_media_source_id

        players = ["media_player.kitchen", "media_player.living_room"]
        options = {"preferred_format": "mp3"}
        await self.say(entity_id=players, message="Hallo", cache=True, language="de", options=options)
        self.assertEqual(self.playbacks[0].data["entity_id"], players)
        parsed = parse_media_source_id(self.playbacks[0].data["media_content_id"])
        self.assertEqual(parsed["options"], {
            "engine": self.entity.entity_id, "language": "de", "use_file_cache": True, "options": options})

    async def test_multiple_entries_require_explicit_eve_entity(self):
        other = await self.add_entry("second")
        with self.assertRaisesRegex(ServiceValidationError, "tts_entity_id"):
            await self.say(entity_id="media_player.sonos", message="Hallo")
        self.assertEqual(self.playbacks, [])
        await self.say(entity_id="media_player.sonos", message="Hallo", tts_entity_id=other.entity_id)
        self.assertIn(other.entity_id, self.playbacks[0].data["media_content_id"])

    async def test_say_resolves_renamed_entity_and_reloaded_entries(self):
        registry = entity_registry.async_get(self.hass)
        registry.async_update_entity(self.entity.entity_id, new_entity_id="tts.renamed_eve")
        await self.hass.async_block_till_done()
        await self.say(entity_id="media_player.sonos", message="Hallo")
        self.assertIn("tts.renamed_eve", self.playbacks[-1].data["media_content_id"])
        await self.component.async_remove_entity("tts.renamed_eve")
        with self.assertRaisesRegex(ServiceValidationError, "Keine EVE"):
            await self.say(entity_id="media_player.sonos", message="Hallo")
        self.assertEqual(len(self.playbacks), 1)
        await self.add_entry("first")
        await self.say(entity_id="media_player.sonos", message="Hallo")
        self.assertEqual(len(self.playbacks), 2)
        self.assertIn("tts.renamed_eve", self.playbacks[-1].data["media_content_id"])

    async def test_say_rejects_other_provider_and_unavailable_eve(self):
        other = tts.TextToSpeechEntity()
        other.entity_id = "tts.cloud"
        other._attr_name = "Cloud"
        other._attr_default_language = "de"
        other._attr_supported_languages = ["de"]
        await self.component.async_add_entities([other])
        self.assertIs(self.component.get_entity("tts.cloud"), other)
        with self.assertRaisesRegex(ServiceValidationError, "nicht geladen"):
            await self.say(entity_id="media_player.sonos", message="Hallo", tts_entity_id="tts.cloud")
        self.entity._attr_available = False
        with self.assertRaisesRegex(ServiceValidationError, "nicht verfügbar"):
            await self.say(entity_id="media_player.sonos", message="Hallo")
        self.assertEqual(self.playbacks, [])

    async def test_playback_failure_is_propagated_once(self):
        play = AsyncMock(side_effect=HomeAssistantError("Playback failed"))
        self.hass.services.async_register("media_player", "play_media", play)
        with self.assertRaisesRegex(HomeAssistantError, "Playback failed"):
            await self.say(entity_id="media_player.sonos", message="Hallo")
        self.assertEqual(play.await_count, 1)

    async def test_synthesis_failure_is_propagated_without_retry(self):
        self.client.synthesize.side_effect = EveError("EVE unavailable")
        await self.say(entity_id="media_player.sonos", message="Hallo", options={"preferred_format": "wav"})
        with self.assertLogs("homeassistant.components.tts", level="ERROR"):
            with self.assertRaisesRegex(HomeAssistantError, "EVE unavailable"):
                await tts.async_get_media_source_audio(self.hass, self.playbacks[0].data["media_content_id"])
        self.client.synthesize.assert_awaited_once_with("Hallo", "de")

    async def test_invalid_call_is_rejected_before_playback(self):
        for data in (
            {"entity_id": "media_player.sonos"},
            {"message": "Hallo"},
            {"entity_id": [], "message": "Hallo"},
            {"entity_id": "light.kitchen", "message": "Hallo"},
            {"entity_id": "media_player.sonos", "message": "Hallo", "tts_entity_id": "light.eve"},
        ):
            with self.subTest(data=data), self.assertRaises(probatio.Invalid):
                await self.say(**data)
        self.assertEqual(self.playbacks, [])

    async def test_service_description_exposes_fields_for_action_discovery(self):
        description = service.async_get_cached_service_description(self.hass, "tts", "eve_say")
        self.assertIn("EVE", description["name"])
        self.assertTrue(description["fields"]["entity_id"]["required"])
        self.assertTrue(description["fields"]["message"]["required"])
        self.assertEqual(set(description["fields"]), {
            "entity_id", "message", "tts_entity_id", "cache", "language", "options"})
        for field in description["fields"].values():
            selector.validate_selector(field["selector"])
