# EVE Home Assistant

This is the independent Home Assistant integration repository, domain `eve_agent`.
The EVE server belongs to the separate EVE-Agent project. Do not copy its source,
configuration, memories, credentials, models, or runtime data into this repository.

- Keep Conversation, STT, and TTS independent; Conversation must not synthesize audio.
- Treat the integration as transport: do not introduce prompts or language heuristics.
- Preserve text and conversation mapping. Never automatically retry a conversation turn.
- Keep runtime code under custom_components/eve_agent for HACS.
- Maintain docs/ASSIST-API.md when changing the API contract; coordinate server changes.
- Test with Python 3.14 and requirements-test.txt, then run unittest discover -s tests -v.
- GitHub owner is Dntouch; license is MIT. See docs/RELEASE.md before a release.
