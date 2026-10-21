# Veröffentlichung vorbereiten

Status: eigenständiges lokales Git-Repository, noch kein Remote und keine Veröffentlichung.
Ziel ist ein **neues**, öffentliches Repository `Dntouch/eve-home-assistant`;
das bestehende KI-Biotop-Repository wird nicht verwendet oder verändert.
GitHub-Eigentümer und MIT-Lizenz wurden am 21.10.2026 festgelegt.

1. Neues öffentliches GitHub-Repository `Dntouch/eve-home-assistant` anlegen,
   ohne automatisch erzeugte README, Lizenz oder .gitignore. Beschreibung:
   „Home Assistant Assist integration for EVE: Conversation, STT and TTS.“
   Topics: `home-assistant`, `hacs`, `eve`, `conversation`, `stt`, `tts`.
2. Manifest-URLs und Codeowner sind auf `Dntouch/eve-home-assistant` bzw.
   `@Dntouch` gesetzt. Die MIT-Lizenz liegt unter LICENSE.
3. Git-Autoridentität festlegen, initialen Commit erstellen und den neuen Remote
   hinzufügen; anschließend `main` pushen.
4. Tests aus README ausführen. Am 21.10.2026 bestanden alle 8 Integrationstests
   mit Python 3.14.8 und den Versionen aus requirements-test.txt.
   HACS-/HA-Metadaten mit den offiziellen Validatoren prüfen; diese lokale
   Vorbereitung behauptet keine bestandene HACS-Validierung. Für vollständige
   HACS-Konformität auch den geforderten Eintrag in Home Assistant Brands
   vorbereiten und dessen Status prüfen.
5. Version im Manifest prüfen und passenden Git-Tag v0.1.0 veröffentlichen.
6. Öffentliches Repository in HACS als benutzerdefiniertes Repository vom Typ
   Integration hinzufügen, herunterladen, HA neu starten und EVE einrichten.

Keine EVE-Konfiguration, Tokens, Chatverläufe oder Modelle veröffentlichen.
Die bestehende Kopie in EVE-Agent bleibt während der Übergabe erhalten. Künftige
Integration-Änderungen gehören in dieses Repository; Backend-Änderungen in EVE-Agent.

Referenzen:
- https://www.hacs.dev/docs/publish/integration/
- https://www.hacs.dev/docs/publish/start/
