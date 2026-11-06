# STEP_02 upstream source review

Inspected the clean `main` clone at
`fed4b610742c1337147281fcec8f2cdcc0a79be5` on 2026-10-24. Source facts below
describe that revision, not an assertion about hosted provider availability today.
The [87-file manifest](baseline/provenance.json), [tracked tree](baseline/tracked-tree.txt)
and [56-file Python declaration/import index](baseline/python-symbols.json) provide
exact byte hashes and source locations. There are 33 Python files under `src/`,
including nine empty package initializers; 24 contain code. The 22 Python files
under `tests/` include test helpers/initializers and are not a test-case count.

## Entry points, responsibilities and contracts

| Source / symbols | Inputs → outputs and important behavior |
|---|---|
| `app.py` | Import-time configuration → SQLite engine/schema, Whisper singleton, compiled graph, audit object and Gradio `demo`; the `__main__` block launches port 7860 |
| `src/utils/config.py`: `Config`, `load_config` | Environment and dotenv → frozen configuration; default OpenAI configuration requires its API key; model size defaults to tiny |
| `src/utils/llm_factory.py`: `get_llm` | Provider/model/timeout → LangChain client; imports provider implementations lazily; unknown providers fall through to OpenAI |
| `src/utils/audio.py`: `detect_audio_format`, `validate_audio_file`, `extract_audio_properties` | Bytes/name → detected container, size validation and audio metadata; WAV/MP3/FLAC/M4A supported; errors become intake failures |
| `src/utils/formatters.py` | Structured dictionaries/time values → Markdown and timestamp strings for UI |
| `src/agents/intake.py`: `run_intake` | `AudioInput` → `IntakeResult`; size/duration/format checks, metadata PII detection, temporary audio file and new call UUID |
| `src/agents/transcription.py`: `run_transcription`, `SpeakerDiarizer` | Valid intake → cached or faster-whisper transcription, English language, confidence heuristic and Agent/Customer heuristic labels; no pyannote |
| `src/agents/summarization.py`: `run_summarization` | Transcript/config → typed `SummaryResult` via structured LLM output with retries |
| `src/agents/qa_scoring.py`: `run_qa_scoring`, `DIMENSION_WEIGHTS` | Transcript and optional summary → dimension scores/compliance flags; overall score recomputed using weights 0.15/0.20/0.30/0.20/0.15 |
| `src/agents/report.py`: `compile_report`, `persist_report`, `generate_report_json`, `generate_report_pdf` | Typed stage outputs → `CallReport`, SQLite row, JSON string or PDF bytes |
| `src/graph/state.py` | Pydantic models for audio/intake/transcript/summary/QA/report; UUID call IDs, confidence 0–1, dimension scores 1–5, constrained severity/status fields |
| `src/graph/workflow.py`: `PipelineState`, `build_workflow`, `compile_workflow` | Partial typed state/config → eight-node graph with success, error and supervisor terminal paths |
| `src/graph/edges.py`: routing functions | Intake validity → transcribe/error; transcription → summarize route; critical QA flag → supervisor rather than report |
| `src/security/injection_detector.py`: `detect_injection` | Transcript string → detection record with matched regex names; 22 configured pattern pairs |
| `src/security/pii_redactor.py`: `redact_pii`, `PIIRedactionResult` | String → replacement text plus detections containing original matches/offsets; four pattern families, not comprehensive multilingual PII recognition |
| `src/security/audit.py`: `AuditLogger.log` | Call/action/user/details → inserted audit row through transactional session |
| `src/database/models.py` | SQLAlchemy `CallRecord`, `AuditLogEntry`, `TranscriptionCache`; text JSON fields and unique call/audio-hash keys |
| `src/database/connection.py`: `get_engine`, `init_db`, `get_session`, `session_scope` | SQLite path/optional key → engine/schema/sessions; context manager commits or rolls back and closes |
| `src/services/pipeline.py`: `process_call`, `PipelineResult` | Filepath or legacy microphone array + metadata → graph invocation, persisted report, UI strings and temporary download paths; failure result has an error string |
| `src/services/history.py`: `list_calls`, `get_call_detail` | Engine/call UUID string → table dictionaries or detail dictionary/None; UI-independent read layer |
| `src/services/observability.py`: `get_observability_dashboard` | Engine/project name → metrics Markdown, tracing status Markdown and recent audit rows |
| `src/ui/app_builder.py`: `build_app` | Config/workflow/engine/audit → `gr.Blocks` with Analyze Call, All MP3 History and Observability tabs |
| `src/ui/tabs/analyze.py` | Upload/microphone filepath, caller and department → processing/error/success state, transcript/summary/QA and PDF/JSON controls |
| `src/ui/tabs/history.py` | Load/tab/row events → refreshed rows and selected call detail; source archived before later visual redesign |
| `src/ui/tabs/observability.py` | Load/tab event → aggregated metrics/status/audit controls |

The first column accounts for all 24 nonempty `src/` modules. Declarations in
`baseline/python-symbols.json` include nested functions and methods with line
numbers; this is a syntax inventory, not an inferred runtime call graph.

## Architecture and data flow

`app.py` bootstraps services, then UI callbacks call `process_call`. The graph
validates intake, transcribes, checks injection, redacts full text and each segment,
summarizes and then scores QA. Normal and supervisor branches compile reports;
the service persists/downloads the result. SQLite stores call records, audit rows
and content-hash transcription cache. External LLM clients are behind the provider
factory; faster-whisper is local inference. Pydantic models validate structured
outputs; there is no implemented training pipeline or React/FastAPI boundary.

`docs/architecture.md` is a useful existing map, but its narrative is not used as
proof when code differs: the service layer directly handles audit/persistence,
summarization and QA are sequential, and raw transcription may be cached before
graph redaction. No separate ADR directory was found. STEP_01's decision appendix
and the existing architecture document form the preceding decision record.

## README claims compared with source

| Claim / source reference | Source inspection and conclusion | Action in this step |
|---|---|---|
| README:96, “7 nodes” | `build_workflow` registers eight nodes, including `error_step` and `supervisor_step` | Record documentation discrepancy; preserve upstream README as evidence |
| README:387, set `GRADIO_SERVER_PORT=7861` | `app.py:36` passes explicit `server_port=7860`; source does not read this variable | Document source-level conflict; alternate port not runtime-validated here |
| README:69/101, injection checked “at ingestion” | `workflow.py` checks transcript after transcription, before redaction/LLM; intake only scans metadata PII | Clarify execution order; do not imply audio ingress scanning |
| README:100, PII before LLM | Graph redacts full/segment text before the LLM, but transcription cache is saved in `run_transcription` before graph redaction | LLM-boundary claim supported by topology; at-rest privacy remains incomplete |
| README:99, identical audio “returns instantly” | Cache hashes only audio content and stores unredacted `TranscriptionResult`; no model/config version or TTL participates in the cache key | Cache exists, but instant service-wide completion and valid cross-model reuse are not proved |
| README:69/104, append-only audit | `AuditLogger.log` inserts rows; ORM schema has no trigger or permission preventing update/delete | Append-only by writer convention, not tamper-resistant enforcement |
| README:67/68, CPU/GPU latency and provider prices/free tiers | Static source cannot establish wall-clock performance, today's pricing, quotas or model availability | Archived claims only; not adopted as measured/current facts |
| README:268, soft cost ceiling | `MAX_COST_PER_CALL_USD` enters `Config`; inspection finds no runtime charging/quota enforcement | Configuration value, not a hard spending limit |
| README:110–113, no real diarization/auth/streaming | `SpeakerDiarizer` uses English text/gaps; UI is batch, no tenant authentication; `language="en"` in ASR | Supported limitation; multilingual neural platform remains future work |
| README:348, ten sample MP3s | Ten tracked `.mp3` paths exist; no call content or training rights were inspected | Presence verified; scenario labels, consent and training permissions unverified |
| README:21/423, 109 unit/security plus four integration tests | Fresh clean-clone regression execution confirms 113 tests; fixture/helper module count differs from case count | Execution results retained separately from file counts |

These are source-review findings, not new runtime or security fixes. Full typing
debt, absent host FFmpeg/editor launchers and the existing async warning remain
from STEP_01. No upstream source or README was edited by STEP_02.

## Privacy and reliability limitations for later work

Retain the original MIT notice. Presence of sample audio does not establish
permission to use it for training. This step hashes committed blob bytes but
does not decode or transcribe bundled audio. No `.env`, ignored database,
credential store or user call recordings are copied into the archive.

Raw transcript cache, heuristic PII coverage, ordinary SQLite audit storage,
conditional SQLCipher pragma use without proof of encryption, Windows temporary
file lifecycle (`"/tmp/"` cleanup check) and import-time model initialization need
later scoped review. They were not changed as a side effect of provenance work.
The cloned snapshot proves Git integrity and source identity, not safety of every
dependency, authenticity of the upstream author or success of real model inference.

## Baseline UI evidence

[Source evidence](baseline/source-evidence.md) archives exact committed `app.py`,
README, LICENSE and every non-symlink `src/ui/` blob. It shows the original Gradio
Soft theme, three tab labels and the upload/history/observability interactions.
This satisfies STEP_02's explicit screenshot **or source evidence** option.
No app import/server/model launch or browser screenshot was attempted. The original
Soft theme/README blue badge metadata are baseline facts, not approved new ERP
styling. The Commercially reference applies to future frontend changes; this step
introduces no frontend, API, routes, theme tokens or accessibility changes.
