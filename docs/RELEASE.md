# Releases

## Aktueller Stand

- Repository: [Dntouch/eve-home-assistant](https://github.com/Dntouch/eve-home-assistant)
- Entwicklung auf `main`, Manifest-Version: `0.2.0`.
- Lizenz: [MIT](../LICENSE).
- Installation über HACS als benutzerdefiniertes Repository vom Typ **Integration**.
  Die Anleitung steht in der [README](../README.md#installation-über-hacs-empfohlen).
- Das EVE-Icon wird unter `custom_components/eve_agent/brand/` mitgeliefert.

## Prüfstand

Stand 21.10.2026: Integrationstests mit Python 3.14 und Home Assistant
2026.10.2 sowie die Server-Tests für Ereignisempfang und Inbox sind bestanden.
[HACS und Hassfest bestehen für Version 0.2.0](https://github.com/Dntouch/eve-home-assistant/actions/runs/39669151855).
HACS meldet die fehlende Integrationskategorie als Warnung.

Installation und Sprachverarbeitung mit Version 0.1.0 wurden in Home Assistant
bestätigt. Der Praxistest des Ereigniskanals in Version 0.2.0 steht noch aus.

Der Workflow [Validate integration](https://github.com/Dntouch/eve-home-assistant/actions/workflows/validate.yaml)
führt beide Prüfungen bei Pushes und Pull Requests aus. Unter **Actions →
Validate integration → Run workflow** lassen sie sich auch manuell starten.

## Änderungen in 0.2.0

- Neue Aktion `eve_agent.send_event` für strukturierte Ereignisse.
- Optionaler Ereigniskanal in Assist-API v1 mit dauerhafter Server-Inbox und
  Duplikaterkennung über eine explizite Ereignis-ID.
- Brainwatch zeigt eine rein lesende Ereignis-Inbox mit exakten Gruppenzählern.
- Native Inbox-Werkzeuge erlauben EVE das Lesen und ausdrückliche Quittieren.
- Keine Bedeutungszuordnung, Default-Prompts oder automatischen LLM-Aufrufe.
- Der EVE-Server muss separat aktualisiert und neu gestartet werden.

## Vor einem versionierten Release

1. Integrationstests mit Python 3.14 ausführen:

   ```sh
   python3.14 -m venv .venv
   .venv/bin/python -m pip install -r requirements-test.txt
   .venv/bin/python -m unittest discover -s tests -v
   ```

2. Metadaten mit [HACS Action](https://www.hacs.dev/docs/publish/action/)
   und Hassfest prüfen und gemeldete Fehler beheben.
3. Installation bzw. Update über HACS prüfen. In Home Assistant Konversation,
   Spracherkennung und Sprachausgabe einzeln testen, einschließlich der
   Gesprächszuordnung nach einem Neustart.
4. Versionsnummer in `custom_components/eve_agent/manifest.json` festlegen.
   Für den Ereigniskanal sind `0.2.0` und der Tag `v0.2.0` vorgesehen.
5. Den geprüften Commit taggen und ein GitHub-Release mit Änderungen,
   Voraussetzungen und bekannten Einschränkungen veröffentlichen.

## Umfang des Release-Pakets

Die Integration liegt vollständig unter `custom_components/eve_agent/`.
EVE-Server, Konfiguration, Zugangsdaten, Chatverläufe und Modelle gehören
nicht in dieses Repository oder in Release-Archive.
