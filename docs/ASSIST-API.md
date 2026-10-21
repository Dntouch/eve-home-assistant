# EVE Assist API v1

Basis-URL: HTTP(S)-Adresse der separat laufenden EVE-Instanz. Alle Endpunkte unter
/api/assist/ benötigen `Authorization: Bearer <Assist-Token>`.

| Methode / Pfad | Eingabe | Antwort |
| --- | --- | --- |
| GET /info | — | api_version=1, conversation=true, stt/tts siehe unten |
| POST /conversations | {} | {"conversation_id":"…"} |
| POST /conversation | {"text":"…","images":[],"conversation_id":"…"} | {"answer":"…","conversation_id":"…","turn_id":"…"} |
| POST /stt?language=de | application/octet-stream: PCM 16 kHz, 16 Bit, mono, little endian | {"text":"…"} |
| POST /events | JSON-Ereignis, siehe unten | HTTP 202: Empfangsbestätigung |
| GET /events?after=0&limit=100 | Cursor und Seitengröße | Gespeicherte Ereignisse und next_cursor |
| POST /tts | {"text":"…","language":"de"} | audio/wav, RIFF/WAVE |

/info beschreibt stt als {"languages":["de"],"sample_rate":16000,
"sample_bytes":2,"channels":1} und tts als {"languages":["de"],"format":"wav"}.
Die tatsächlichen Sprachen stammen aus EVE; Deutsch ist hier ein Beispiel.

Conversation erzeugt kein Audio. STT startet kein Gespräch. TTS spielt am Server
kein Audio ab. Texte werden unverändert transportiert. Die Integration legt pro
HA-Gespräch eine EVE-ID an und speichert sie vor dem ersten Turn dauerhaft.
Die optionale fixed-Strategie verwendet eine bereits vorhandene EVE-ID.

401/403 werden als Authentifizierungsfehler behandelt, sonstige HTTP-Fehler,
Timeouts und ungültige Antworten als sichtbare Fehler. Kein automatischer
Wiederholungsversuch eines Gesprächs. Kein Streaming in API v1.

## Ereigniskanal (optionale Erweiterung von API v1)

Ein unterstützender Server meldet zusätzlich `"events": true` in `/info`.
Fehlt das Feld oder ist es nicht `true`, bleibt Conversation/STT/TTS verfügbar;
`eve_agent.send_event` bricht vor dem Senden mit einem sichtbaren Fehler ab.
Nach einem Server-Update muss die Integration neu geladen werden.

`POST /events` erwartet `application/json` mit genau diesen Feldern:

```json
{"event_id":"sensor-123","event_type":"motion_detected","data":{"area":"Flur"}}
```

- `event_id` und `event_type`: nicht leere Zeichenketten mit höchstens 128 Zeichen.
- `data`: JSON-Objekt; verschachtelte JSON-Werte sind erlaubt, NaN/Infinity nicht.
- Maximale Größe des vollständigen UTF-8-JSON-Requests: 65.536 Bytes.
- Die HA-Aktion verlangt eine explizite `config_entry_id` für die Zielinstallation.
  Sie erzeugt eine UUID, wenn der Aufrufer keine `event_id` angibt.
- Der Server bestätigt erst nach dauerhafter Speicherung mit HTTP 202:
  `{"accepted":true,"event_id":"sensor-123","duplicate":false}`.
- Dieselbe ID mit gleichem Typ und gleichen Daten liefert `duplicate:true`.
  Die Reihenfolge von JSON-Objektschlüsseln ist dabei unerheblich.
  Dieselbe ID mit abweichendem Inhalt wird mit HTTP 400 abgewiesen.
- Die Inbox gehört zur EVE-Serverinstallation, nicht zu einem Chat. IDs sind
  innerhalb dieser Inbox eindeutig. Sie liegt in `runtime/assist-events.sqlite3`
  bzw. im entsprechend konfigurierten Runtime-Verzeichnis und bleibt bei
  Neustarts erhalten. Automatisches Löschen ist nicht implementiert.

`GET /events` liest gespeicherte Ereignisse in Empfangsreihenfolge, ohne sie
zu löschen oder als verarbeitet zu markieren. `after` ist eine nicht negative
Sequenznummer (Standard 0), `limit` liegt zwischen 1 und 100 (Standard 100).
Die Antwort enthält `events` mit `sequence`, `event_id`, `event_type`, `data`,
`received_at` (UTC) sowie `next_cursor`. Auf der nächsten Seite wird dieser
Cursor als `after` übergeben. Ein leerer Abruf behält den Cursor bei.
Beide Endpunkte benötigen denselben Assist-Bearer-Token wie die übrige API.

Der Kanal transportiert und speichert Daten ohne Bedeutungszuordnung,
Default-Prompt, Prompt-Vorlage, LLM-Aufruf oder automatische Reaktion.
Ein paralleler Chat wird nicht unterbrochen oder um Ereignisse ergänzt.
Ereignisse erzeugen weder Gesprächs-IDs noch Audio. Es gibt keine automatische
Wiederholung. Bei einem Timeout ist der Speicherstatus unbekannt; eine
bewusste Wiederholung mit identischer `event_id` und identischen Daten ist
idempotent. Die Empfangsbestätigung bedeutet Speicherung, nicht Verarbeitung.

## Brainwatch und nativer Inbox-Zugriff auf dem EVE-Server

`GET /api/brainwatch/assist-events?offset=0&limit=50` liest die offenen Gruppen
über den bestehenden Browser-Zugang (`X-EVE-Token`, falls konfiguriert), nicht
über den Assist-Token. `offset` ist nicht negativ, `limit` liegt zwischen 1 und
100. Die Antwort enthält `groups`, `pending_count`, `pending_groups`,
`total_count` und `next_offset` (oder `null`). Eine Gruppe enthält `group_id`,
`event_type`, unveränderte `data`, `count`, `first_received_at`,
`last_received_at` und `through_sequence`.

Gruppierung erfolgt nur nach exakt gleichem Ereignistyp und kanonischen
JSON-Daten (sortierte Objektschlüssel). IDs und Empfangszeiten sind kein Teil
des Gruppenschlüssels. Es gibt weder Ähnlichkeitssuche noch Bedeutungszuordnung.
Eine erneute Übermittlung derselben Ereignis-ID erhöht den Zähler nicht.
Verschiedene IDs mit demselben Inhalt sind separate Eingänge derselben Gruppe.

EVE erhält die native Capability `assist_events` mit den Operationen `list`
und `acknowledge`. `list` liest dieselben offenen Gruppen. `acknowledge`
verlangt die veröffentlichte `group_id` und deren `through_sequence`.
Es quittiert nur diese Gruppe bis zum gelesenen Stand; spätere Eingänge
bleiben offen. Quittierungen sind persistent. Rohereignisse bleiben über
`GET /api/assist/events` verfügbar. Quittiert ist kein Nachweis einer Reaktion.
Brainwatch kann nur lesen und quittiert nicht selbst.

Die Capability wird bei aktivierter Assist-API veröffentlicht. Der Eingang
startet keinen LLM-Turn und unterbricht keinen laufenden Turn. EVE kann die
Werkzeuge innerhalb eines regulären Turns selbst auswählen. Ein automatischer
Hintergrundaufruf oder ein Ereignis-Default-Prompt ist nicht implementiert.
Die Seitennummerierung der Gruppen ist eine aktuelle Ansicht, kein Snapshot;
bei gleichzeitigen neuen Eingängen oder Quittierungen erneut ab Offset 0 lesen.
