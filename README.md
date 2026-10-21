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

## Ereignisse aus Automationen senden

Ab Version **0.2.0** steht die Aktion **EVE: Ereignis senden** (`eve_agent.send_event`)
zur Verfügung. Dafür muss auch der EVE-Server den Ereigniskanal unterstützen.
Nach dem Server-Update EVE neu starten, die Integration über HACS aktualisieren
und Home Assistant neu starten.

Unter **Entwicklerwerkzeuge → Aktionen** wählst du **EVE: Ereignis senden** und
die gewünschte EVE-Installation. Der YAML-Editor zeigt deren `config_entry_id`.
Diese ID kannst du in einer Automation verwenden:

```yaml
alias: Bewegung an EVE melden
triggers:
  - trigger: state
    entity_id: binary_sensor.bewegung_flur
    from: "off"
    to: "on"
actions:
  - action: eve_agent.send_event
    data:
      config_entry_id: DEINE_EVE_CONFIG_ENTRY_ID
      event_type: motion_detected
      data:
        entity_id: "{{ trigger.entity_id }}"
        area: Flur
    response_variable: empfang
mode: single
```

Passe Sensor, Installations-ID und Daten an deine Automation an. `event_type`
ist eine frei gewählte Kennung; die Integration wertet sie nicht aus.
`data` enthält ein JSON-Objekt. Pro Ereignis sind höchstens 64 KiB erlaubt.

EVE speichert das Ereignis und bestätigt mit `accepted`, `event_id` und
`duplicate` den Empfang. Die optionale `response_variable` enthält diese Werte.
Es wird kein Chat gestartet, kein Prompt erzeugt und kein LLM aufgerufen.
Auch während eines laufenden Chats werden Ereignisse separat gespeichert;
sie unterbrechen den Chat nicht und werden ihm nicht automatisch hinzugefügt.
Unter **EVE Brainwatch → Ereignisse** siehst du offene Ereignisgruppen mit
Anzahl, Daten und erstem/letztem Empfang. Exakt gleicher Typ und gleiche
JSON-Daten bilden eine Gruppe; die einzelnen Eingänge bleiben gespeichert.
Die Anzeige quittiert nichts.

EVE kann die Inbox über ihre nativen Werkzeuge `assist_events.list` und
`assist_events.acknowledge` lesen und Gruppen ausdrücklich quittieren. Neue
Eingänge nach dem gelesenen Stand bleiben offen. Quittiert bedeutet nur
„zur Kenntnis genommen“. Es gibt keinen automatischen Weckaufruf, keine
Reaktionsregel und keine automatische Übernahme ins Memory.

Ohne `event_id` bekommt jeder Aufruf eine neue ID. Mit derselben expliziten ID
und denselben Daten wird ein Ereignis nur einmal gespeichert. Dieselbe ID mit
anderen Daten führt zu einem Fehler. Nach Verbindungsfehlern wird nicht
automatisch erneut gesendet; bei einem Timeout kann der Server das Ereignis
bereits gespeichert haben.

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
