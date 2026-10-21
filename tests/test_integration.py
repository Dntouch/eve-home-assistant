"""Run with a real Home Assistant installation, not HA module stubs."""
import asyncio
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import wave

try:
    import aiohttp
    from homeassistant.components import stt
    from homeassistant.components.conversation import ConversationInput
    from homeassistant.core import Context, HomeAssistant
except ModuleNotFoundError as exc:
    raise unittest.SkipTest("Home Assistant test environment required") from exc

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from custom_components.eve_agent.api import EveClient, EveRuntime, EveError, EveAuthError
from custom_components.eve_agent.conversation import EveConversation
from custom_components.eve_agent.stt import EveSTT
from custom_components.eve_agent.tts import EveTTS
from homeassistant.helpers.storage import Store
from aiohttp import web


class HAIntegrationTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.hass = HomeAssistant(self.temp.name)
        self.calls = []
        self.created = 0
        self.events = []
        self.event_status = 202
        output = io.BytesIO()
        with wave.open(output, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(16000)
            audio.writeframes(b"\x00\x00" * 100)
        wav_bytes = output.getvalue()

        async def handle(request):
            if request.headers.get("Authorization") != "Bearer test-only":
                return web.Response(status=401)
            operation = request.match_info["operation"]
            if operation == "info":
                return web.json_response({"api_version": 1, "conversation": True, "events": True,
                    "stt": {"languages": ["de"], "sample_rate": 16000,
                            "sample_bytes": 2, "channels": 1},
                    "tts": {"languages": ["de"], "format": "wav"}})
            if operation == "events":
                payload = await request.json()
                self.events.append(payload)
                return web.json_response({"accepted": True, "event_id": payload["event_id"],
                                          "duplicate": False}, status=self.event_status)
            if operation == "conversations":
                self.created += 1
                return web.json_response({"conversation_id": f"eve-{self.created}"})
            if operation == "conversation":
                data = await request.json()
                self.calls.append((data["text"], data["images"], data["conversation_id"]))
                return web.json_response({"answer": "  Antwort\n",
                    "conversation_id": data["conversation_id"], "turn_id": "turn"})
            if operation == "stt":
                assert request.query["language"] == "de"
                assert await request.read() == b"\x00\x00" * 100
                return web.json_response({"text": "Erkannter Text"})
            if operation == "tts":
                assert await request.json() == {"text": "Hallo", "language": "de"}
                return web.Response(body=wav_bytes, content_type="audio/wav")
            return web.Response(status=404)

        app = web.Application()
        app.router.add_route("*", "/api/assist/{operation}", handle)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        self.session = aiohttp.ClientSession()
        self.client = EveClient(self.session, f"http://127.0.0.1:{port}", "test-only", 5)
        self.info = await self.client.info()
        self.store = Store(self.hass, 1, "eve_test_mapping")
        self.runtime = EveRuntime(self.client, self.info, self.store, {"conversation_strategy": "mapped"})
        await self.runtime.load()
        self.entry = SimpleNamespace(entry_id="test", runtime_data=self.runtime)

    async def asyncTearDown(self):
        await self.session.close()
        await self.runner.cleanup()
        await self.hass.async_stop(force=True)
        self.temp.cleanup()

    async def test_conversation_uses_real_entity_and_persistent_mapping(self):
        entity = EveConversation(self.entry)
        entity.entity_id = "conversation.eve"
        log = SimpleNamespace(conversation_id="ha-chat", async_add_assistant_content_without_tools=Mock())
        input = ConversationInput(text="  Original\n", context=Context(), conversation_id="ha-chat",
                                  device_id=None, satellite_id=None, language="de", agent_id="conversation.eve")
        result = await entity._async_handle_message(input, log)
        self.assertEqual(result.response.speech["plain"]["speech"], "  Antwort\n")
        self.assertEqual(self.calls, [("  Original\n", [], "eve-1")])
        restored = EveRuntime(self.client, self.info, Store(self.hass, 1, "eve_test_mapping"), {})
        await restored.load()
        await restored.converse("Nachfrage", "ha-chat", [])
        self.assertEqual(self.created, 1)
        self.assertEqual(self.calls[-1][2], "eve-1")

    async def test_real_stt_entity_accepts_assist_pcm(self):
        entity = EveSTT(self.entry)
        metadata = stt.SpeechMetadata(language="de", format=stt.AudioFormats.WAV,
            codec=stt.AudioCodecs.PCM, bit_rate=stt.AudioBitRates.BITRATE_16,
            sample_rate=stt.AudioSampleRates.SAMPLERATE_16000, channel=stt.AudioChannels.CHANNEL_MONO)
        self.assertTrue(entity.check_metadata(metadata))
        async def audio():
            yield b"\x00\x00" * 100
        result = await entity.async_process_audio_stream(metadata, audio())
        self.assertEqual(result.text, "Erkannter Text")
        self.assertEqual(result.result, stt.SpeechResultState.SUCCESS)
        self.assertEqual(self.calls, [])

    async def test_real_tts_entity_returns_wav(self):
        entity = EveTTS(self.entry)
        extension, audio = await entity.async_get_tts_audio("Hallo", "de", {})
        self.assertEqual(extension, "wav")
        with wave.open(io.BytesIO(audio)) as wav:
            self.assertEqual(wav.getnframes(), 100)
        self.assertEqual(entity.default_language, "de")
        self.assertEqual(self.calls, [])

    async def test_auth_failure_is_explicit(self):
        client = EveClient(self.session, self.client.url, "wrong", 5)
        with self.assertRaises(EveAuthError):
            await client.info()

    async def test_fixed_strategy_reuses_existing_eve_conversation(self):
        self.runtime.config = {"conversation_strategy": "fixed", "fixed_conversation_id": "existing"}
        await asyncio.gather(self.runtime.converse("one", "ha-1", []),
                             self.runtime.converse("two", "ha-2", []))
        self.assertEqual(self.created, 0)
        self.assertEqual([call[2] for call in self.calls], ["existing", "existing"])

    async def test_config_flow_validates_real_backend_and_all_platforms_are_registered(self):
        from custom_components.eve_agent import PLATFORMS
        from custom_components.eve_agent.config_flow import EveConfigFlow, schema
        from homeassistant.const import Platform
        self.assertEqual(set(PLATFORMS), {Platform.CONVERSATION, Platform.STT, Platform.TTS})
        data = schema({})({"url": self.client.url, "token": "test-only", "timeout": 5,
                           "verify_ssl": True, "conversation_strategy": "mapped"})
        flow = EveConfigFlow()
        flow.hass = self.hass
        # This harness does not boot HA's global mDNS/network stack.
        with patch("custom_components.eve_agent.config_flow.async_get_clientsession", return_value=self.session):
            info = await flow._validate(data)
        self.assertEqual(info["api_version"], 1)

    async def test_same_chat_requests_are_sequential(self):
        await asyncio.gather(*(self.runtime.converse(str(i), "same-chat", []) for i in range(8)))
        self.assertEqual(self.created, 1)
        self.assertEqual(len(self.calls), 8)
        self.assertEqual({call[2] for call in self.calls}, {"eve-1"})

    async def test_mapping_save_failure_does_not_send_a_turn(self):
        async def fail(_):
            raise OSError("storage failure")
        self.runtime.store.async_save = fail
        with self.assertRaises(EveError):
            await self.runtime.converse("Do not send", "new-chat", [])
        self.assertEqual(self.calls, [])

    async def test_event_action_preserves_structured_data_without_conversation(self):
        from custom_components.eve_agent import async_setup
        await async_setup(self.hass, {})
        payload = {"entity_id": "binary_sensor.flur", "area": "  Flur\n", "values": [False, 2, None]}
        with patch("custom_components.eve_agent.services.service.async_get_config_entry", return_value=self.entry) as resolve:
            result = await self.hass.services.async_call("eve_agent", "send_event", {
                "config_entry_id": "test", "event_type": "motion_detected", "data": payload,
                "event_id": "motion-1"}, blocking=True, return_response=True)
        resolve.assert_called_once_with(self.hass, "eve_agent", "test")
        self.assertEqual(result, {"accepted": True, "event_id": "motion-1", "duplicate": False})
        self.assertEqual(self.events, [{"event_id": "motion-1", "event_type": "motion_detected", "data": payload}])
        self.assertEqual((self.created, self.calls), (0, []))

    async def test_event_failure_is_not_retried(self):
        self.event_status = 503
        with self.assertRaises(EveError):
            await self.client.send_event("motion", {}, "id")
        self.assertEqual(len(self.events), 1)
        self.assertEqual((self.created, self.calls), (0, []))

    async def test_event_rejects_non_json_and_oversized_data_before_sending(self):
        for data in ({"value": float("nan")}, {"value": object()}, {"value": "x" * 65536}):
            with self.assertRaises(EveError):
                await self.client.send_event("motion", data, "id")
        self.assertEqual(self.events, [])

    async def test_event_action_rejects_old_backend_without_sending(self):
        from custom_components.eve_agent import async_setup
        from homeassistant.exceptions import ServiceValidationError
        await async_setup(self.hass, {})
        self.runtime.info = {**self.info, "events": False}
        with patch("custom_components.eve_agent.services.service.async_get_config_entry", return_value=self.entry):
            with self.assertRaises(ServiceValidationError):
                await self.hass.services.async_call("eve_agent", "send_event", {
                    "config_entry_id": "test", "event_type": "motion"}, blocking=True)
        self.assertEqual(self.events, [])

    async def test_event_action_requires_explicit_loaded_target(self):
        import voluptuous as vol
        from custom_components.eve_agent import async_setup
        from homeassistant.exceptions import ServiceValidationError
        await async_setup(self.hass, {})
        with self.assertRaises(vol.Invalid):
            await self.hass.services.async_call("eve_agent", "send_event", {
                "event_type": "motion"}, blocking=True)
        self.hass.config_entries = SimpleNamespace(async_get_entry=lambda entry_id: None)
        with self.assertRaises(ServiceValidationError):
            await self.hass.services.async_call("eve_agent", "send_event", {
                "config_entry_id": "missing", "event_type": "motion"}, blocking=True)
        self.assertEqual(self.events, [])

    async def test_event_action_generates_id_without_response_variable(self):
        import uuid
        from custom_components.eve_agent import async_setup
        await async_setup(self.hass, {})
        with patch("custom_components.eve_agent.services.service.async_get_config_entry", return_value=self.entry):
            await self.hass.services.async_call("eve_agent", "send_event", {
                "config_entry_id": "test", "event_type": "motion"}, blocking=True)
        uuid.UUID(self.events[0]["event_id"])
        self.assertEqual(self.events[0]["data"], {})
