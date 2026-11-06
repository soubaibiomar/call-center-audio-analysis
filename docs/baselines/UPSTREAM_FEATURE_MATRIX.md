# STEP_06 original feature matrix

Date: 2026-10-24. Source pinned original `fed4b610742c1337147281fcec8f2cdcc0a79be5`,
working HEAD `a37e4634af1d2947fc3c548d54e62bda0b0daf89` plus documented changes.
This is a source inventory plus actual runtime outcome, not a working-demo claim.

| Feature | Actual source | Source finding | This real run |
|---|---|---|---|
| App/bootstrap | `app.py`, `src/utils/config.py::load_config` | Config → SQLite → Whisper → graph → Gradio | FAILED at configuration before server/model startup |
| Upload/microphone analysis | `src/ui/tabs/analyze.py`, `src/services/pipeline.py::process_call` | Filepath input, metadata, processing/error/success state | NOT EXECUTED |
| Intake validation | `src/agents/intake.py::run_intake`, `src/utils/audio.py` | Format/size/duration checks, temporary audio file | Source inspected; existing synthetic tests passed, no sample run |
| ASR | `src/agents/transcription.py::run_transcription` | faster-whisper, fixed English, CPU fallback, heuristic confidence | NOT EXECUTED; no model downloaded |
| Speaker labels | `SpeakerDiarizer.assign_speakers` | Two-label text/gap heuristic, not pyannote neural diarization | No new diarization result measured |
| Injection/PII | `src/graph/workflow.py`, `src/security/` | Injection then full/segment redaction before LLM | Source inspected; security fixtures passed earlier, no real call |
| Summary | `src/agents/summarization.py::run_summarization` | Structured hosted LLM output with retries | NOT EXECUTED |
| Weighted QA | `src/agents/qa_scoring.py` | Five dimensions, Python weighted total, critical routing | NOT EXECUTED on audio |
| Report assembly | `src/agents/report.py::compile_report` | Typed combined CallReport | NOT EXECUTED |
| JSON/PDF exports | `generate_report_json`, `generate_report_pdf`, pipeline service | JSON string/PDF bytes and temporary download paths | NOT EXECUTED; no export success claimed |
| Call history | `src/services/history.py`, `src/ui/tabs/history.py` | SQLite rows and selectable report detail | NOT EXECUTED in browser |
| Observability | `src/services/observability.py`, corresponding tab | Aggregated metrics/status/recent audit rows | NOT EXECUTED in browser |
| Audio hash cache | `src/agents/transcription.py`, `TranscriptionCache` | Raw transcript cached before graph redaction; no versioned model key | Existing privacy/reuse limitation, no new runtime test |
| Real streaming | No implementation in original batch graph | Absent | NOT IMPLEMENTED by this step |
| Tenant authentication | No original tenant-auth boundary | Absent; single-user baseline | NOT IMPLEMENTED by this step |
| Neural emotion model | No acoustic classifier in original | LLM sentiment text is not acoustic emotion inference | NOT IMPLEMENTED by this step |
| Training/registry/promotion | No original train/evaluate/promote pipeline | Absent | NOT IMPLEMENTED by this step |
| Ollama provider | Original `get_llm` supports openai/gemini/groq only | No adapter; unknown provider falls through to OpenAI | No silent substitution |

The real startup attempt exited 1 in 13.80 s, before `app.py` could create its engine,
load a model, compile the graph or launch Gradio. Required selected provider key is
missing. [Raw evidence](evidence/step06-20261024/startup.json) preserves the traceback
with profile paths redacted. No confidential screenshots exist because no browser
session was launched. Real runtime feature success count is **Not measured**;
source-present rows are not counted as successfully demonstrated features.
Sample latency/model metrics and export outcome: **NOT EXECUTED**, not zero or pass.

Configure a supported provider/key privately in `.env`, check readiness without
printing values, then resume this same step. Model availability, safe resources,
actual recording permissions, browser behavior and exports still require validation.
Do not proceed to STEP_07 on the current failed real-baseline attempt.


## Latest STEP_06 resumption

2026-10-24: actual `load_config()` preflight still exits 1 for missing selected
OPENAI_API_KEY. Four mocked/storage integration cases pass in 0.94 s; no new full
app startup or real sample/browser/export run performed. Source feature findings
above remain unchanged. [Fresh evidence](evidence/step06-preflight-20261024T194812Z/commands.json).
STEP_06 remains BLOCKED / FAIL.


## Current successful baseline — supersedes prior blocked status

STEP_06 section16 records real Groq + cached tiny CPU inference on bundled sample01:
startup/upload/transcript/summary/weighted QA/persistence/history/observability and
JSON/PDF endpoint delivery observed. Transcript38 segments, duration122.74s; final
callback3.518s with ASR cache hit. JSON15,601bytes and PDF3,161bytes return200.
Browser download-save event timed out; full mypy still fails. Original theme is
dark/purple and not approved ERP styling; preserved deliberately as baseline.
Privacy, heuristic speakers, single-sample quality and completion-before-export
metrics limitations remain. No future streaming/neural/training/auth features added.
See [current report](../implementation/STEP_06_launch_the_original_gradio_app_and_create_baseline_repo_REPORT.md).


## Fresh Docker STEP_06 re-execution

One real bundled sample callback completes in5.4757s including upload/downloads;
ASR not a transcript-cache hit,31 segments,QA3.05. JSON13,584bytes and PDF3,117bytes
downloaded and validated. Empty input rejection/clearing, history and dashboard
observed. Source hashes match running container. No new API/migration/worker/model
feature introduced. [Evidence](evidence/step06-docker-20261024T201057Z/runtime.json).


## STEP_07 compatibility boundary

Gradio now delegates to AnalysisService, which calls original process_call.
An internal services.api adapter returns the same typed CallReport; there is no
new HTTP API/auth or PostgreSQL migration. Schemas and scoring implementation are
preserved. See the STEP_07 report for real post-refactor execution evidence.
