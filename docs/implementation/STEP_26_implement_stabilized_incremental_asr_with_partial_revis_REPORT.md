# STEP_26 — Implement stabilized incremental ASR with partial revisions

**DONE — PASS WITH LIMITATIONS** for the local incremental adapter and its three
acceptance gates. Owner: ML / Platform integration (Codex). Date: 2026-10-31,
Africa/Casablanca. Windows 11, PowerShell, uv-managed Python 3.12.15, Node 24.18.0,
Chrome and isolated local PostgreSQL. Branch `feature/project28-foundation`;
working HEAD `a37e4634af1d2947fc3c548d54e62bda0b0daf89`; pinned original upstream
`fed4b610742c1337147281fcec8f2cdcc0a79be5`.
No model/package download, training, promotion, production migration, public
deployment, push or commit-date modification occurred. Existing Ollama was not
stopped or reconfigured. Commit scheduling still requires exact dates; the user's
reply confirmed intent but supplied no calendar dates, so none were invented.

## 1. Goal, prerequisites and completed work

The live path now produces replaceable provisional hypotheses and immutable final
rows instead of appending independent four-second recognition blocks. It detects
speech boundaries, preserves participant/sample context, decodes overlapping
windows, assigns revision IDs, reconciles boundary context and finalizes on silence
or an explicit authorized request. A transient decoder failure gets one bounded
retry; persistent failure stops analysis with a clear user message.

Read the master instructions, STEP_INDEX, full STEP_26 prompt/template, preceding
STEP_25 report, retained limitations, UI design system/checklist and both approved
reference images. Inspected the existing streaming broker, ASR adapter, auth/capture
routes, frontend controller, generated contracts, tests and pinned upstream batch
transcription. STEP_25 supplies real WebRTC audio, authenticated participant-bound
sessions, consent epochs and cleanup. Its research limitations remain prerequisites
for interpreting this work, not proof of production readiness.

Executed deterministic algorithm tests, real signed HTTP/WS tests, a cached local
Whisper replay, paced 1/2/4-source load cases and a two-browser native-media test.
The original Gradio/batch path, QA weighting, reports and STEP_24 review workflow
are preserved. Whisper is still an offline decoder invoked on bounded chunks;
there is no native streaming decoder, new training, assistant logic or multilingual
accuracy improvement claim.

## 2. Actual upstream versus upgraded implementation

| Feature | Original pinned upstream | Before STEP_26 | STEP_26 modification / symbols | Compatibility |
|---|---|---|---|---|
| Recognition | `src/agents/transcription.py::run_transcription` processes an intake file using faster-whisper; upstream already requests VAD, word timestamps and disabled previous-text conditioning | Separate live `LocalWhisper` decoded independent four-second PCM blocks | `transcribe_words`, `recognize_words`, `SpeechWindows`, `Reconciler` add state to the live adapter | Batch agent and its existing VAD are unchanged |
| Speech boundaries | Batch decoder VAD operates within file analysis | Live fixed-duration blocks, no live VAD state | 20 ms energy frames, onset/pre-roll/hangover and explicit bounded utterance windows | Does not claim to improve upstream VAD accuracy |
| Live hypotheses | No upstream browser revision protocol | Each live result appended to UI | `TranscriptRevision`, keyed `applyTranscript`: provisional/failed/final replacements | Final text remains available in legacy `segments`; provisional consumers use new contract |
| Window overlap | No continuous browser reconciliation in upstream | Independent blocks could cut words; tails discarded | Timed word ownership, context holdback, normalized timed boundary deduplication | Original preprocessing/reconciliation modules untouched |
| Speaker context | Batch source/diarization behavior | Authenticated microphone participant identity | Separate window/reconciler state per participant and consent epoch | No new physical-speaker attribution claim |
| Failure recovery | Existing batch failure behavior | Live generic failure notice for a block | Interrupted revision, one retry, then explicit analysis pause; re-enable requires current grants | Existing room/audio authorization and cleanup retained |
| Finalization | Batch completes when file finishes | Live end discards short tail | Authorized participant-only `/finalize` before ending; silence finalizes automatically | End/revocation still discards unfinished audio for privacy |
| API/schema | Upstream has no this browser WS protocol | 40 HTTP paths plus WS schema extension | 41 HTTP paths; additive revision/finalization DTOs and generated validators | Database revision stays `0005_call_review` |

Actual Git stat/name-status artifacts and pre-step source fingerprints are in
[evidence](evidence/step26-20261031/). Ordinary Git diff includes accumulated earlier
tracked edits and omits untracked new directories; it is not a STEP_26-only patch.
`step-files.json` identifies **27 changed/new files** in the fingerprinted source
roots. OpenAPI, CI and documentation changes outside those roots are listed below.
The pinned upstream implementation was inspected directly; its existing word
timestamps/VAD are not falsely described as new functionality introduced here.

## 3. File inventory and interfaces

Repository-relative paths; no source or dataset was deleted.

| File(s) | Created/modified, interface, purpose and validation |
|---|---|
| `ml/asr/__init__.py`, `ml/asr/incremental.py` | New pure window/reconciliation module: `Word`, `Window`, `SpeechWindows`, `HypothesisState`, `Revision`, `Reconciler`, normalization/rendering helpers; deterministic VAD/ownership/revision tests |
| `services/streaming/asr.py` | Adds native word-timing protocol, explicit segment-only compatibility conversion and `LocalWhisper.transcribe_words`; existing `transcribe` interface retained with an eight-second bounded input cap |
| `services/streaming/broker.py` | Per-participant speech/reconciliation state, coalescing scheduler, finalization, revision publication, timing fields and bounded retry/failure policy |
| `services/streaming/contracts.py` | New `TranscriptRevision`, `TranscriptFlush`, `FlushReceipt`; optional revision event payload and retry notice; generated schema verification |
| `services/streaming/routes.py` | New consent/version/member-checked POST finalize endpoint; existing capture checks retained |
| `services/streaming/settings.py` | Explicit pending-window limit 1–4, default four; other live limits remain |
| `stubs/faster_whisper/__init__.pyi` | Adds consumed `Word` protocol and segment `words` metadata; typing only, no runtime SDK replacement |
| `apps/web/src/features/live/transcript.ts` | New typed row reducer: ID/participant/epoch matching, monotonic revisions, final-row protection and 100-row bound |
| `apps/web/src/features/live/transcript.test.ts` | Seven new client cases: partial replacement, stale/duplicate rejection, finals, epochs, recovery, participant identity and bounded repeated text |
| `apps/web/src/features/live/LivePage.tsx`, `live.css` | Provisional/final/interrupted rows, real revision/timing labels, stable keys and explicit own-speech finalization |
| `apps/web/src/features/live/transport.ts` | Finalize request and accurate retry/recovery notices; existing native media/consent lifecycle retained |
| `apps/web/src/lib/api/client.ts` | Adds finalize to existing same-origin write allowlist |
| `apps/web/scripts/generate-api.mjs` | Includes revision/finalize response contracts in reproducible type/runtime generation |
| `generated.ts`, `schema.generated.json`, `validators.generated.mjs`, `validators.generated.d.mts` under `apps/web/src/lib/api/` | Four regenerated artifacts; no handwritten contract divergence |
| `docs/api/openapi.json`, `tests/api/test_api.py` | Regenerated 41-path contract and expected path count |
| `scripts/benchmark_incremental_asr.py` | New bounded local WAV replay, baseline chunks, real word-window inference and paced concurrency measurements; emits explicit conditions and input/model identifiers |
| `scripts/preview_workspace.py` | Allows isolated STEP_26 context/port 8790 and reuses Windows selector-loop launch behavior |
| `tests/streaming/test_incremental.py` | Fourteen pure algorithm/percentile cases, including Unicode and no duplicated overlap ownership |
| `tests/streaming/test_incremental_transport.py` | Three real HTTP/WS finalize/failure-recovery cases using signed identities and isolated PostgreSQL |
| `tests/streaming/test_transport.py`, `conftest.py` | Prior transport/security regressions use explicit voiced fixture samples and configurable bounded-queue test; existing permission/revocation checks remain |
| `tests/frontend/incremental-call.mjs` | Real two-browser audio/ASR test: provisional row survives DOM updates, becomes final, no duplicate IDs, and inherited consent/cleanup/reconnect behavior |
| `.github/workflows/ci.yml` | Explicitly includes new `ml/asr` runtime code in lint, format and strict typing checks |
| `docs/development/incremental-asr.md`, `browser-calling.md` | New current algorithm/runbook and follow-on note on the historical four-second description |
| STEP_25 report follow-on note; this report, `PROGRESS.md`, `CURRENT_LIMITATIONS.md` | Preserve historical results, document current behavior and next dependency |
| `docs/implementation/evidence/step26-20261031/` | Actual check logs, test results, input/model IDs, replay/load metrics, overlap comparison, screenshots, source/Git/bundle evidence |

Private `.local` URLs, signed context, generated WAVs and helper harnesses remain
execution material, not distributable credentials. No dependency pin or package
lock changed. Original frontend/Gradio and STEP_24 correction source are preserved.

## 4. Important code, functions and algorithms

**`SpeechWindows.push`.** Require one contiguous second of mono PCM16LE. Convert
int16 to normalized float32, reshape into fifty 20 ms frames and calculate RMS.
Three voiced frames trigger onset; retain up to 200 ms of pre-roll. Thirty quiet
frames end a turn after 600 ms silence. Initial silence keeps only the pre-roll
ring and schedules no recognition. The threshold, 0.015, is a documented heuristic,
not a learned speech/noise classifier or proof of speech.

**Partial/forced windows.** Offer a partial every two seconds of active speech.
At eight seconds of buffered context, finalize ownership only through one second
before the window ends. Retain one second of already-owned context plus the
unowned tail for the next turn. The first full chunk owns seven seconds; later
full chunks normally own six because both leading context and trailing holdback
occupy the eight-second window. Each turn receives a fresh UUID. Windows overlap;
their final ownership intervals do not. `flush` finalizes only the current active
turn and is idempotent until more speech arrives.

**`LocalWhisper.transcribe_words`, `WordASRPort`, `recognize_words`.** The real
adapter requests native word timestamps and disables previous-text conditioning.
It loads only an existing local model, on CPU/int8 with four threads, and accepts
at most eight seconds. Invalid/zero-duration words are omitted and output is
bounded. Injected older segment-only ports still work through token interpolation;
their output is explicitly labeled `interpolated`, not passed off as model timing.
The legacy segment method remains usable and is measured separately as a baseline.

**Ownership and `Reconciler.apply`.** Add the window's original sample offset to
native word times. Keep only words whose midpoint belongs to this turn's owned
interval, and clamp the exposed endpoints. Compare an overlapping timed boundary
prefix to up to twelve previous final tail tokens after Unicode/case/punctuation
normalization. Remove matched context only when timing also overlaps or is within
the small boundary tolerance; do not remove an arbitrary later repeated phrase.
Invalid/nonfinite/out-of-window words never become public transcript text.

**Revision state machine.** Each utterance has a revision counter and latest words.
Changed partial text replaces its earlier hypothesis, so `transcrip-` followed by
`transcription` is one row, not two appended fragments. Identical partial text is
suppressed, but finalization always emits a state transition. A finalized ID cannot
be rewritten by a late result. Consecutive normalized prefix agreement is measured
as a diagnostic; all provisional text remains revisable until a final boundary.
This is not a claim to implement the published LocalAgreement-2 algorithm.

**`LiveBroker.schedule` and coalescing.** One inference worker remains active.
Pending work is bounded to four windows; a newer snapshot for the same turn replaces
an obsolete queued partial, without replacing a queued final with a partial. Queue
overflow still pauses analysis and clears pending media. The initial two-slot
configuration rejected a synchronized four-source burst despite acceptable local
decode times; the measured four-slot configuration accepted all frames in the
short replay. It is a bounded admission improvement, not unlimited concurrency.

**`process`, `publish`, failure handling.** Decode off the event loop, then recheck
room existence, consent epoch and allowed state before publishing. Redact the
assembled text before constructing public DTOs. Include sender ID, utterance ID,
revision/state, source window/ownership times and measured queue/decoding timing.
Only final text is copied into legacy `segments`. A failure publishes an
interrupted revision and retries once. A successful retry advances the same ID;
a second failure turns analysis off with an explicit message. A queued newer
snapshot can supersede obsolete retry work. Raw exception details are not exposed.

**Finalization endpoint.** POST `/api/v1/live/sessions/{id}/finalize` accepts only
the current consent revision and verified participant identity. It rechecks mutual
analysis permission and both enabled users, then flushes only that participant's
track. Missing permission, wrong participant or stale epoch is denied. No flush is
performed after end/revocation. Ending still discards unfinished material, and a
manual cut can occur mid-word; final status is not human verification.

**`applyTranscript` and UI.** Match participant plus utterance ID; accept only a
newer revision in the current consent epoch. Replace that row in place, ignore
duplicate/out-of-order updates, and protect final rows. Epoch/end changes clear
rows. Keep at most 100 recent rows and retain repeated speech with distinct IDs.
Stable React keys preserve the DOM row during updates, verified by the browser
test retaining an element handle through provisional → final. Text growth can
still change row height; the implementation does not force automatic scrolling.

**Metrics.** `ready_to_event_ms` starts when a completed server-side window is
scheduled and ends during revision construction, before socket transmission. It
includes queue/inference delay but excludes microphone framing, window formation,
network/render latency and later WS delivery. `inference_ms` measures the real
decoder invocation. The benchmark measures both per-window RTF and effective RTF
against unique source duration, so overlap work is not hidden.

## 5. Imports and dependency explanation

No new Python/npm dependency was installed. Existing runtime versions were read
from the environment and saved in `versions.json`: faster-whisper 1.2.1,
CTranslate2 4.8.3, NumPy 2.5.4, FastAPI 0.162.0, Pydantic 2.11.3,
SQLAlchemy 2.0.41, pytest 8.3.5, Ruff 0.11.8 and mypy 2.4.0.

| Actual introduced/relevant imports | Origin | Meaning, location and reason |
|---|---|---|
| `math`, `unicodedata` | Python 3.12 stdlib | Finite word-time validation, nearest-rank percentile calculation and Unicode/case/punctuation matching; no English-only ASCII deduplication |
| `dataclass`, `field`, `replace` | stdlib dataclasses | Bounded word/window/revision records and fresh retry work without mutating an in-flight snapshot |
| `Literal`, `Protocol`, `runtime_checkable` | stdlib typing | Typed state/reason variants and a structural native-word port; enables explicit legacy compatibility instead of assuming word timing exists |
| `uuid4`, `UUID` | stdlib uuid | Per-turn random IDs and validated public identifiers; no client-supplied speaker identity |
| `numpy as np` | Existing NumPy 2.5.4 | Vectorized int16 normalization and 20 ms RMS; already a locked preprocessing dependency |
| `re` | stdlib | Preserve whitespace while splitting an injected segment-only adapter's text into estimated word units |
| `Word`, `Window`, `SpeechWindows`, `Reconciler` | New local `ml.asr.incremental` | Private timed words, bounded source snapshots, live VAD/window state and revision reconciliation |
| `WordASRPort`, `recognize_words`; existing `ASRPort`, `LocalWhisper` | Local streaming ASR | Use native alignment when present and label interpolated compatibility output honestly |
| `TranscriptRevision`, `TranscriptFlush`, `FlushReceipt`; existing event/span DTOs | Local Pydantic contracts | Typed WS hypotheses and authenticated finalize request/response; no schema-less transcript event |
| `redact_pii` | Existing local security module | Redact assembled word hypotheses and replay-report text before public output; regex limits remain |
| Existing `asyncio`, `time`, `Principal`, tenant sessions, FastAPI routing/header/identity symbols | Existing stdlib/local/framework imports | Keep CPU work off-loop, record real timings and preserve session/permission boundaries; no replacement auth system |
| `applyTranscript`, `TranscriptRow`; generated `LiveEvent`, `TranscriptRevision` types | New local TS reducer and generated contracts | Deterministic UI state transitions, source/epoch identity and compile-time shape checking |
| Existing React hooks, `BrowserCall`, `sendResource`, shared UI helpers | React 19.3.1 / local modules | Reuse ephemeral state, native audio lifecycle, safe write allowlist and approved shell; no new state framework |
| `argparse`, `asyncio`, `hashlib`, `json`, `statistics`, `time`, `wave`, `Path` | stdlib benchmark tooling | Bound CLI replay inputs, pace load, fingerprint source, measure actual processing and serialize evidence |
| `LiveBroker`, `LocalWhisper`, `LiveSettings`, `LiveConsent`, `LivePeer`, `Principal` | Local benchmark imports | Exercise the actual scheduler/model/permission state with synthetic participants, distinct from a network benchmark |
| `pytest`, `dataclasses.replace`, existing live HTTP fixtures and helpers | Test-only | Deterministic word/ownership/failure cases and real signed HTTP/WS finalization execution |
| Vitest `expect`, `it`; Node fs/module/url/assert helpers, Chromium and AxeBuilder | Existing test stack | Seven reducer tests and native browser DOM/media/accessibility evidence; not production model imports |
| SDK stub `Word` and `Segment.words` | Local consumed-interface declaration | Describe supported faster-whisper fields for strict typing; no runtime monkey patch or new SDK implementation |

The [faster-whisper source](https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py)
and [official usage documentation](https://github.com/SYSTRAN/faster-whisper)
were checked for native word-timestamp behavior. Runtime execution, not those
references alone, proves the adapter worked. No published streaming-paper latency
or benchmark result is copied as a result from this laptop.

## 6. Concepts from first principles

**Chunked ASR:** the model repeatedly recognizes a growing bounded piece of audio.
It does not carry a native causal decoder state across the whole live call.
Overlapping context reduces boundary damage, but reprocessing costs extra CPU.

**VAD:** a gate estimates where speech starts and ends before deciding when to
recognize/finalize. This implementation uses signal energy with a silence hangover.
It is cheap and deterministic but cannot reliably distinguish speech from music
or recognize every quiet voice. Original batch recognition retains its own VAD.

**Partial/final state:** a provisional hypothesis is editable machine output, such
as `Transcrip-`. The next revision can replace it with `Transcription works.`
without adding another row. Silence, a bounded ownership split or explicit flush
ends that turn; final means the recognition state is closed, not that a human
verified the words. Failures have an explicit interrupted state and recovery path.

**Overlap reconciliation:** windows may both hear the word at their common edge.
Each final turn owns a non-overlapping time range, while matching boundary words
are removed only with supporting time overlap. Later intentional repetition is
kept. Per-participant clocks and independent state prevent one microphone's words
from deduplicating another participant's speech.

**Backpressure:** obsolete partials can be replaced because the latest snapshot
contains the current turn's context. Final work must not be silently replaced by
an interim. The bounded scheduler prevents unlimited delayed audio accumulation.

## 7. Data, models, security, privacy and reliability

All execution used fictional accounts and Windows-SAPI English speech generated
locally. The offline source supplied a known synthetic paragraph; its final
normalized transcript matched that generator text in the recorded one-sample
check. This is not a real human-reviewed call corpus or evidence for French,
Arabic, Darija, accents, noise or telephone audio. A separate longer SAPI phrase
was used in the browser to exercise partial updates and forced/manual boundaries.

Cached `Systran/faster-whisper-tiny`, revision
`d90ca5fe260221311c53c58e660288d3deb8d356`, ran on CPU/int8 with four threads.
No model training or GPU inference occurred; RTX 4060 peak VRAM/process memory
was not measured. Batch model defaults and production inference configuration
remain unchanged. This CPU Tiny checkpoint is transport/algorithm evidence, not
a recommendation to replace previously benchmarked multilingual models.

Existing signed identity, enabled-user checks, exact origins, two-party consent,
sample sequencing, deadlines, ticket binding and epoch fencing remain. Revocation
clears window/reconciliation state and queued work. Late native inference may
finish computing but cannot publish into the changed/ended epoch. Public events
contain redacted text and bounded metadata, not raw word lists or audio buffers.
PII detection remains pattern-based and incomplete; no new training rights arise.

Transport remains the single-worker direct-browser prototype from STEP_25.
HTTP/WS is explicitly loopback-only in the executed preview; remote TLS/TURN/NAT,
telephony, durable consent/audit and production capacity were not added or tested.
Finalized rows remain immutable even if a later model hypothesis would differ.
No finalized ASR row automatically becomes an approved training annotation.

## 8. Tests, exact execution and verification

Executed in the existing uv-managed `.venv`; private test URL files point only to
the newly prepared isolated local database, at unchanged schema revision 0005.

```powershell
$env:PROJECT28_TEST_ADMIN_URL_FILE='.local/step26_test_admin_url'
$env:PROJECT28_TEST_APP_URL_FILE='.local/step26_test_app_url'
.venv/Scripts/python.exe -m pytest tests/unit tests/security tests/api tests/integration tests/workers tests/llm tests/datasets tests/rag tests/emotion tests/reviews tests/streaming -q --tb=short -rs
.venv/Scripts/python.exe -m ruff check src/ services/ tests/ scripts/ stubs/ migrations/ ml/asr/ app.py
.venv/Scripts/python.exe -m ruff format --check src/ services/ tests/ scripts/ stubs/ migrations/ ml/asr/ app.py
.venv/Scripts/python.exe -m mypy src/ services/ ml/asr app.py
.venv/Scripts/python.exe -m scripts.export_api_schema
npm --prefix apps/web run api:generate
npm --prefix apps/web run api:check
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
npm --prefix apps/web test
npm --prefix apps/web run build
node tests/frontend/incremental-call.mjs
.venv/Scripts/python.exe -m scripts.benchmark_incremental_asr --audio .local/step26-browser-speech.wav --model-file .local/step25_asr_path --output docs/implementation/evidence/step26-20261031/asr-benchmark.json
```

| Check | Actual outcome | Evidence under `evidence/step26-20261031/` |
|---|---|---|
| Full backend regression | **522 passed, 2 existing skips**, 136.30 s, exit 0 | `backend-tests.txt` |
| Streaming cases | 21 previous cases plus 14 pure incremental/percentile and 3 finalize/recovery cases, all included in the full passing run | Test source and full log; earlier focused run before the final percentile case had 37 passes |
| Skips | Two existing knowledge/pgvector cases lack their separate configured test DB; no incremental case skipped | Full log names/reasons |
| Ruff / format / strict typing | Pass; **221 formatted files**, **99 typed files**, exit 0 | `ruff.txt`, `format.txt`, `mypy.txt` |
| Frontend component/client tests | **43 passed in 6 files**, 12.90 s, exit 0 | `frontend-tests.txt` |
| Frontend type/lint/generated contract | Pass, exit 0 | `frontend-types.txt`, `frontend-lint.txt`, `frontend-contract.txt` |
| Both frontend builds | Legacy emotion and workspace production builds pass, exit 0 | `frontend-build.txt` |
| Native browser incremental call | **7 compound scenarios**, **12 screenshots / 12 zero-violation axe scans**, no page errors/overflow | `browser-results.json`, `browser-run.txt` |
| Existing workspace regression | **13 scenarios / 9 views**, **17 screenshots / 16 zero-violation scans**, no page errors | `workspace-regression/`, `workspace-regression-run.txt` |
| Real checkpoint replay/load | Baseline chunks, incremental windows and paced 1/2/4-source cases executed; no room/ticket state retained after each load | `asr-benchmark.json` |
| Actual final overlap check | Non-overlapping ownership and exact normalized match to the known SAPI paragraph, n=1 | `overlap-execution.json` |

Backend cases exercise silence/no recognition, pre-roll, bounded long speech,
contiguous sample clocks, silence/manual endpoints, context ownership, mid-word
and punctuation replacement, final immutability, suppressed duplicate partials,
legitimate repeated speech, invalid word times, Unicode matching, transient retry,
persistent-failure revocation, stale finalize epochs and idempotent finalization.
The inherited consent/Origin/ticket/disabled-user/binary-frame/cleanup tests remain.

The browser retains an element handle to a provisional row, invokes the real
finalize endpoint and verifies that the same element becomes final with a newer
revision. It asserts unique row IDs, actual native peer audio/local checkpoint
events, two-participant permission checks, revocation, native track cleanup and
fresh-room reconnect. Algorithm fixtures use controlled words; browser/replay
execution uses the actual cached model. They are not interchangeable evidence.

Problems and solutions: the first load with two pending slots paused one room at
four synchronized sources; a bounded four-slot scheduler passed the rerun. The
initial percentile estimator was unsuitable for very small samples and is now
nearest-rank p95 with a regression test. `asr-benchmark-initial-cap2.json` is retained
as superseded diagnostic evidence; its percentile fields are not final results.
Very large bytes-valued pytest IDs hit Windows fixture/path handling, so tests now
use short descriptive IDs. Long-window test expectations were corrected to account
for both leading context and trailing holdback. These corrections are reflected
in the final passing suite, not described as model improvements.

## 9. Analytics and quantitative report

Measured on this laptop, cached Tiny CPU/int8, warm model for replay timings.
Offline source: 12 seconds including padded silence. Load cases pace one-second
frames through the actual broker without HTTP/WebRTC overhead. Browser measurements
use real Chrome WebRTC plus model processing; these remain short synthetic tests.

| Metric | Baseline → observed | Definition, sample and interpretation |
|---|---|---|
| Browser partial ready-to-event latency | STEP_25 did not record this metric → p50 **517.98 ms**, p95 **1407.03 ms**, n=7 provisional updates | Current server window-ready to event construction, excluding microphone framing, formation delay, network/render time; not an end-to-end SLA |
| Revision stability | Append-only baseline had no revision IDs → **9 updates for 4 utterances**, maximum revisions **4, 2, 2, 1** | Count from one receiver to avoid double-counting delivery; includes final transitions. Two utterances visibly progressed provisional → final; unfinished turns were later discarded by revocation |
| Incremental effective RTF | Baseline four-second chunks **0.1292** → incremental **0.2531** | Total measured inference seconds / unique 12-second source, warm CPU; overlap/word alignment increases compute rather than making the model faster |
| Final overlap execution | Not measured in live baseline → **4 final ownership intervals**, no overlap, normalized generator-text match | One SAPI English paragraph, not representative ASR accuracy; detailed text/source SHA in `overlap-execution.json` |
| One-source load | **12/12 frames accepted**, no pause/rejection | 12 s paced replay, partial ready-to-event p50 **439.72**, p95 **442.01 ms**, n=2; one coalesced pending update |
| Two-source load | **24/24 accepted**, no pause/rejection | 12 s, p50 **655.28**, p95 **930.06 ms**, n=4; two coalesced updates |
| Four-source load | **48/48 accepted**, no pause/rejection | 12 s, p50 **913.76**, p95 **1367.17 ms**, n=5; seven obsolete pending updates coalesced, observed pending peak four |
| Buffer observation | Peak tracked PCM ring total **279,040 bytes** in four-source case | Sum of participant rings sampled by load harness; excludes active/queued snapshots, model and browser memory, so it is not total peak RAM |
| Cleanup | All load rooms/tickets cleared; browser ended native tracks | Execution checks, not forensic memory zeroing |
| Existing calls-list refresh | p50 **33.51**, p95 **47.72 ms**, n=20 | Warm synthetic local UI regression; not ASR latency or a production performance comparison |
| Build output | STEP_25 **1,091,602 raw / 275,547 gzip bytes** → **1,114,538 / 277,628**, 13 files | +22,936 raw / +2,081 gzip bytes; existing main-chunk/client-directive warnings remain |
| Real-call WER/CER, multilingual accuracy, broad finalization lag, GPU peak | **Not measured** | No representative permissioned human corpus, physical microphone study, adverse-network/load distribution or GPU experiment in this step |

Median p50 and nearest-rank p95 are calculated from actual samples. Small n means
large uncertainty; no confidence interval or production concurrency claim is made.
Latest-window coalescing deliberately omits obsolete interim decodes; it does not
hide audio recording loss. Readiness is a scheduling timestamp, not the instant
the person began speaking. The two-second partial stride is a configured earliest
opportunity and is not itself a measured two-second end-to-end guarantee.

## 10. Questions with detailed answers

1. **Does Whisper natively stream here?** No. A finite-window decoder is invoked
   repeatedly with new context. The adapter supplies window timing, revision IDs,
   ownership and finalization. Native streaming-state latency claims would be false.
2. **Why version partial hypotheses?** A later recognition can complete a word or
   change punctuation. The participant/utterance ID identifies the same row and a
   higher revision replaces it. Appending both hypotheses would duplicate speech;
   accepting older revisions would move the UI backward.
3. **What makes a final stable?** A boundary closes its owned interval and both
   server/client reject later rewrites of that ID. This is protocol stability,
   not proof of linguistic correctness or human approval. Corrections still belong
   in the separate reviewed annotation workflow.
4. **Why measure finalization lag separately?** An assistant should rely on stable
   information, not a rapidly changing fragment. This step measures queue/decoder
   timing and revision transitions; comprehensive capture-to-final/render latency
   and real-call lag distributions remain unmeasured for later evaluation.
5. **How does overlap avoid duplication without deleting repeated speech?** Ownership
   chooses which turn owns a timed word; normalized suffix/prefix matching removes
   repeated boundary context only when timestamps also support it. A later `No.
   no!` with distinct timing is preserved, as tested.
6. **Why use energy VAD if the batch pipeline already uses VAD?** The new boundary
   state runs cheaply over incoming PCM without changing batch behavior or adding
   a model download. It is a prototype choice with explicit quiet/noisy-speech
   limitations, not an accuracy upgrade over the batch VAD.
7. **What happens after decoder failure or revocation?** One transient failure is
   retried with an interrupted status; success advances the same row. A second
   failure pauses analysis. Revocation/end clears queues and invalidates results
   regardless of retries; an in-flight native call may finish but cannot publish.
8. **Why does effective RTF increase despite earlier partials?** Repeated overlapping
   inference and word alignment perform more work per unique audio second. Earlier
   provisional visibility trades compute for responsiveness; neither the measured
   RTF nor one exact synthetic paragraph proves broad model improvement.

## 11. Decisions, limitations and remaining risks

| Decision / remaining limitation | Practical implication / next action |
|---|---|
| Energy VAD with fixed threshold | Quiet speech, music and noise remain unvalidated; calibrate/compare on representative authorized calls before production |
| Provisional agreement is diagnostic | Only finals are committed; no published LocalAgreement-2 or native decoder implementation is claimed |
| Word timing and bounded ownership | Model alignment errors can still lose/misassign boundary words; executed no-duplicate cases are not a universal accuracy guarantee |
| Silence/forced/manual finalization | Manual cuts can split a word; end/revocation still discards unfinished tails; no automatic post-end inference |
| Four pending windows, one CPU worker | Small 1/2/4-source load passed; longer/model-heavy/adverse-network capacity and production ingress are unmeasured |
| Recent state/display bounds | Server retains recent reconciliation state and UI shows 100 rows; this is not a durable full-call transcript store |
| Immutable finals | A later better hypothesis cannot silently rewrite a final; human correction and re-evaluation remain separate |
| Inherited local-transport restrictions | Single ASGI worker, direct candidates, loopback HTTP test, no TURN/SIP/PBX/PSTN or remote deployment validation |
| Model/data/PII restrictions | No human-label quality, French/Arabic/Darija improvement, training, promotion or complete anonymization established |
| Browser layout/assistive technology | Stable DOM keys and automated checks passed; text growth can change height, and a complete human/AT study is not done |

Existing build warnings and the two unrelated pgvector integration skips remain.
Historical Step 25 results were preserved with a follow-on note instead of being
rewritten to imply these features existed earlier. No prior dataset, rights,
retention, model-evaluation or deployment limitation is closed by this test suite.

## 12. Completion decision, deliverables and next handoff

**PASS WITH LIMITATIONS.** All three STEP_26 gates were implemented and executed:

- [x] Final windows have non-overlapping ownership and duplicated context is removed
  in deterministic cases and the recorded real-model synthetic replay.
- [x] Live UI replaces revisions in one keyed DOM row, protects finals and rejects
  stale/out-of-order data; actual browser provisional → final execution passed.
- [x] Transient failures recover once with an explicit state; persistent failure
  stops analysis and exposes a safe recovery message.
- [x] Original regressions, generated contracts, strict checks and both builds pass.
- [x] Real replay/concurrency measurements and screenshots are recorded with limits.
- [x] Complete import/file/code explanation, answered questions, runbook and tracker
  updates are provided without claiming training or representative accuracy.

Next eligible: **STEP_27 — Add grounded real-time agent assistance**, after reading
its own prerequisites. STEP_27 was not started. Future assistance must distinguish
provisional text from final state, preserve participant/consent epochs, and must not
treat a stable machine hypothesis as human-verified truth. Use
[incremental ASR runbook](../development/incremental-asr.md) for launch and replay.
Next safe command: `uv run --no-sync pytest tests/streaming -q` with isolated test
URL environment variables configured. Current local preview: port 8790, `/workspace/#/live`.

Milestone commit work remains uncommitted pending an exact user-supplied date
schedule. No adjusted dates or published-history rewrites were applied.

## 13. Approved ERP UI design / visual contract verification

Compared the implemented page to primary
`design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png` and the secondary approved ERP
reference after reading the design guide/checklist. Inspected actual provisional
desktop and final/provisional mobile captures. The rounded light sidebar/topbar,
white cards, warm `#F6F6F3` canvas, dark `#182820` text, forest `#1D5B49` controls
and restrained amber provisional statuses remain consistent. Final labels use
light green; no dominant blue or pink was added.

The UI uses actual utterance/revision/timing metadata, shows model versus estimated
word timing honestly, and keeps experimental/synthetic banners visible. It does
not fabricate waveform, confidence, training or accuracy metrics. Existing native
audio controls, call consent, End/reconnect and batch monitor remain. The original
Gradio surface is preserved; only the integrated live transcript changed.

Actual evidence:

- [Setup 1440](evidence/step26-20261031/live-setup-1440.png), [1280](evidence/step26-20261031/live-setup-1280.png), [1024](evidence/step26-20261031/live-setup-1024.png), [390](evidence/step26-20261031/live-setup-390.png)
- [Provisional row](evidence/step26-20261031/provisional-revision-desktop.png)
- [Final/updated desktop](evidence/step26-20261031/authorized-local-asr-desktop.png), [mobile](evidence/step26-20261031/authorized-local-asr-mobile.png)
- [Consent off](evidence/step26-20261031/two-party-call-analysis-off.png), [one-sided consent](evidence/step26-20261031/one-sided-analysis-consent.png), [revoked](evidence/step26-20261031/analysis-revoked-call-continues.png)
- [Ended/cleared](evidence/step26-20261031/call-ended-session-cleared.png), [fresh reconnect](evidence/step26-20261031/reconnected-fresh-consent.png)

Twelve live-page axe scans and sixteen existing-view scans found zero tested
WCAG-rule violations; screenshots showed no horizontal overflow. Visible labels,
native keyboard controls, focus styling and reduced-motion settings were retained.
Intentional differences from the reference are functional transcript states and
finalization controls instead of mock sales charts. There is no claim of full
screen-reader certification or perfectly fixed text height during recognition.
