# Browser calling and consented local audio analysis

**STEP_26 update:** the transport/consent/lifecycle instructions remain valid, but
the original four-second append-only ASR description below is historical. Current
ASR uses VAD-driven overlapping windows (up to eight seconds), provisional/final
revision rows, bounded four-window coalescing and explicit finalization. See
[incremental ASR](incremental-asr.md) for the current algorithm and validation.

Open `/workspace/#/live`. Calling is opt-in and disabled by default. The existing
batch-job monitor remains on the page and works without live transport enabled.

## Local demonstration

The implementation uses three separate paths:

- WebRTC carries encrypted peer audio directly between the two browsers.
- WebSockets carry authenticated signaling, session/consent updates and server ASR
  events. They do not carry binary call audio.
- An authorized HTTP endpoint accepts a separate 16 kHz mono PCM16LE microphone
  copy, only when both participants have permitted analysis and are connected.

Create an invitation for an enabled member of your own tenant. Each participant
must connect with their own signed workspace identity, check microphone consent,
then choose **Join with microphone** and grant browser microphone permission.
Analysis permission is a separate checkbox and starts off. Either participant may
revoke it; this stops analysis for both while their conversation can continue.
The permission is for this ephemeral call only and never grants training rights.

The browser requests no video, uses native echo/noise controls, and exposes an
**Enable speaker** control if autoplay is blocked. Activity indicators and packet
counters come from native WebRTC statistics, not generated demonstration values.
No application audio recording is written to disk or object storage. Transcripts
and media buffers are ephemeral. Browser/server memory is released logically;
this is not a claim of forensic byte-zeroing.

**End call**, tab/navigation cleanup, a signaling disconnect, disabled identity,
authorization expiry or session expiry ends the room and stops local media.
An ICE disconnection has a ten-second local recovery grace period with capture
stopped. Persistent failure ends the call. **Reconnect with a new invitation**
creates a new room, and both participants must consent and join again. It does not
silently resume a recording or restore old audio buffers.

## Configuration

```powershell
$env:LIVE_ENABLED='true'
$env:LIVE_ALLOWED_ORIGINS='http://127.0.0.1:8788'
$env:LIVE_ASR_MODEL_PATH=Get-Content .local/step25_asr_path -Raw
```

Allowed origins must be exact canonical origins, without a path or trailing slash.
HTTP is accepted only for explicitly configured loopback origins; use HTTPS/WSS
for other hosts. The demonstrated loopback HTTP origin is a browser secure
context, but HTTP analysis/signaling is not TLS encrypted. The peer media uses
DTLS-SRTP. Remote HTTPS/WSS deployment has not been validated in this step.

`LIVE_ASR_MODEL_PATH` must reference an already available CTranslate2 Whisper
directory containing `model.bin`. There are no model downloads. Empty configuration
allows calls without analysis. The isolated test used cached Whisper Tiny on CPU
with int8, four CPU threads and one inference worker; it does not change the
application's batch ASR defaults or establish French/Arabic/Darija accuracy.

Run exactly one ASGI worker. Rooms, tickets and buffers live in its process memory.
The common `WEB_CONCURRENCY` setting is checked, but explicit external CLI worker
overrides still require correct deployment configuration. There is no distributed
broker, failover, durable consent ledger, call recording or PSTN/SIP/PBX gateway.
No STUN/TURN infrastructure is configured. Direct candidates were tested on this
laptop; other networks, restrictive NATs and mobile handoffs are unvalidated.

The isolated preview prepared for this step can be restarted with:

```powershell
$env:PROJECT28_TEST_ADMIN_URL_FILE='.local/step25_test_admin_url'
$env:PROJECT28_TEST_APP_URL_FILE='.local/step25_test_app_url'
$env:PROJECT28_PREVIEW_STEP='25'
$env:PROJECT28_PREVIEW_PORT='8788'
$env:LIVE_ENABLED='true'
$env:LIVE_ALLOWED_ORIGINS='http://127.0.0.1:8788,http://127.0.0.1:8789'
$env:LIVE_ASR_MODEL_PATH=Get-Content .local/step25_asr_path -Raw
uv run --no-sync python -m scripts.preview_workspace
```

After `npm --prefix apps/web run build`, open
`http://127.0.0.1:8788/workspace/#/live`. Private synthetic test credentials are
written to `.local/step25-ui-context.json`, expire after an hour and must not be
published. They are not a production sign-in system. This seeder accepts only
matching explicitly isolated loopback test databases. Its STEP_25 Windows launcher
uses a selector event loop and bounds WebSocket messages to 64 KiB / queue 8.

## Capture, clocks and backpressure

The browser's 16 kHz AudioContext feeds an AudioWorklet that transfers one-second
32,000-byte PCM16LE frames. The participant ID is obtained from authenticated
identity, never from the audio body. Headers carry the frame sequence, starting
sample index and current consent revision. The server rejects stale epochs,
replays, gaps, wrong size/content type, excessive bursts and unauthorized callers.
It rechecks both participants' enabled status before frame admission.

Per-participant buffering forms four-second ASR windows. There is one active
local inference worker and one pending work item across rooms. Queue pressure
revokes analysis and clears pending media while leaving the call available.
The browser also stops capture if an upload cannot finish before the next frame;
it does not build an unbounded JavaScript upload queue.

Within a participant, timestamps follow the accepted sample clock. Cross-party
alignment is anchored to first server receipt minus the frame duration, and is
therefore approximate by network/browser scheduling delay. Consent revisions
invalidate queued and in-flight results on revocation/disconnect. An inference
already executing in a native thread cannot be forcibly interrupted; its stale
result is discarded. Termination discards partial windows rather than flushing
additional analysis after the session has ended.

This is a transport and bounded ASR-path prototype. It does not implement
stabilized incremental hypotheses, final full-call transcription, assistant
suggestions or measured end-to-end production latency. Those remain later steps.
Regex PII redaction is applied to emitted ASR text and is not complete anonymity.

## Validation

```powershell
$env:PROJECT28_TEST_ADMIN_URL_FILE='.local/step25_test_admin_url'
$env:PROJECT28_TEST_APP_URL_FILE='.local/step25_test_app_url'
uv run --no-sync pytest tests/streaming -q
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
npm --prefix apps/web run api:check
npm --prefix apps/web test
npm --prefix apps/web run build
node tests/frontend/live-call.mjs
```

The browser harness requires the isolated preview/private context and
`.local/step25-browser-speech.wav`, generated from Windows SAPI for this execution.
It launches two isolated Chrome contexts with synthetic microphone input and
actual native WebRTC/DTLS/Opus. It checks consent, real offline Whisper output,
revocation, track cleanup, a new-room reconnect, screenshots and accessibility.
It does not measure real callers, physical microphone quality or employee outcomes.
