# EVE für Home Assistant Assist

Eine Custom Integration stellt drei unabhängige Anbieter bereit:

| Assist-Einstellung | Anbieter |
| --- | --- |
| Konversationsagent | EVE |
| Sprache-zu-Text | EVE STT |
| Text-zu-Sprache | EVE TTS |

Die Integration ist eine Transportbrücke. Antworten, Gedächtnis, Gerätezugriffe,
Spracherkennung und Stimme kommen von der laufenden EVE-Installation. Keine
Prompts, kein weiteres LLM, keine Modelle auf dem HA-Rechner.

## Installation

1. Das ZIP so in das HA-Konfigurationsverzeichnis entpacken, dass
   `/config/custom_components/eve_agent/manifest.json` existiert. Bei anderen
   Installationsarten kann das HA-Konfigurationsverzeichnis anders heißen.
2. Home Assistant neu starten.
3. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach
   **EVE** suchen.
4. EVEs Basis-URL (ohne `/api/message`) und den separaten Assist-Token eintragen.
   Beispiel: `https://eve.example:8790`.
5. Bei einem selbstsignierten EVE-Zertifikat muss dessen CA auf HA vertraut sein
   oder für diese Verbindung **TLS-Zertifikat prüfen** ausgeschaltet werden.
6. Gesprächszuordnung **mapped** belassen. Die Option **fixed** benötigt eine
   bereits existierende EVE-Gesprächs-ID und teilt diese zwischen HA-Unterhaltungen.
7. Unter **Einstellungen → Sprachassistenten** den Assistenten öffnen und die
   drei EVE-Anbieter auswählen. Für direkte Verarbeitung durch EVE die Option
   **Lokale Verarbeitung von Befehlen bevorzugen** ausschalten.

Der Timeout gilt je HTTP-Aufruf; 180 Sekunden sind voreingestellt. Während des
ersten Modellladens kann eine Anfrage länger dauern. Nachfolgende Änderungen
an URL, Token und Timeout erfolgen über **Neu konfigurieren** an der Integration.

## EVE-Seite

Der separat installierte EVE-Agent benötigt die Assist-API v1 und diese Einstellung:

```json
{"assist_api": {"enabled": true}}
```

Der Token steht in `EVE_ASSIST_TOKEN` oder in der lokalen `.env`, nicht in
`eve.json`. In der EVE-Einstellungsseite kann er unter **Home Assistant Assist**
gesetzt werden. Danach EVE neu starten. Der EVE-Host muss vom HA-Rechner über die
angegebene URL erreichbar und in `visual.allowed_hosts` erlaubt sein.

Alle `/api/assist/*`-Endpunkte benötigen `Authorization: Bearer <Assist-Token>`.
Die bisherige Browser-API bleibt separat bestehen.

| Endpunkt | Funktion |
| --- | --- |
| `GET /api/assist/info` | API-Version, Sprach- und Audioformate |
| `POST /api/assist/conversations` | Separates EVE-Gespräch ohne Modellaufruf anlegen |
| `POST /api/assist/conversation` | Text und vorhandene `images` an EVE, Antworttext zurück |
| `POST /api/assist/stt?language=de` | Roh-PCM transkribieren, kein Gespräch starten |
| `POST /api/assist/tts` | Text in WAV umwandeln, keine lokale Wiedergabe |

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

Entwickelt und gegen echte Entitätsklassen und Storage von Home Assistant
**2026.10.2** geprüft. Eine Installation in der konkreten HA-Zielinstanz ist ein
separater Schritt. Das Paket enthält keine Tokens oder Sprachmodelle.

## Validierung am 21.10.2026

8 Tests mit echten HA-2026.10.2-Entitätsklassen und HA-Storage sowie 5 Backend-API-Tests
bestanden. Zusätzlich bestanden 42 vorhandene VisualServer-, 21 Native-Runtime-,
20 Konfigurations- und 14 Nova-Snapshot-Tests.

Am laufenden EVE-Backend erfolgreich geprüft: Piper-WAV-Erzeugung, Transkription
dieses Testsatzes durch die vorhandene Whisper-small-Erkennung und ein separater
Conversation-Aufruf. Die zusätzliche Audio-Nachverarbeitung dieses Gesprächsturns
war `skipped`. Die Zielinstallation von Home Assistant wurde noch nicht verändert.

## Eigenständiges Entwicklungsprojekt

Dieses Repository enthält ausschließlich die Home-Assistant-Integration. Der
EVE-Server und seine Modelle werden im separaten EVE-Agent-Projekt gepflegt.
Der gemeinsame Vertrag ist in [docs/ASSIST-API.md](docs/ASSIST-API.md) beschrieben.

Die Quellstruktur und `hacs.json` sind für HACS vorbereitet. Der Quellcode ist auf
[Dntouch/eve-home-assistant](https://github.com/Dntouch/eve-home-assistant)
veröffentlicht. Die Integration steht unter der [MIT-Lizenz](LICENSE).
Ein versioniertes Release und die offiziellen HACS-/HA-Validierungen stehen noch aus;
siehe [docs/RELEASE.md](docs/RELEASE.md).

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
