"""HTTP transport only. EVE owns all language processing and synthesis."""
import asyncio
from contextlib import asynccontextmanager
from urllib.parse import urlsplit
import weakref

import aiohttp

from .const import CONF_FIXED_ID, CONF_STRATEGY, MAX_AUDIO_BYTES


class EveError(Exception):
    pass


class EveAuthError(EveError):
    pass


def normalize_url(value):
    value = value.rstrip("/")
    parsed = urlsplit(value)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("Expected an HTTP(S) base URL without credentials, query or fragment")
    return value


class EveClient:
    def __init__(self, session, url, token, timeout=180):
        self.session, self.url = session, normalize_url(url)
        self.token, self.timeout = token, timeout

    async def request(self, method, path, *, binary=False, **kwargs):
        headers = {"Authorization": "Bearer " + self.token, **kwargs.pop("headers", {})}
        try:
            async with self.session.request(
                method, self.url + "/api/assist/" + path, headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout), allow_redirects=False, **kwargs,
            ) as response:
                if response.status in {401, 403}:
                    raise EveAuthError("EVE: Zugriff verweigert; Token und erlaubten Host prüfen")
                if response.status >= 300:
                    raise EveError(f"EVE: HTTP {response.status} bei {path}")
                limit = 16 * 1024 * 1024 if binary else 1024 * 1024
                body = bytearray()
                async for chunk in response.content.iter_chunked(65536):
                    body.extend(chunk)
                    if len(body) > limit:
                        raise EveError("EVE-Antwort überschreitet das Größenlimit")
                if binary:
                    if not body.startswith(b"RIFF") or body[8:12] != b"WAVE":
                        raise EveError("EVE lieferte kein WAV-Audio")
                    return bytes(body)
                import json
                result = json.loads(body)
                if not isinstance(result, dict):
                    raise EveError("EVE lieferte kein JSON-Objekt")
                return result
        except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
            raise EveError("EVE-Verbindung fehlgeschlagen oder Antwort ungültig") from exc

    async def info(self):
        info = await self.request("GET", "info")
        try:
            if (info["api_version"] != 1 or info["conversation"] is not True
                    or info["stt"]["sample_rate"] != 16000 or info["stt"]["channels"] != 1
                    or info["stt"]["sample_bytes"] != 2 or info["tts"]["format"] != "wav"):
                raise ValueError()
            for kind in ("stt", "tts"):
                languages = info[kind]["languages"]
                if not isinstance(languages, list) or not languages or not all(isinstance(v, str) and v for v in languages):
                    raise ValueError()
        except (KeyError, TypeError, ValueError) as exc:
            raise EveError("EVE unterstützt nicht die erforderliche Assist-API v1") from exc
        return info

    async def transcribe(self, stream, language):
        pcm = bytearray()
        async for chunk in stream:
            pcm.extend(chunk)
            if len(pcm) > MAX_AUDIO_BYTES:
                raise EveError("Audioaufnahme zu groß")
        result = await self.request("POST", "stt", data=bytes(pcm),
                                    headers={"Content-Type": "application/octet-stream"},
                                    params={"language": language})
        if not isinstance(result.get("text"), str):
            raise EveError("EVE lieferte keine Transkription")
        return result["text"]

    async def synthesize(self, text, language):
        return await self.request("POST", "tts", binary=True, json={"text": text, "language": language})


class EveRuntime:
    def __init__(self, client, info, store, config):
        self.client, self.info, self.store, self.config = client, info, store, config
        self.mapping = {}
        self._locks = weakref.WeakValueDictionary()
        self._storage_lock = asyncio.Lock()

    async def load(self):
        self.mapping = await self.store.async_load() or {}
        if not isinstance(self.mapping, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in self.mapping.items()):
            raise EveError("Ungültige gespeicherte Gesprächszuordnung")

    @asynccontextmanager
    async def lock(self, key):
        lock = self._locks.get(key)
        if lock is None:
            lock = self._locks[key] = asyncio.Lock()
        async with lock:
            yield

    async def remember(self, key, value):
        async with self._storage_lock:
            updated = {**self.mapping, key: value}
            try:
                await self.store.async_save(updated)
            except OSError as exc:
                raise EveError("Gesprächszuordnung konnte nicht gespeichert werden") from exc
            self.mapping = updated

    async def converse(self, text, conversation_id, images):
        fixed = self.config.get(CONF_STRATEGY) == "fixed"
        async with self.lock(self.config.get(CONF_FIXED_ID, "") if fixed else conversation_id):
            identifier = self.config.get(CONF_FIXED_ID) if fixed else self.mapping.get(conversation_id)
            if not identifier:
                created = await self.client.request("POST", "conversations", json={})
                identifier = created.get("conversation_id")
                if not isinstance(identifier, str) or not identifier:
                    raise EveError("EVE lieferte keine Gesprächs-ID")
                await self.remember(conversation_id, identifier)
            result = await self.client.request("POST", "conversation", json={
                "text": text, "conversation_id": identifier, "images": images})
            if not isinstance(result.get("answer"), str) or not isinstance(result.get("conversation_id"), str) or not result["conversation_id"]:
                raise EveError("EVE lieferte keine gültige Gesprächsantwort")
            if not fixed and result["conversation_id"] != identifier:
                await self.remember(conversation_id, result["conversation_id"])
            return result["answer"]
