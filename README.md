# EVE für Home Assistant Assist

Mit EVE nutzt du deinen eigenen EVE-Agenten als Sprachassistenten in Home Assistant.
Die Integration stellt drei unabhängige Anbieter für Assist bereit:

| Assist-Einstellung | Anbieter |
| --- | --- |
| Konversationsagent | EVE |
| Sprache-zu-Text | EVE STT |
| Text-zu-Sprache | EVE TTS |

Die Verarbeitung erfolgt auf deinem EVE-Server. Home Assistant übernimmt die
Aufnahme und Wiedergabe am jeweiligen Gerät.

## Voraussetzungen

- Home Assistant **2026.10.2 oder neuer**.
- Eine separat laufende EVE-Installation mit aktivierter **Assist-API v1**
  und einem Assist-Token; siehe [EVE vorbereiten](#eve-vorbereiten).
- Home Assistant muss die EVE-Installation über das Netzwerk erreichen können.
- Für die empfohlene Installation: eingerichtetes [HACS](https://www.hacs.dev/).

## Installation über HACS (empfohlen)

Füge EVE in HACS als **benutzerdefiniertes Repository** hinzu:

1. Öffne **HACS** in Home Assistant.
2. Öffne oben rechts das **Drei-Punkte-Menü → Benutzerdefinierte Repositories**.
3. Trage `https://github.com/Dntouch/eve-home-assistant` als Repository ein
   und wähle den Typ **Integration**.
4. Füge das Repository hinzu, öffne **EVE** in HACS und lade die Integration herunter.
5. Starte Home Assistant neu und richte EVE wie unten beschrieben ein.

Updates der Integration kannst du anschließend über HACS herunterladen.
Die Schritte zum Hinzufügen eines Repositorys beschreibt auch die
[HACS-Anleitung](https://www.hacs.dev/docs/faq/custom_repositories/).

### Alternative: manuelle Installation

1. Lade den Quellcode über **Code → Download ZIP** von
   [GitHub](https://github.com/Dntouch/eve-home-assistant) herunter und entpacke ihn.
2. Kopiere den enthaltenen Ordner `custom_components/eve_agent` in das
   `custom_components`-Verzeichnis deiner Home-Assistant-Konfiguration.
   Danach muss `/config/custom_components/eve_agent/manifest.json` existieren.
   Je nach Installationsart kann das Konfigurationsverzeichnis anders heißen.
3. Starte Home Assistant neu. Bei dieser Installationsart musst du Updates selbst einspielen.

## EVE in Home Assistant einrichten

1. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach
   **EVE** suchen.
2. EVEs Basis-URL (ohne `/api/message`) und den separaten Assist-Token eintragen.
   Beispiel: `https://eve.example:8790`.
3. Bei einem selbstsignierten EVE-Zertifikat muss dessen CA auf HA vertraut sein
   oder für diese Verbindung **TLS-Zertifikat prüfen** ausgeschaltet werden.
4. Gesprächszuordnung **mapped** belassen. Die Option **fixed** benötigt eine
   bereits existierende EVE-Gesprächs-ID und teilt diese zwischen HA-Unterhaltungen.
5. Unter **Einstellungen → Sprachassistenten** den Assistenten öffnen und die
   drei EVE-Anbieter auswählen. Für direkte Verarbeitung durch EVE die Option
   **Lokale Verarbeitung von Befehlen bevorzugen** ausschalten.

Der Timeout gilt je HTTP-Aufruf; 180 Sekunden sind voreingestellt. Während des
ersten Modellladens kann eine Anfrage länger dauern. Nachfolgende Änderungen
an URL, Token und Timeout erfolgen über **Neu konfigurieren** an der Integration.

## EVE vorbereiten

Der separat installierte EVE-Agent benötigt die Assist-API v1 und diese Einstellung:

```json
{"assist_api": {"enabled": true}}
```

Der Token steht in `EVE_ASSIST_TOKEN` oder in der lokalen `.env`, nicht in
`eve.json`. In der EVE-Einstellungsseite kann er unter **Home Assistant Assist**
gesetzt werden. Danach EVE neu starten. Der EVE-Host muss vom HA-Rechner über die
angegebene URL erreichbar und in `visual.allowed_hosts` erlaubt sein.

Technische Details zu Endpunkten und Datenformaten findest du in
[docs/ASSIST-API.md](docs/ASSIST-API.md).

## Hinweise zur Nutzung

- Neue Assist-Chats erhalten eigene EVE-Gespräche. Diese Zuordnung bleibt nach
  einem Neustart von Home Assistant erhalten.
- Die Sprachausgabe verwendet die in EVE eingestellte Stimme.
- Spracherkennung und Sprachausgabe verarbeiten vollständige Aufnahmen bzw.
  Antworten. Eine fortlaufende Ausgabe während der Verarbeitung gibt es derzeit nicht.
- Ist EVE ausgelastet oder nicht erreichbar, zeigt Home Assistant einen Fehler an.
  Gesprächsanfragen werden nicht automatisch wiederholt.
- Bilder und Dateianhänge aus Home Assistant werden nicht automatisch an EVE übertragen.

## Entwicklung

Die API ist in [docs/ASSIST-API.md](docs/ASSIST-API.md) beschrieben.
Hinweise zu Releases und noch offenen Prüfungen stehen in
[docs/RELEASE.md](docs/RELEASE.md).

Für die Tests Python 3.14 verwenden:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python -m unittest discover -s tests -v
```

Die Tests benötigen keinen laufenden EVE-Server.

## Lizenz

[MIT](LICENSE)
