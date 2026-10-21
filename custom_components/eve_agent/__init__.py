"""EVE conversation, speech recognition and speech synthesis."""
import hashlib
from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers import config_validation as cv

from .api import EveClient, EveRuntime, EveAuthError, EveError
from .const import DOMAIN, CONF_URL, CONF_TOKEN, CONF_TIMEOUT, CONF_VERIFY_SSL

PLATFORMS = [Platform.CONVERSATION, Platform.STT, Platform.TTS]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass, config):
    from .services import async_register_services

    async_register_services(hass)
    return True


async def async_setup_entry(hass, entry):
    data = {**entry.data, **entry.options}
    client = EveClient(async_get_clientsession(hass, verify_ssl=data.get(CONF_VERIFY_SSL, True)),
                       data[CONF_URL], data[CONF_TOKEN], data.get(CONF_TIMEOUT, 180))
    try:
        info = await client.info()
        endpoint_key = hashlib.sha256(client.url.encode()).hexdigest()[:16]
        runtime = EveRuntime(client, info, Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.{endpoint_key}"), data)
        await runtime.load()
    except EveAuthError as exc:
        raise ConfigEntryAuthFailed(str(exc)) from exc
    except (EveError, OSError) as exc:
        raise ConfigEntryNotReady(str(exc)) from exc
    entry.runtime_data = runtime
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
