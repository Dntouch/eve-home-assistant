# EVE für Home Assistant Assist

Mit EVE nutzt du deinen eigenen EVE-Agenten als Sprachassistenten in Home Assistant.
Die Integration stellt drei unabhängige Anbieter für Assist bereit:

| Assist-Einstellung | Anbieter |
| --- | --- |
| Konversationsagent | EVE |
| Sprache-zu-Text | EVE STT |
| Text-zu-Sprache | EVE TTS |

Die Integration ist eine Transportbrücke. Antworten, Gedächtnis, Gerätezugriffe,
Spracherkennung und Stimme kommen von der laufenden EVE-Installation. Keine
Prompts, kein weiteres LLM, keine Modelle auf dem HA-Rechner.

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

## Verhalten und Grenzen dieser Version

- Die HA→EVE-Gesprächszuordnung liegt dauerhaft in HA-Storage. Neue HA-Chats
  bekommen eigene EVE-Gespräche. Ein HA-Neustart verwirft die Zuordnung nicht.
- Anfragen derselben Unterhaltung werden sequenziell verarbeitet. EVE kann bei
  gleichzeitig laufenden anderen Unterhaltungen mit einem sichtbaren Fehler
  antworten. Es gibt keinen automatischen Wiederholungsversuch für Gesprächsturns.
- STT erwartet die von Assist gelieferten 16-kHz-/16-Bit-/Mono-PCM-Daten. Sie
  werden zunächst gesammelt und von EVE mit einem WAV-Header versehen. Diese
  Version liefert keine partiellen Transkripte oder Streaming-TTS-Ausgabe.
- TTS verwendet EVEs konfigurierte Stimme und liefert WAV an Home Assistant;
  HA übernimmt die Ausgabe am Zielgerät und notwendige Formatkonvertierung.
- Conversation selbst erzeugt kein Audio. Dadurch wird die Antwort nicht
  zweimal vertont und nicht zusätzlich am EVE-Rechner abgespielt.
- Keine Ableitung von Fragen, Befehlen oder Antworten im Brückencode.
- Bilder werden nur transportiert, wenn der aufrufende Client tatsächlich ein
  `images`-Array bereitstellt. Normale HA-Sprachaufrufe enthalten keines;
  HA-Dateianhänge werden nicht automatisch gelesen oder konvertiert.
- Keine YAML-Konfiguration in dieser Version; Einrichtung über die HA-UI.

## Eigenständiges Entwicklungsprojekt

Dieses Repository enthält ausschließlich die Home-Assistant-Integration. Der
EVE-Server und seine Modelle werden im separaten EVE-Agent-Projekt gepflegt.
Der gemeinsame Vertrag ist in [docs/ASSIST-API.md](docs/ASSIST-API.md) beschrieben.

Die Integration steht unter der [MIT-Lizenz](LICENSE). Hinweise zur
Veröffentlichung und zu noch offenen Validierungen stehen in
[docs/RELEASE.md](docs/RELEASE.md).

### Tests

Python 3.14 und eine virtuelle Umgebung verwenden:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python -m unittest discover -s tests -v
```

Die Tests verwenden echte HA-Entitäten und HA-Storage sowie einen lokalen
HTTP-Testserver für den EVE-API-Vertrag. Sie benötigen weder EVE-Quellcode
noch Sprachmodelle, Zugangsdaten oder eine laufende Home-Assistant-Installation.
