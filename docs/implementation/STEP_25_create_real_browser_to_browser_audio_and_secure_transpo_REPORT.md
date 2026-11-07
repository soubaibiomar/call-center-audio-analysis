# STEP_25 — Create real browser-to-browser audio and secure transport

**Follow-on note (2026-10-31):** STEP_26 subsequently replaces independent
four-second/append-only ASR with VAD-driven overlapping windows and versioned
provisional/final rows, adds explicit authorized finalization and bounds the pending
queue to four windows with coalescing. STEP_25's execution results below are its
historical checkpoint; transport, permission and cleanup behavior remain. See the
STEP_26 report for current ASR behavior and retained limitations.

**DONE — PASS WITH LIMITATIONS**, for a single-worker local browser-call prototype.
Owner: Platform / local ML integration (Codex). Date: 2026-10-31,
Africa/Casablanca. Windows 11, PowerShell, uv-managed Python 3.12.15, Node 24.18.0,
Chrome, local PostgreSQL and cached Whisper Tiny CPU inference.
Branch `feature/project28-foundation`; working HEAD
`a37e4634af1d2947fc3c548d54e62bda0b0daf89`; pinned original upstream
`fed4b610742c1337147281fcec8f2cdcc0a79be5`. No commit, push, public deployment,
production database migration, package/model download, training or model promotion.

## 1. Goal and plain-English explanation

Implemented a real two-party browser call. Native WebRTC carries peer audio;
authenticated WebSockets carry signaling and server events. A separate HTTP
capture path sends microphone PCM to local ASR only after both authenticated
participants explicitly allow analysis and report their media connection ready.
Ending or losing the signaling session clears room membership, tickets and pending
audio, while the client releases its microphone, audio processing and peer state.

Read the master instructions, STEP_INDEX, complete STEP_25 prompt/template,
STEP_24 report and unresolved limitations, approved design system/checklist and
both reference images. Inspected the existing live/batch monitor, authentication,
application lifetime, transcription interfaces, database fixtures and schema
generator before editing. STEP_24 passed with documented research limitations;
its signed identity boundary, shared shell and tested playback infrastructure
provide prerequisites. No prior real browser media transport existed.

Validated two distinct signed identities in isolated Chrome contexts using
Windows-SAPI-generated microphone speech, actual WebRTC/DTLS/Opus, real HTTP PCM
capture and an already cached local neural checkpoint. This is not a physical
two-person conversation study, telephone integration or an accuracy benchmark.
All three transport gates were executed, with the limitations below retained.

## 2. Actual upstream versus upgraded implementation

| Capability | Original pinned upstream | Before STEP_25 | Implemented behavior / exact location | Compatibility |
|---|---|---|---|---|
| Microphone input | `src/ui/tabs/analyze.py::build_analyze_tab` accepts uploaded/recorded audio for batch analysis | Integrated workspace offered local playback and batch-job monitoring | `LivePage`, `BrowserCall.connect`: explicit consent, native permission and two-party audio | Existing Gradio and batch pipeline unchanged |
| Media transport | No `services/streaming/` or native browser-call implementation in upstream | Live UI truthfully said transport unavailable | Native `RTCPeerConnection`, direct encrypted media; participant-bound signaling | New opt-in feature, disabled by default |
| Live analysis admission | Batch `process_call` path | No live media admission | `routes.audio`, `LiveBroker.audio`, `LocalWhisper`: separate consent-gated raw PCM input | No batch ASR/default model change |
| Authentication | Original application security/audit surrounds analysis | Verified signed identities mapped to enabled tenant users | Existing `Principal` reused; one-use room/user-bound WS tickets and exact Origin checks | No guest identity or fabricated role system |
| Events | No live transcription event channel | HTTP polling for stored job states | Typed `LiveEvent` over WS; no binary media on WS | Original polling retained in `BatchMonitor` |
| Lifecycle | No room/peer/capture lifecycle | Local-file player cleanup | `LiveBroker.end`, `BrowserCall.stop`: buffers/tickets/RTC/tracks/context cleanup | Source calls and reviewed annotations unaffected |
| API contracts | Original Gradio application | 33 documented HTTP paths | 40 HTTP paths plus explicit `x-live-websocket` frame contracts | Additive API; database stays at `0005_call_review` |
| UI | Original Gradio | Green-neutral shell and read-only live placeholder | Two participant cards, real connection/activity/statistics, consent and End/reconnect controls | Existing shell, review UI, reports and batch controls preserved |

Git artifacts are saved under [step25 evidence](evidence/step25-20261031/), including
`git-stat-before/after.txt` and `git-names-before/after.txt`. The repository contains
substantial accumulated earlier work: ordinary Git diff omits untracked new
directories and is not a STEP_25-only patch. `step-files.json` compares pre-step
and final source-root fingerprints and identifies **27 changed/new source files**.
The inventory below separately covers CI, stubs, OpenAPI and documentation outside
those fingerprint roots. No earlier accumulated change is attributed to this step.

## 3. Files created, modified and preserved

All paths are repository-relative. No source or dataset was deleted.

| Path | Change / important exports / purpose and validation |
|---|---|
| `services/streaming/__init__.py` | New package; ephemeral live-call boundary |
| `services/streaming/contracts.py` | New strict consent, room, ticket, signal, event and receipt DTOs; schema/unit/browser validation |
| `services/streaming/settings.py` | New opt-in settings, exact secure-origin and resource-limit checks; negative tests |
| `services/streaming/broker.py` | New `Participant`, `Room`, `Ticket`, `Work`, `LiveBroker`; lifetime, queues, admission, consent fences and cleanup; real HTTP/WS plus asynchronous broker tests |
| `services/streaming/asr.py` | New `ASRPort`, `LocalWhisper`; bounded offline PCM-to-text CPU inference; real local smoke and browser evidence |
| `services/streaming/routes.py` | New `live_routers`; authenticated directory/invitations/consent/tickets/capture and separate socket handler; permission/protocol tests |
| `services/api/app.py` | Injects broker/settings/ASR, registers HTTP/WS routes, closes broker on shutdown, publishes real WS DTO schemas; existing auth boundary retained |
| `services/api/schemas.py`, `services/api/routes/workspace.py` | Context can truthfully report `webrtc_direct_demo` when enabled, otherwise `not_available` |
| `stubs/faster_whisper/__init__.pyi` | Extends the consumed existing SDK constructor signature with typed CPU-thread/worker/offline keywords; no runtime replacement |
| `apps/web/src/features/live/LivePage.tsx` | Replaces unavailable placeholder with config-gated call setup, consent, participants, stats, transcript, End/reconnect and retained batch monitor |
| `apps/web/src/features/live/BatchMonitor.tsx` | Extracts the existing batch monitoring behavior; existing browser regression still executes it |
| `apps/web/src/features/live/transport.ts` | New `BrowserCall`, `CallUpdate`, `MediaStats`, `liveError`; native media, signaling, capture, stats and cleanup lifecycle |
| `apps/web/src/features/live/pcm-worklet.js` | New audio-render-thread PCM16LE framing; transfer one-second buffers, no file/network access |
| `apps/web/src/features/live/live.css` | New responsive green/neutral participant/forms/statistics layout |
| `apps/web/src/features/live/transport.test.ts` | Four new tests: permission denial, late permission cleanup, event validation and action errors |
| `apps/web/src/app/App.tsx` | Background identity refresh no longer unmounts an already authenticated call; failed identity still removes protected views |
| `apps/web/src/lib/api/client.ts` | Adds bounded same-origin live read/write paths to existing allowlists |
| `apps/web/scripts/generate-api.mjs` | Consumes live DTOs and standalone validators |
| `generated.ts`, `schema.generated.json`, `validators.generated.mjs`, `validators.generated.d.mts` in `apps/web/src/lib/api/` | Four regenerated canonical contract artifacts |
| `docs/api/openapi.json`, `tests/api/test_api.py` | Updated 40-path schema, WS extension and expected count; canonical schema regression passed |
| `scripts/preview_workspace.py` | Adds isolated STEP_25 port/context selection; Windows selector event loop and bounded WS transport configuration |
| `tests/streaming/conftest.py`, `tests/streaming/test_transport.py` | New signed HTTP/WS/PostgreSQL and asynchronous broker tests; 21 focused cases |
| `tests/frontend/live-call.mjs` | New two-browser real media/ASR test, native track cleanup, metrics, screenshots and axe scans |
| `.github/workflows/ci.yml` | Adds streaming tests to existing isolated PostgreSQL CI run |
| `docs/development/browser-calling.md` | New configuration, privacy, lifecycle, buffering and validation runbook |
| This report, `PROGRESS.md`, `CURRENT_LIMITATIONS.md`, evidence directory | Implementation record, progress, retained limitations and observed outputs |

Existing emotion UI, frontend legacy entry/config, package lock, dependency pins,
ASR/QA/Gradio agents and STEP_24 review source remain unchanged by this step.
Private `.local` context, synthetic WAV, model-path and disposable test URL files
are execution material, not public configuration or credentials to commit.

## 4. Architecture, code and algorithm explanation

```text
Participant A browser ←── WebRTC / DTLS-SRTP / negotiated Opus ──→ Participant B
         │                                                            │
         ├── authenticated signaling and events: WS tickets ───────────┤
         │                 FastAPI + ephemeral broker                  │
         └── own PCM16LE via HTTP, only with mutual analysis consent ──┘
                       ↓ bounded four-second work item
                one offline CPU Whisper worker
                       ↓ redacted typed transcript events over WS
```

**Contracts and entry points.** Under `/api/v1/live`, `GET /config` reports enabled
and analysis availability; `GET /peers` lists up to 50 enabled members of the same
tenant, excluding self/service/disabled users; `GET/POST /sessions` lists or creates
invitations; `DELETE /sessions/{id}` ends a participant's room;
`PATCH /sessions/{id}/consent` changes permissions; `POST /sessions/{id}/tickets`
issues a one-use WS credential; `POST /sessions/{id}/audio` admits exact PCM frames.
`/api/v1/live/socket/{id}` is a separate WebSocket endpoint, not an HTTP media route.
OpenAPI explicitly publishes `SocketAuth`, `SocketMessage`, `LiveEvent` and the
socket extension because FastAPI cannot infer WS frame schemas automatically.

**`LiveSettings`.** Disabled by default. Enabling requires exact allowed origins.
Non-loopback HTTP origins, paths, wildcards and embedded credentials are rejected.
Rooms are limited to eight globally and 600 seconds, with one active room per
participant. The common multi-worker environment setting is rejected when enabled.
This is a single-process contract, not a distributed session service.

**`LiveBroker.create`, `room`, `reap`, `view`.** Routes resolve both participants
through the existing tenant-scoped database connection. The broker generates a
random UUID room and keeps only ephemeral membership/permission/buffer state.
Every access checks tenant, membership and expiry. Expired invitations are removed
when accessed; connected rooms also have socket deadlines. Views contain actual
consent/media state and accepted sample counters, without audio or storage paths.

**`issue`, `attach`.** The existing HTTP boundary first verifies JWT signature,
issuer, audience, lifetime and enabled database identity. The ticket route then
reads that already verified token's expiry; unverified decoding here only extracts
the deadline and never grants identity. A cryptographically random, single-use
ticket binds room/user/tenant, expires within 30 seconds and cannot outlive the
original authorization. It is sent in the first socket text frame, not in a URL,
cookie or access log. Attachment rejects duplicate sockets and replayed tickets.

**`live_routers.socket`.** Check Origin before accepting; authenticate the first
bounded text frame within five seconds; recheck the enabled account. A bounded
writer queue sends typed events. Incoming signaling accepts one audio media
section with a SHA-256 DTLS fingerprint; video/data descriptions are rejected.
Only the initiator offers and the other participant answers. ICE candidates relay
only within the same consenting room. Binary/invalid frames, oversized messages,
signaling floods, heartbeat timeout, identity disablement or authorization expiry
terminate the room. A first-frame credential is not a replacement for ongoing
expiry/enabled-user checks. No peer connection is made to the application server.

**`consent`, `connection`, `reset_capture`, `allowed`.** Both participants must
permit microphone use before signaling. Analysis additionally requires their
separate analysis grants, attached sockets, connected media states and an available
local ASR adapter. Changes advance a consent revision and clear buffered/pending
media. Captures and results from an earlier revision cannot be applied later.
The browser's reported connected state is coordination metadata, not server proof
of a physical person speaking.

**`routes.audio`, `LiveBroker.audio`.** Require authenticated membership, allowed
Origin, mutual consent and current enabled status for both users. Accept only
`application/octet-stream` with exactly 32,000 bytes: one second of 16 kHz mono
PCM16LE. Headers carry sequence, starting sample and consent revision. Reject
replay, gaps, stale revisions, wrong length/type and uploads excessively ahead of
the wall clock. Body reading stops at the byte limit and rechecks the room/gates
after asynchronous receipt, so consent changes during upload cannot bypass checks.

**Buffering and `process`.** Each participant accumulates at most a four-second
128,000-byte window. One local worker processes inference and one pending work
item is allowed globally. Queue overflow revokes analysis, purges pending buffers
and reports backpressure while leaving peer conversation available. Before/after
inference, the worker checks room existence, permission and consent revision.
Revoked/terminated results are discarded. Native inference already executing in
a thread cannot be forcibly stopped; no new inference is admitted after revocation.

**`LocalWhisper.transcribe`.** Validate bounded PCM; interpret little-endian int16,
convert to float32 and divide by 32768. Lazily load an existing local CTranslate2
model with `device='cpu'`, int8, four threads, one worker and offline-only loading.
Iterate the generator to execute real inference, clamp spans to input duration,
redact recognizable PII and emit bounded typed segments. No container decoder,
temporary audio file, hosted provider, training or batch cache write is involved.

**Timestamp alignment.** Accepted sample indices give an exact per-track ordering
at 16,000 samples/second. First server receipt minus frame duration anchors each
participant to the shared capture epoch. Network/scheduling delay makes cross-party
alignment approximate; it is not synchronized hardware time. Four-second windows
are independent; partial tails are discarded at revocation/end for cleanup rather
than analyzed after termination. This is not stabilized incremental/full-call ASR.

**`BrowserCall.connect`, `signal`, `event`.** After explicit UI consent, request
audio-only `getUserMedia`, create a native peer, add microphone tracks and open the
ticket-authenticated socket. Set microphone/analysis grants only after socket
attachment is acknowledged. The initiator offers once both participants are ready;
the other answers; early ICE candidates wait until a remote description exists.
Native remote tracks play through an audio element with an explicit speaker button
for autoplay restrictions. Connection state is sent to the server and shown in UI.

**`startCapture`, worklet, `upload`, `stopCapture`.** Only a current allowed epoch
starts a 16 kHz AudioContext and AudioWorklet. Float samples are clipped, encoded
as little-endian int16 and transferred in one-second buffers. A silent output gain
keeps processing active without playing the microphone back. Only one upload may
be pending; overlap stops analysis rather than growing a browser queue. Requests
carry bearer headers, omit cookies, refuse redirects and time out. Revocation
disconnects the processor, closes the context and aborts pending capture requests.

**`stop`, `end`, cleanup.** End/disconnect/navigation stops tracks, native RTC,
socket, context, timers and remote playback; clears UI transcripts/counters; removes
server room/tickets/queued work. A late microphone permission grant is immediately
stopped if the user ended meanwhile. A ten-second disconnected-media grace period
permits native recovery with capture stopped; persistent failure ends. Reconnect
creates a new room and requires fresh consent. Background identity revalidation
no longer unmounts a valid call while fetching; an actual failure still removes
protected content and releases media.

## 5. Imports and dependency explanation

No new package was installed and no dependency pin or package lock changed.
Versions below were read from the running environment; full evidence is in
`versions.json`. Browser APIs are native Chrome APIs, not new npm libraries.

| Actual import / symbols | Origin and version | Purpose, call site and tradeoff |
|---|---|---|
| `asyncio` | Python stdlib 3.12.15 | Bounded queues/tasks, socket deadlines and off-loop inference; avoids blocking signaling with CPU work |
| `contextlib` | stdlib | Suppresses expected cancellation/disconnect during socket cleanup; does not hide admission/model errors as successes |
| `secrets`, `time` | stdlib | Random tickets; monotonic session/capture deadlines and wall-clock JWT expiry conversion |
| `dataclass`, `field` | stdlib `dataclasses` | Independent per-room/participant buffers, queue references and work records |
| `UUID`, `uuid4` | stdlib `uuid` | Validated identifiers and random room IDs |
| `Path`, `os`, `urlsplit` | stdlib pathlib/os/urllib.parse | Verify local model directory, explicit settings and exact secure-origin validation |
| `Annotated`, `Literal`, `Protocol`; `Callable` | stdlib typing/collections.abc | Bounded DTO annotations, event/state variants, injectable ASR and typed engine factory |
| `Field`, `StringConstraints`, `model_validator`, `ValidationError` | Pydantic 2.11.3 | Input limits, consent prerequisites, audio-only SDP, strict frame validation and safe rejection |
| `HTTPException`, `APIRouter`, `Depends`, `Header`, `Request`, `Response`, `WebSocket` | FastAPI 0.162.0 | Authenticated routes, bounded header/body contracts, explicit 204 and WS adapters |
| `run_in_threadpool`, `WebSocketDisconnect` | Starlette 0.52.1 | Keep database checks off the event loop and clean up transport disconnects |
| `select`, `Engine` | SQLAlchemy 2.0.41 | Reuse scoped enabled-user queries; no new persistence layer |
| `jwt` | PyJWT 2.15.1, existing dependency | Extract already verified token expiry for socket lifetime; never authenticates unsigned claims |
| `numpy as np` | Existing locked NumPy 2.5.4 | PCM int16-to-float32 conversion; same numerical dependency already used by preprocessing |
| `WhisperModel` | faster-whisper 1.2.1 / CTranslate2 4.8.3 | Real offline neural inference; CPU chosen to avoid altering/contending with existing GPU/Ollama workloads |
| `Strict`, `Principal`, `User`, `get_identity`, `session_scope`, `redact_pii` | Existing local review/auth/database/security modules | Reuse strict extras policy, signed identity, tenant isolation and cautious text redaction |
| `ASRPort`, `LocalWhisper`, `LiveBroker`, `live_routers`, `LiveSettings` | New local streaming modules | Separate settings, state, inference adapter and HTTP/socket composition |
| `AudioReceipt`, `LiveConfig`, `LiveConsent`, `LiveCreate`, `LiveEvent`, `LiveParticipant`, `LivePeer`, `LivePeers`, `LiveSessions`, `LiveSessionView`, `LiveSignal`, `LiveTicket`, `MediaState`, `SocketAuth`, `SocketMessage`, `LiveTranscriptSpan` | New local contracts | Actual typed inputs/outputs, signaling coordination and event serialization; generated browser types derive from these same schemas |
| `useEffect`, `useRef`, `useState`; existing `FormEvent` in extracted monitor | React 19.3.1 | Call UI state, native-resource references and unmount cleanup; no new global state library |
| `useSession`, `sendResource`, `ApiError`, `useApiQuery`, `validateResource` | Existing/extended local frontend modules | Transient bearer identity, safe paths, query lifecycle and offline runtime validators |
| Generated `LiveConfig`, `LiveEvent`, `LivePeers`, `LiveSessions`, `LiveSessionView`, `LiveSignal`, `LiveTicket`, `AudioReceipt` types | Local generated TypeScript | Static contract checking; runtime events/responses are separately validated |
| `Heading`, `Pending`, `QueryProblem`, `Status`, `timeLabel`; `BatchMonitor`, `BrowserCall`, `CallUpdate`, `./live.css` | Local shared/live modules | Shared approved shell/states, preserved batch control, isolated media controller and styling |
| `AudioWorkletProcessor`, `registerProcessor`, DataView/ArrayBuffer | Browser globals, no imports | Audio render-thread conversion and transferable frames; no deprecated main-thread ScriptProcessor |
| `RTCPeerConnection`, MediaStream, AudioContext, AudioWorkletNode, WebSocket, AbortController | Browser globals, no imports | Peer media, capture, events, cancellation and lifecycle |
| `uvicorn`; existing `asyncio` addition in preview | Uvicorn 0.54.0 / stdlib | Bounds WS transport messages/queue and uses Windows selector loop for this preview |
| `pytest`, `TestClient`, `Session`, `Event`, asynchronous helpers and existing signed fixtures | pytest 8.3.5 / FastAPI / SQLAlchemy / stdlib / local | Real HTTP/WS/database authorization tests and controlled inference/backpressure races; tests do not enter application inference |
| Vitest `afterEach`, `expect`, `it`, `vi` | Vitest 5.0.5 | Four new permission/lifecycle/contract/error tests |
| Node `createRequire`, fs promises, `fileURLToPath`, `assert/strict`; Chromium, AxeBuilder | Node 24.18.0 / Playwright 1.64.1 / axe 4.14.0 | Resolve installed test tools, private fixture context, native browser execution and auditable evidence |

Primary references checked during implementation: [getUserMedia permission and
secure contexts](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia),
[AudioWorkletNode](https://developer.mozilla.org/en-US/docs/Web/API/AudioWorkletNode),
[native WebRTC statistics](https://developer.mozilla.org/en-US/docs/Web/API/RTCPeerConnection/getStats),
[FastAPI sockets](https://fastapi.tiangolo.com/advanced/websockets/) and the
[faster-whisper implementation](https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py).
Installed-library execution and native browser tests are the implementation proof;
the documentation alone is not a test result.

## 6. Concepts explained from first principles

**WebRTC:** browsers negotiate how to exchange media using an offer, answer and
network candidates. The application authenticates and relays that setup; native
WebRTC then transports the audio. DTLS establishes keys and SRTP protects the
media. This execution measured connected DTLS and negotiated `audio/opus` at both
receivers. No media server, STUN service or TURN relay was added.

**WebSockets:** an ordered bidirectional event channel keeps consent, connection
and ASR results current. It is not treated as the peer media connection. Socket
closure is also a safety signal: the server removes the room and clients release
their microphones rather than continuing an unmonitored call.

**Opus versus PCM:** Opus is the negotiated compressed peer audio codec. The
analysis copy is raw PCM: signed sixteen-bit samples, 16,000 per second, one
channel, explicitly little-endian. One second is `16000 × 1 × 2 = 32000` bytes.
Known raw PCM avoids accepting arbitrary compressed containers on the new capture
endpoint, and makes ordering and model sampling explicit.

**Consent:** browser microphone permission allows device access; it does not grant
analysis or training rights. Here both participants separately permit analysis,
and either can stop it. Consent revisions act like epochs: an old audio frame or
result from epoch 4 is invalid after revocation advances to epoch 5.

**Backpressure:** if work arrives faster than ASR can consume it, a queue can grow
without bound and turn a live system into delayed playback. This prototype bounds
both browser uploads and server work; it pauses analysis rather than silently
accumulating recordings. Packet counters do not prove transcription quality.

## 7. Data, models, evaluation, security and privacy

Only Windows-SAPI synthetic speech and fictional test identities/reports were
used. The generated microphone WAV is local test material, not a private recording
or an operational benchmark. Existing cached `Systran/faster-whisper-tiny`, revision
`d90ca5fe260221311c53c58e660288d3deb8d356`, ran on CPU/int8. No model was downloaded,
trained, promoted or evaluated for linguistic accuracy. RTX 4060 VRAM was unused
by this adapter; peak VRAM and process-memory use were not measured.

Existing verified auth is enforced before HTTP body parsing. Session membership is
tenant/user-bound, not inferred from an invitation UUID or body actor. WebSocket
tickets are random, one-use, short-lived and never URL query credentials. Enabled
users and authorization expiry are revalidated; capture also checks both users.
Origins are explicit and non-loopback plaintext origins are rejected. Strict DTOs
reject extra fields; binary media on WS terminates the room. Bounded input sizes,
sequence/epoch checks, rate/queue limits and result fencing fail closed.

The tested **loopback HTTP** signaling/capture was not TLS encrypted. Peer media
was encrypted by actual WebRTC DTLS-SRTP. Outside loopback, configure HTTPS/WSS
and approved origins; remote TLS/relay deployment was not executed here. This
distinction is deliberate and must not be described as an all-traffic TLS test.

The application writes no live recording or transcript history to disk, S3 or
PostgreSQL. In-memory text is regex-redacted, with the existing incomplete PII
limitations. Ephemeral consent state is not a durable compliance ledger. The
server cannot prove physical listening, the truth of a browser's media-state
report, or that distinct accounts belong to distinct physical people. Existing
dataset/rights/retention limitations remain, and this flow creates no training
dataset. Logical cleanup does not promise forensic zeroing of native memory.

## 8. Executed tests and actual verification

```powershell
$env:PROJECT28_TEST_ADMIN_URL_FILE='.local/step25_test_admin_url'
$env:PROJECT28_TEST_APP_URL_FILE='.local/step25_test_app_url'
.venv/Scripts/python.exe -m pytest tests/unit tests/security tests/api tests/integration tests/workers tests/llm tests/datasets tests/rag tests/emotion tests/reviews tests/streaming -q --tb=short -rs
.venv/Scripts/python.exe -m pytest tests/streaming -q --tb=short
.venv/Scripts/python.exe -m ruff check src/ services/ tests/ scripts/ stubs/ migrations/ app.py
.venv/Scripts/python.exe -m ruff format --check src/ services/ tests/ scripts/ stubs/ migrations/ app.py
.venv/Scripts/python.exe -m mypy src/ services/ app.py
.venv/Scripts/python.exe -m scripts.export_api_schema
npm --prefix apps/web run api:generate
npm --prefix apps/web run api:check
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
npm --prefix apps/web test
npm --prefix apps/web run build
node tests/frontend/live-call.mjs
```

| Check | Actual final result / exit | Evidence under `evidence/step25-20261031/` |
|---|---|---|
| Full backend regression | **505 passed, 2 skipped**, 192.82 s, exit 0 | `backend-tests.txt` |
| Focused new streaming tests | **21 passed**, 24.19 s, exit 0; included in full suite | `streaming-tests.txt` |
| Two skips | Existing knowledge/pgvector cases lack their separate test DB; no streaming case skipped | Full log names/reasons |
| Ruff / format / strict mypy | Pass; **216 formatted files**, **97 typed files**, exit 0 | `ruff.txt`, `format.txt`, `mypy.txt` |
| Frontend tests | **36 passed / 5 files**, 16.92 s, exit 0 | `frontend-tests.txt` |
| Frontend types, lint, generated contract | Pass, exit 0 | `frontend-types/lint/contract.txt` |
| Both frontend builds | Legacy emotion and workspace builds pass, exit 0 | `frontend-build.txt` |
| Real live-call browser test | **7 compound scenarios**, **11 screenshots**, **11 zero-violation axe scans**, no page errors/overflow | `browser-results.json`, `browser-run.txt` |
| Existing workspace regression | **13 scenarios**, **9 views**, **17 screenshots**, **16 zero-violation axe scans**, no page errors | `workspace-regression/`, `workspace-regression-run.txt` |
| Local real ASR smoke | Four seconds of synthetic PCM → one actual recognized span, offline CPU | `local-asr-smoke.json` |

Security/lifecycle cases include disabled default, missing auth, wrong Origin,
nonmember access, directory scope, one-use/expired tickets, missing mutual consent,
wrong sequence/index/length/MIME, disabled-user socket cleanup, video/unencrypted
SDP rejection, binary/malformed WS rejection, revocation during inference and
bounded queue overflow. Controlled broker tests use a recording/slow stub to
observe admissions and race fencing; the browser and separate smoke use the real
checkpoint. These are explicitly different evidence sources.

The browser test checks native encrypted audio at both receivers, no HTTP audio
without consent or with one-sided consent, actual transcripts from both user
streams, immediate admission denial after revocation, continued peer media,
server room removal, remote playback cleanup and **all acquired native microphone
tracks ended**. A fresh invitation reconnects with unchecked microphone consent.
Navigating away then clears the peer session. Permission-denied and late-permission
cases are unit-simulated; physical OS microphone quality was not tested.

Problems resolved: the controlled analysis checkbox originally waited for a server
echo before showing its new value; local state now updates immediately and server
events reconcile it. Background identity fetching originally unmounted protected
pages; it now preserves an already authenticated call during revalidation. Typed
SDK stubs lacked the supported CPU/offline keywords and were extended explicitly.
WS DTOs were absent from automatic OpenAPI inference and are now published from
their real Pydantic models. Windows Proactor shutdown callbacks produced WinError
10054 during an early browser-close test; the isolated Windows STEP_25 launcher
now uses a selector loop, and the final server stderr is clean. Initial evidence
is retained in `initial-windows-transport-log.txt`. Invalid binary WS frames now
take a deliberate rejection/cleanup path rather than an unexpected text-key error.

## 9. Analytics and quantitative interpretation

Baseline for all transport metrics is **Not measured**: STEP_24 had no browser
media path. Final measured values are in
[transport-metrics.json](evidence/step25-20261031/transport-metrics.json), derived
from real native receiver statistics and HTTP receipts, not reference screenshots.

| Metric | Observed result | Formula / sample / interpretation |
|---|---|---|
| Packet loss | **0 / 597 = 0%** | Sum of two receiver snapshots; lost / (received + lost), one short same-laptop synthetic call; no WAN/network stress evidence |
| Audio concealment proxy | **0 / 521,760 = 0%** | Sum of concealed / received audio samples from those two snapshots; a continuity proxy, not perceptual speech quality |
| PCM continuity | **10 accepted one-second frames**, five per participant | Each stream has sequences 0–4 with no accepted gaps/duplicates; **160,000 samples / 320,000 bytes** admitted |
| ASR path | **2 distinct transcript events from 2 participant streams**, delivered **4 times** | Each event delivered to both browsers; genuine cached-model inference, not synthetic transcript generation |
| Reconnect success | **1 / 1 = 100%** | One controlled new-room reconnect with fresh consent; not transparent network-handoff recovery or a reliability estimate |
| Real ASR smoke | **0.8024 s** for a 4.0 s input | One cached Tiny CPU/int8 adapter invocation including lazy model initialization; not broad model latency/accuracy benchmarking |
| Accessibility | **0 detected violations in 11 live-page scans**, plus 16 existing-view scans | axe WCAG2A/AA and WCAG2.1AA; no full screen-reader study |
| Existing calls-list refresh | p50 **82.42 ms**, p95 **181.39 ms**, n=20 | Warm local sequential UI/HTTP refresh with 3 synthetic records and concurrent test work; includes automation overhead, not a production SLA |
| Workspace emitted build | **1,091,602 raw / 275,547 gzip bytes**, 13 files | STEP_24: 1,018,967 / 264,803; delta **72,635 raw / 10,744 gzip bytes**; includes native-controller UI and validators, not a model download |
| End-to-end ASR latency, physical speech quality, multilingual accuracy, load capacity, GPU peak | **Not measured** | This step establishes transport and an admission path, not production performance or model improvement |

Short local zero-loss samples cannot establish deployment reliability. Partial
windows are intentionally discarded at revocation/end; accepted-frame continuity
must not be described as a complete final-call transcript. Earlier runs had
different counters due to timing; only the final artifact above defines this table.

## 10. Technical questions and answered responses

1. **Why WebRTC for audio?** It provides native low-latency media, codec negotiation,
   jitter handling and encrypted peer transport. The browser already supplies the
   microphone and connection APIs; writing a new media stack would be unnecessary.
2. **Are WebSockets the media call?** No. They relay authenticated setup and
   application events. The remote audio track comes from RTCPeerConnection, while
   the ASR copy is a separately authorized HTTP PCM stream.
3. **Why ask for analysis consent separately from mic access?** Device permission
   allows capture for the conversation. Sending a copy to server inference is a
   different use. Requiring both participants' grants prevents one-sided analysis;
   neither grant authorizes training or permanent recording.
4. **Why use PCM instead of forwarding Opus to ASR?** Known 16 kHz mono PCM is
   directly usable by the model and makes sample ordering explicit. It avoids a
   compressed-container decode path, at the cost of higher bandwidth for this
   bounded local prototype.
5. **Can revocation stop inference already running?** It stops new admission and
   purges queued media immediately. A native CPU call cannot be safely interrupted
   inside a Python thread; its result is fenced by room/consent revision and
   discarded. This limitation is different from allowing new work after revocation.
6. **Does reconnect preserve the prior recording/session?** No recording exists.
   Persistent disconnect ends the room and releases resources. Reconnect creates
   a new room and requires fresh grants; it cannot replay old buffers or tickets.
7. **Is the browser demo equivalent to a call center telephone system?** No. There
   is no SIP/PBX/PSTN gateway or TURN service. Same-laptop direct browser audio is
   proven; real network routing, telephony and production availability are not.
8. **Why not declare zero loss a performance win?** The sample is only two receiver
   snapshots of one short synthetic loopback call. No comparable prior transport
   benchmark, adverse-network study or physical listening test exists.
9. **What is actually encrypted here?** Native peer audio uses measured connected
   DTLS-SRTP. The explicitly local test used HTTP/WS for signaling and the analysis
   copy. Real remote use requires configured HTTPS/WSS and separate validation.

## 11. Decisions, remaining limitations and risks

| Decision / limitation | Reason and next action |
|---|---|
| Single process, eight rooms, ten-minute lifetime | Bounded local prototype; external CLI worker overrides must also honor one-worker deployment; no distributed failover |
| Direct candidates only, no STUN/TURN | No unnecessary external infrastructure or credentials; NAT traversal and remote/mobile networks remain unvalidated |
| Loopback HTTP test, encrypted peer media | Exact loopback-only plaintext origin allowance; HTTPS/WSS remote deployment remains work before production |
| Independent four-second CPU ASR windows | Proves a real authorized path without changing batch models or GPU workloads; no stable partial revisions, silence/quality guarantees or final tail flush |
| Receipt-anchored cross-party alignment | Tracks order exactly within each participant but includes network/browser delay across participants; precision not benchmarked |
| Ephemeral consent/media/text | No persistence or training use; not a durable organizational consent/audit ledger |
| Native inference cannot be forcibly cancelled | Admission/queued work stop and stale results are discarded; CPU work already executing may finish |
| Tested synthetic microphone inputs, unit-simulated denial | Physical microphones, headsets, echo/acoustic quality and real participants require separate testing |
| Bounded queues and bodies, no production ingress/load study | Capacity, abusive request concurrency, long calls, bandwidth and failure distributions are unmeasured |
| Existing bundle/client-directive build warnings | Builds pass; main chunk still exceeds advisory 500 kB, requiring later measured optimization |
| Regex PII redaction and existing corpus/model limitations | No claim of complete anonymization, representative accuracy, benchmark promotion or resolved historical rights/retention issues |

No Ollama workload was stopped or reconfigured. No data migration is needed for
the ephemeral transport; production remains unchanged and opt-in. The two existing
knowledge integration skips remain documented rather than counted as passes.

## 12. Deliverables, completion decision and next handoff

**Decision: PASS WITH LIMITATIONS.** The three STEP_25 gates are implemented and
executed for the local prototype:

- [x] Two authenticated browser users exchange native encrypted audio in both directions.
- [x] Audio reaches a real local ASR path only after mutual analysis authorization;
  denied/revoked/invalid paths are tested.
- [x] End/disconnect/navigation clears session/tickets/buffers and native media tracks.
- [x] Relevant original regression, strict checks, generated contracts and builds pass.
- [x] Actual desktop/mobile screenshots and metrics are recorded, with scope limits.
- [x] Source/Git fingerprints, file/import explanations, questions and runbook exist.
- [x] Progress and persistent limitations updated without claiming model training.

Next eligible: **STEP_26 — Implement stabilized incremental ASR with partial
revisions**, after its own prerequisite review. STEP_26 was not started. It should
reuse the consent/epoch boundary and address hypothesis stabilization, window
boundaries, finalization and measured timing rather than bypassing authorization.
Use [browser-calling runbook](../development/browser-calling.md) for configuration.
Next safe check: `uv run --no-sync pytest tests/streaming -q` with the isolated test
URL environment variables configured. The local built preview is available at
`http://127.0.0.1:8788/workspace/#/live`; private synthetic credentials expire.

## 13. Approved ERP UI design / visual contract verification

Read `design/UI_DESIGN_SYSTEM.md` and `UI_ACCEPTANCE_CHECKLIST.md` and visually
inspected both approved references. Compared actual desktop/mobile live-call
screens to `design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png` as the primary
direction, retaining the existing product branding and shared shell.

The warm-neutral `#F6F6F3` canvas, white rounded cards/sidebar/topbar, dark
`#182820` text, forest `#1D5B49` actions, muted borders and amber caveats match the
approved design. Native controls use the existing focus/keyboard styling. Green
activity pills reflect actual native audio levels; there are no fabricated live
waveforms, performance charts or copied reference metrics. No blue/pink dominant
theme was introduced. Participant cards and statistics stack on mobile; text and
session identifiers wrap rather than overflow.

Compared with original Gradio, this is a separate authenticated browser-call
surface; the original upload/recorded-file batch analysis remains intact. Compared
with STEP_24, `/live` now contains real call setup/media/consent states when enabled,
and still displays a truthful disabled state otherwise. The former batch monitor
is preserved below the call controls. Status, event absence, errors, backpressure,
speaker playback, End and new-room reconnect are real controls, not placeholders.

Actual screenshots:

- [Setup 1440](evidence/step25-20261031/live-setup-1440.png), [1280](evidence/step25-20261031/live-setup-1280.png), [1024](evidence/step25-20261031/live-setup-1024.png), [390](evidence/step25-20261031/live-setup-390.png)
- [Call without analysis](evidence/step25-20261031/two-party-call-analysis-off.png), [one-sided consent](evidence/step25-20261031/one-sided-analysis-consent.png)
- [Authorized real ASR desktop](evidence/step25-20261031/authorized-local-asr-desktop.png), [mobile](evidence/step25-20261031/authorized-local-asr-mobile.png)
- [Analysis revoked, call continues](evidence/step25-20261031/analysis-revoked-call-continues.png), [ended/cleared](evidence/step25-20261031/call-ended-session-cleared.png), [fresh reconnect](evidence/step25-20261031/reconnected-fresh-consent.png)

All eleven live screenshots have zero detected axe violations and no horizontal
overflow. Existing capability regression adds seventeen screenshots and sixteen
zero-violation scans. Visible/accessibly matched labels, native keyboard controls,
reduced-motion browser settings and actual small-screen layouts were checked.
Full assistive-technology and human listening studies remain unmeasured. The
intentional design differences are functional participant/transport controls and
truthful experimental transcript states in place of mock sales/analytics content.
