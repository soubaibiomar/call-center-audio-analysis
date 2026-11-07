# Incremental ASR and transcript revisions

STEP_26 upgrades the opt-in browser call ASR path. It does not change the original
Gradio/batch recognizer or turn Whisper into a native streaming decoder.

## Recognition lifecycle

Each authorized participant has an independent sample clock, speech window builder
and hypothesis reconciler. The existing HTTP endpoint still accepts contiguous
one-second 16 kHz mono PCM16LE frames. Its identity, mutual consent, Origin,
sequence and consent-epoch checks remain in force.

`SpeechWindows` measures 20 ms RMS frames. The default threshold is 0.015 of full
scale, with 60 ms onset, 200 ms pre-roll and 600 ms silence hangover. This is an
energy heuristic: noise/music can trigger it and quiet speech can be missed. It
is not a trained or calibrated speech classifier.

An active utterance offers a provisional decode every two seconds. Windows never
exceed eight seconds. A long-speech split owns text only through one second before
the window ends; the next window retains prior context and that unfinished tail.
The first forced chunk owns seven seconds and later full chunks normally own six
seconds because they also include prior context. Time ownership and matching timed
boundary tokens prevent the same context from becoming two final transcript rows.

Whisper supplies native word timestamps. Injected older segment-only adapters
remain supported through explicitly labeled interpolated word timing. Only emitted
complete text is PII-redacted; raw transient word hypotheses are not public events.

## Event contract and UI

`LiveEvent.transcript` carries a `TranscriptRevision`: utterance UUID, monotonically
increasing revision, provisional/final/failed state, source ownership times, text,
agreement-prefix count, finalization reason, timing quality, window bounds and
measured processing/queue timing. The sender remains the authenticated microphone
participant; it is not a diarization claim about a physical person.

The frontend keys rows by participant plus utterance ID, replaces only newer
revisions, rejects stale epochs and preserves finalized rows. It displays amber
**Provisional**, green **Final**, or an interrupted-recognition status. Repeated
text alone is not a duplicate: genuinely repeated speech gets distinct IDs/times.
The UI shows at most 100 recent rows and clears them on consent changes/end.

The agreement-prefix count compares consecutive hypotheses after Unicode/case/
punctuation normalization. It is diagnostic: it does not make provisional text
irreversible or establish semantic truth. Only a final boundary commits the row.
This is not an implementation of a published LocalAgreement-2 policy.

Legacy `segments` are emitted for final text only. Consumers wanting provisional
updates must consume the revision contract rather than append every event.

Silence finalizes an utterance automatically. **Finalize my current speech** calls
`POST /api/v1/live/sessions/{id}/finalize` with the current consent revision. It
flushes only that authenticated participant's pending utterance while the call is
still authorized. Repeating it without more speech schedules nothing. A new audio
frame may begin a new turn. Manual cuts can still occur mid-word; do not treat
finalization as human verification.

End/disconnect/revocation intentionally discards unfinalized material and queued
results. Use explicit finalization before ending if a pending tail matters. An
already executing native inference cannot be forcibly interrupted, but its result
cannot cross a changed/ended consent epoch.

## Queues, failure and recovery

One CPU inference worker is active at a time. Up to four pending windows are
allowed by default; `LiveSettings.pending_windows` is bounded to 1–4. A newer queued
window for the same utterance replaces its earlier provisional work. Finals are
not replaced by later interim hypotheses. This bounds memory and avoids a backlog
of obsolete partials. Queue overflow still pauses analysis rather than recording
indefinitely; the WebRTC conversation can continue.

A decoder error emits an interrupted revision and an explicit retry notice. There
is one automatic retry; successful recognition updates the same row with a newer
revision. A second failure turns analysis off and tells both participants to grant
analysis again if they want a new attempt. There is no unbounded retry loop, raw
exception disclosure or analysis after consent is lost.

Four synchronized sources passed the short synthetic load replay on this laptop.
That is not a production concurrency guarantee for longer calls, different models
or noisy/language-mixed speech. Window coalescing intentionally skips obsolete
interim work; it is not proof that every possible partial was decoded.

## Run and validate locally

The isolated preview uses the existing schema revision, `0005_call_review`:

```powershell
$env:PROJECT28_TEST_ADMIN_URL_FILE='.local/step26_test_admin_url'
$env:PROJECT28_TEST_APP_URL_FILE='.local/step26_test_app_url'
$env:PROJECT28_PREVIEW_STEP='26'
$env:PROJECT28_PREVIEW_PORT='8790'
$env:LIVE_ENABLED='true'
$env:LIVE_ALLOWED_ORIGINS='http://127.0.0.1:8790'
$env:LIVE_ASR_MODEL_PATH=Get-Content .local/step25_asr_path -Raw
uv run --no-sync python -m scripts.preview_workspace
```

Build the frontend, then open `http://127.0.0.1:8790/workspace/#/live`. The private
synthetic context is `.local/step26-ui-context.json`; never publish its tokens.
No large model download or GPU/Ollama reconfiguration is involved. The measured
adapter used cached Whisper Tiny on CPU/int8. Production model choice is unchanged.

```powershell
uv run --no-sync pytest tests/streaming -q
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
npm --prefix apps/web run api:check
npm --prefix apps/web test
npm --prefix apps/web run build
node tests/frontend/incremental-call.mjs
uv run --no-sync python -m scripts.benchmark_incremental_asr --audio .local/step26-browser-speech.wav --model-file .local/step25_asr_path --output docs/implementation/evidence/step26-20261031/asr-benchmark.json
```

The browser harness uses `.local/step26-extended-mic.wav`, generated with Windows
SAPI. It checks real WebRTC, revision replacement in the same DOM row, manual
finalization, no duplicated row IDs, consent revocation, native track cleanup and
fresh-room reconnect. The load harness paces broker frames for 1/2/4 active sources
and distinguishes this from HTTP/WebRTC network load. It measures warmed offline
inference, baseline four-second chunks and repeated incremental windows. Evidence
contains real measurements, not model-quality or training claims.

Ready-to-event latency starts when an audio window is available at the server and
includes queue/decoding time. It excludes device capture, window-formation delay,
network transmission and browser rendering. RTF divides inference seconds by audio
seconds; effective RTF uses unique input duration and therefore includes repeated
window work. Percentiles use median p50 and nearest-rank p95. Small samples and
synthetic English speech do not establish multilingual performance or an SLA.
