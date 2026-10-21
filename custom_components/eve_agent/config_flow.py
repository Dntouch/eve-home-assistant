import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EveClient, EveAuthError, EveError, normalize_url
from .const import (DOMAIN, CONF_URL, CONF_TOKEN, CONF_TIMEOUT, CONF_VERIFY_SSL,
                    CONF_STRATEGY, CONF_FIXED_ID)


def schema(defaults):
    return vol.Schema({
        vol.Required(CONF_URL, default=defaults.get(CONF_URL, "")): str,
        vol.Required(CONF_TOKEN, default=defaults.get(CONF_TOKEN, "")): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
        vol.Required(CONF_TIMEOUT, default=defaults.get(CONF_TIMEOUT, 180)): vol.All(vol.Coerce(int), vol.Range(min=1, max=900)),
        vol.Required(CONF_VERIFY_SSL, default=defaults.get(CONF_VERIFY_SSL, True)): bool,
        vol.Required(CONF_STRATEGY, default=defaults.get(CONF_STRATEGY, "mapped")): vol.In(["mapped", "fixed"]),
        vol.Optional(CONF_FIXED_ID, default=defaults.get(CONF_FIXED_ID, "")): str,
    })


class EveConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _validate(self, data):
        data[CONF_URL] = normalize_url(data[CONF_URL])
        if not data[CONF_TOKEN].strip():
            raise ValueError("Token is required")
        if data.get(CONF_STRATEGY) == "fixed" and not data.get(CONF_FIXED_ID, "").strip():
            raise ValueError("Fixed conversation ID is required")
        client = EveClient(async_get_clientsession(self.hass, verify_ssl=data.get(CONF_VERIFY_SSL, True)),
                           data[CONF_URL], data[CONF_TOKEN], data.get(CONF_TIMEOUT, 180))
        return await client.info()

    async def async_step_user(self, user_input=None):
        return await self._step("user", user_input)

    async def async_step_reconfigure(self, user_input=None):
        return await self._step("reconfigure", user_input)

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        return await self._step("reauth_confirm", user_input)

    async def _step(self, step, data):
        errors = {}
        entry = (self._get_reconfigure_entry() if step == "reconfigure" else
                 self._get_reauth_entry() if step == "reauth_confirm" else None)
        defaults = entry.data if entry else {}
        if data is not None:
            defaults = data
            try:
                await self._validate(data)
            except EveAuthError:
                errors["base"] = "invalid_auth"
            except EveError:
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "invalid_config"
            else:
                if step == "reconfigure":
                    return self.async_update_reload_and_abort(self._get_reconfigure_entry(), data_updates=data, unique_id=data[CONF_URL])
                if step == "reauth_confirm":
                    return self.async_update_reload_and_abort(self._get_reauth_entry(), data_updates=data, unique_id=data[CONF_URL])
                await self.async_set_unique_id(data[CONF_URL])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="EVE", data=data)
        return self.async_show_form(step_id=step, data_schema=schema(defaults), errors=errors)
