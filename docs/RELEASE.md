# Veröffentlichung vorbereiten

Status: Quellcode auf `main` im öffentlichen Repository
https://github.com/Dntouch/eve-home-assistant veröffentlicht.
Es handelt sich um ein **neues**, eigenständiges Repository;
das bestehende KI-Biotop-Repository wird nicht verwendet oder verändert.
GitHub-Eigentümer und MIT-Lizenz wurden am 21.10.2026 festgelegt.

1. Das neue öffentliche GitHub-Repository `Dntouch/eve-home-assistant` ist angelegt.
   Beschreibung und Topics bei Bedarf in GitHub ergänzen. Beschreibung:
   „Home Assistant Assist integration for EVE: Conversation, STT and TTS.“
   Topics: `home-assistant`, `hacs`, `eve`, `conversation`, `stt`, `tts`.
2. Manifest-URLs und Codeowner sind auf `Dntouch/eve-home-assistant` bzw.
   `@Dntouch` gesetzt. Die MIT-Lizenz liegt unter LICENSE.
3. Initialer lokaler Commit und Veröffentlichung über den GitHub-Connector
   sind erfolgt. Die lokale Git-Autoridentität verwendet `Dntouch` und die
   GitHub-Noreply-Adresse. Remote: `https://github.com/Dntouch/eve-home-assistant.git`.
4. Tests aus README ausführen. Am 21.10.2026 bestanden alle 8 Integrationstests
   mit Python 3.14.8 und den Versionen aus requirements-test.txt.
   HACS-/HA-Metadaten mit den offiziellen Validatoren prüfen; diese lokale
   Vorbereitung behauptet keine bestandene HACS-Validierung. Die Integration
   liefert das EVE-Icon unter `custom_components/eve_agent/brand/` mit.
   Home Assistant unterstützt lokale Brand-Bilder seit 2026.3; ein separater
   Eintrag im zentralen Brands-Repository ist dafür nicht erforderlich.
   Die Anzeige in HACS hängt zusätzlich von dessen Version und Bild-Cache ab.
5. Version im Manifest prüfen und passenden Git-Tag v0.1.0 veröffentlichen.
6. Öffentliches Repository in HACS als benutzerdefiniertes Repository vom Typ
   Integration hinzufügen, herunterladen, HA neu starten und EVE einrichten.

Keine EVE-Konfiguration, Tokens, Chatverläufe oder Modelle veröffentlichen.
Die bestehende Kopie in EVE-Agent bleibt während der Übergabe erhalten. Künftige
Integration-Änderungen gehören in dieses Repository; Backend-Änderungen in EVE-Agent.

Referenzen:
- https://www.hacs.dev/docs/publish/integration/
- https://www.hacs.dev/docs/publish/start/
