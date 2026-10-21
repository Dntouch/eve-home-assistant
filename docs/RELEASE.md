# Releases

## Aktueller Stand

- Repository: [Dntouch/eve-home-assistant](https://github.com/Dntouch/eve-home-assistant)
- Entwicklung auf `main`, Manifest-Version: `0.1.0`.
- Lizenz: [MIT](../LICENSE).
- Installation über HACS als benutzerdefiniertes Repository vom Typ **Integration**.
  Die Anleitung steht in der [README](../README.md#installation-über-hacs-empfohlen).
- Das EVE-Icon wird unter `custom_components/eve_agent/brand/` mitgeliefert.

## Prüfstand

Am 21.10.2026 bestanden alle 8 Integrationstests mit Python 3.14.8,
Home Assistant 2026.10.2 und den Abhängigkeiten aus `requirements-test.txt`.
Die Tests prüfen Konversation, Gesprächszuordnung, STT, TTS und Einrichtung
gegen einen lokalen HTTP-Testserver.

Download über HACS, Einrichtung und Sprachverarbeitung in der
Home-Assistant-Zielinstanz wurden am 21.10.2026 erfolgreich bestätigt.
Automatische Prüfungen am 21.10.2026 ([Prüflauf](https://github.com/Dntouch/eve-home-assistant/actions/runs/39665770590)):

- **Hassfest: bestanden.** Die Reihenfolge der Manifest-Felder wurde korrigiert.
- **HACS Action: alle 10 Prüfungen bestanden.** Beschreibung und Topics sind ergänzt.
  Die fehlende Kategorie im Integrationsmanifest wird weiterhin als Warnung gemeldet.

Der Workflow [Validate integration](https://github.com/Dntouch/eve-home-assistant/actions/workflows/validate.yaml)
führt beide Prüfungen bei Pushes und Pull Requests aus. Unter **Actions →
Validate integration → Run workflow** lassen sie sich auch manuell starten.

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
   Für die erste Version sind `0.1.0` und der Tag `v0.1.0` vorgesehen.
5. Den geprüften Commit taggen und ein GitHub-Release mit Änderungen,
   Voraussetzungen und bekannten Einschränkungen veröffentlichen.

## Umfang des Release-Pakets

Die Integration liegt vollständig unter `custom_components/eve_agent/`.
EVE-Server, Konfiguration, Zugangsdaten, Chatverläufe und Modelle gehören
nicht in dieses Repository oder in Release-Archive.
