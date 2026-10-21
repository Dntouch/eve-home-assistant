# EVE Assist API v1

Basis-URL: HTTP(S)-Adresse der separat laufenden EVE-Instanz. Alle Endpunkte unter
/api/assist/ benötigen `Authorization: Bearer <Assist-Token>`.

| Methode / Pfad | Eingabe | Antwort |
| --- | --- | --- |
| GET /info | — | api_version=1, conversation=true, stt/tts siehe unten |
| POST /conversations | {} | {"conversation_id":"…"} |
| POST /conversation | {"text":"…","images":[],"conversation_id":"…"} | {"answer":"…","conversation_id":"…","turn_id":"…"} |
| POST /stt?language=de | application/octet-stream: PCM 16 kHz, 16 Bit, mono, little endian | {"text":"…"} |
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
