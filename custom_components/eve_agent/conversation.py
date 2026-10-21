from homeassistant.components import conversation
from homeassistant.const import MATCH_ALL
from homeassistant.helpers import intent

from .api import EveError


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([EveConversation(entry)])


class EveConversation(conversation.ConversationEntity):
    _attr_name = "EVE"
    _attr_has_entity_name = True
    _attr_supported_features = conversation.ConversationEntityFeature.CONTROL

    def __init__(self, entry):
        self.runtime = entry.runtime_data
        self._attr_unique_id = entry.entry_id + "_conversation"

    @property
    def supported_languages(self):
        return MATCH_ALL

    async def _async_handle_message(self, user_input, chat_log):
        identifier = user_input.conversation_id or chat_log.conversation_id
        response = intent.IntentResponse(language=user_input.language)
        try:
            # Only images actually supplied by the caller are transported.
            # No attachment inference, prompts or local language interpretation.
            answer = await self.runtime.converse(user_input.text, identifier, getattr(user_input, "images", []))
        except EveError as exc:
            response.async_set_error(intent.IntentResponseErrorCode.UNKNOWN, str(exc))
        else:
            chat_log.async_add_assistant_content_without_tools(conversation.AssistantContent(
                agent_id=self.entity_id, content=answer))
            response.async_set_speech(answer)
        return conversation.ConversationResult(response=response, conversation_id=identifier)
