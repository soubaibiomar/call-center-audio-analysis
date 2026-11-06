# Step 06 — Launch original Gradio app and create baseline report

> **Current status: DONE — PASS WITH LIMITATIONS. See sections 16–17 for successful native and Docker runs.**  
> Date: 2026-10-24, Africa/Casablanca; lead Both. Windows 11 / uv Python 3.12.15.  
> Branch `feature/project28-foundation`, HEAD `a37e4634af1d2947fc3c548d54e62bda0b0daf89`.  
> Pinned original `fed4b610742c1337147281fcec8f2cdcc0a79be5`.  
> [Prompt](../../prompts/STEP_06_launch_the_original_gradio_app_and_create_baseline_repo_PROMPT.md),
> [template](../../report_templates/STEP_06_launch_the_original_gradio_app_and_create_baseline_repo_REPORT.md).

Sections 1–15 preserve earlier blocked attempts and their historical verdicts.
Section 16 supersedes their readiness status with actual authenticated execution.

## 1. Goal and actual outcome

Attempted to run the genuine original application before changing architecture.
Read the master/current prompt, preceding reports/known blockers, app/config/UI/
pipeline/provider/transcription/report sources and original source evidence. The
dependency and diagnostic baseline steps passed with explicit limitations, but
private credential readiness remained missing. The user said they will configure
`.env` privately; that reply is not evidence the key has been saved or authenticated.

Executed `.venv/Scripts/python.exe app.py` with hub/model downloads disabled,
tracing/analytics off and cloud-space binding removed in the child environment.
It exited 1 in 13.80 s: `OSError: Required environment variable OPENAI_API_KEY is not set`.
No source bug was invented or bypassed; no fake key/provider/mocked launch substituted
for the original app. Real pipeline/browser/sample/export verification cannot pass.
STEP_06 is BLOCKED and its quality verdict FAIL; STEP_07–STEP_15 remain unstarted.

## 2. Original vs working behavior

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


Existing feature source is documented, not labelled demonstrated. The actual
startup failure is consistent with original `load_config` requiring a selected
hosted key. STEP_06 changes no app source or provider semantics. Prior source edits
remain attributed to their steps; original full clone is preserved. Git comparison
is saved with the failed run. No later neural/platform function is claimed present.

## 3. Files explained

Created `docs/baselines/UPSTREAM_FEATURE_MATRIX.md`, this report,
`docs/baselines/evidence/step06-20261024/startup.json`, summary, Git comparison and
file inventory. Updated progress to show STEP_06 BLOCKED, not DONE. No production
code, tests, imports, dependencies, private config or UI changed in this step.
The bounded capture helper lives outside the repository. No data deleted/renamed.

## 4. Code and data flow

`app.py` imports the original components and calls `load_config()` at line 19.
`load_config` loads local dotenv settings and `_require` rejects a missing OpenAI
key when `LLM_PROVIDER` defaults to openai. That exception occurs before engine
creation/model initialization/graph compilation/Gradio construction. The traceback
locates this exact failure; it is not a GPU memory or model-quality diagnosis.

When prerequisites are satisfied, `build_app` assembles three tabs; callbacks call
`process_call`; typed `AudioInput` reaches intake/ASR/injection/redaction/summary/QA
and report nodes. The service formats transcript/summary/QA and PDF/JSON paths,
persists results and supports history/observability. This source explanation is
not runtime evidence of those outputs. No function/class was added here.

## 5. Imports/dependencies

No repository imports/packages added. Existing Gradio 5.29.0 constructs Blocks/tabs;
LangGraph 0.4.1 coordinates typed node state; faster-whisper 1.2.1 performs local
ASR; ReportLab 4.4.0 generates PDF bytes; python-dotenv 1.1.0 reads config. They
were retained by STEP_04. Presence/version is not proof of real execution.
The temporary helper uses stdlib pathlib/json/os/subprocess/time/datetime for
bounded execution, child-only safety controls and sanitized evidence. No Conda,
new credential client, model download or hidden provider adapter was introduced.

## 6. Concepts explained

Startup is an ordered dependency chain: a failed required configuration prevents
later components from initializing. Source availability, mocked-test correctness
and a real working feature are separate evidence levels. Gradio builds browser
controls; a LangGraph workflow routes state; faster-whisper needs model weights;
PDF generation needs a successful typed report. A missing credential is an external
prerequisite, not something repaired by disabling authentication or fabricating data.

## 7. Data/models/security

No audio sample, customer recording, transcript, provider request or model checkpoint
was processed. Child flags prevented model hub downloads and tracing/analytics;
no public listener was launched. Private `.env` remained untouched and ignored.
Only the required variable name appears in the sanitized traceback, not any value.
Existing raw cache/audit/encryption limitations remain. No training, metric gain,
dataset-consent conclusion, model promotion or cross-tenant capability is asserted.

## 8. Actual tests/validation

Real app command: exit 1, 13.8011 s, before server/model startup. Exact command,
traceback, flags and timestamp are in
[startup evidence](../baselines/evidence/step06-20261024/startup.json).
STEP_05 separately passed 141 unit/security and four integration fixtures and
original 113 tests; those are historical regression evidence, **not** a replacement
for this failed real baseline. Full application mypy remains an inherited FAIL.

Task gates: exact baseline attempt recorded; feature inventory references actual
paths; no confidential screenshot exposed. However, the central real-demo objective
is blocked: browser/sample/transcript/summary/QA/history/observability/PDF/JSON were
NOT EXECUTED. No green baseline is inferred from an attempted command alone.
No repetitive failed retries or source workaround; one bounded real attempt.

## 9. Analytics

One startup attempt failed in 13.80 s. This is startup-to-error time, not inference
latency or an application's working response time. Runtime demonstrated feature
count is Not measured; no source-row count becomes working capability. Sample
latency, export results, WER/CER/DER/F1, model throughput and peak VRAM are Not
measured/NOT EXECUTED. The preserved command itself downloaded no models.

## 10. Questions and answers

1. **Why preserve original Gradio?** It is the regression baseline before React or
   architecture migration; replacing it would hide whether original behavior works.
2. **Why does config fail before the UI?** The entry point requires a provider
   credential before it initializes services and constructs the browser app.
3. **Why not supply a dummy key?** It would only move failure to a later remote call
   and could falsely imply authenticated functionality without any real validation.
4. **Why not silently use Ollama?** The original factory has no adapter; that would
   replace the baseline with an unimplemented/different integration.
5. **What do passing mocks prove?** Controlled graph/data interactions, not actual
   model initialization, billing, audio quality or browser exports.
6. **Are screenshots available?** No. The app did not launch; no mock reference or
   generated imitation is substituted for a real screenshot.
7. **What is absent upstream?** Neural diarization, live streaming, tenant auth,
   acoustic emotion and a training/promotion loop; source matrix records the limits.
8. **What is needed next?** Save a supported provider/key privately, confirm status,
   then resume this same step and validate selected model, audio, UI and exports.

## 11. Decisions/risks

Maintain original behavior and fail honestly. Do not alter `.env`, remove required
key validation, use fake results or skip the failing baseline to satisfy the queue.
User scope is through STEP_15, but ordered dependencies and their no-advance-on-FAIL
rule stop at STEP_06. Credentials/model availability, actual recording permissions,
current resource capacity and runtime/browser exports still require checks.

## 12. Quality review and handoff

Acceptance/demo is incomplete; no source regression fixed or hidden. Architecture,
imports, security and performance claims are bounded to observed startup/source.
Report matches the traceback and Git diff; metrics are actual; no UI changed or
screenshot invented; blocker/next prerequisites are explicit. The ten review areas
therefore produce **FAIL** for real baseline readiness. No later step begun.

Configure matching `LLM_PROVIDER` and key privately in `.env` (openai/OpenAI key,
gemini/Google key, groq/Groq key). Run the status-only setup checker; CONFIGURED_UNVERIFIED
is still not authentication success. Resume STEP_06 when ready, retaining this
failed record under its original filename. Future runs require new evidence paths.

## 13. Approved ERP UI design / visual contract verification

Original `build_app` still uses Gradio Soft and three tabs, unchanged by this step.
The approved Commercially reference applies to future frontend development; no
redesign was requested here. Actual baseline screenshot, desktop/mobile layout and
accessibility runtime verification are **NOT EXECUTED**, because no UI started.
No confidential images or reference-metric values are used as evidence.

# Failure Analysis and Correction Report

## A. Executive Summary
E06-01 blocks the real app: selected OpenAI key missing. No genuine launch/sample
baseline is available. Private user configuration is required; report remains FAIL.

## B. Failure Inventory

| ID | Failure | Component | Severity | Reproduction | Root cause | Status |
|---|---|---|---|---|---|---|
| E06-01 | Original app exits before initialization | `load_config` / app bootstrap | P1 runtime blocker | `.venv/Scripts/python.exe app.py`, exit 1 | Selected provider key absent in effective config | UNRESOLVED; private user setup required |

Browser/sample/export omissions share this upstream cause and are not inflated
into separate fixed failures. Mypy debt remains separately recorded in STEP_05.

## C. Root-Cause Analysis
The traceback reaches `_require('OPENAI_API_KEY')` and raises OSError. This
matches the status-only config diagnostic. No model/GPU/audio call was reached,
so no CUDA, quality, diarization or latency hypothesis is invented.

## D. Code Corrections
None: original mandatory credential validation is correct. The unavailable private
credential cannot safely be replaced with a source patch or fake value. One bounded
startup attempt, no repeated unchanged retries; no three-approach ceiling exceeded.

## E. Import and Dependency Analysis
No imports/dependencies changed. Installed original stack versions remain present;
their availability does not fix the missing private configuration.

## F. File-by-File Changes
Only source matrix, report, sanitized failure evidence and progress/inventory changed.
Actual runtime source, tests, private `.env`, services and model files unchanged.

## G. Original vs Improved Repository
The same original provider requirement remains. STEP_04 improves development
readiness diagnostics and setup safety, not live-provider access. This step provides
honest baseline source evidence and failed runtime capture, not invented upgrades.

## H. Architecture Impact
No architecture change. The config boundary fails before SQLite/Whisper/graph/UI
initialization, isolating the missing input without bypassing downstream behavior.

## I. Tests and Validation
Recorded exit 1 and traceback in startup.json; earlier mock regressions remain
separate. Real analysis/browser/export tests NOT EXECUTED due to launch blocker.
No failure is converted to a pass by report wording or a fake service.

## J. Performance and ML Metrics
13.80 s startup-to-error, one sample command. No inference/training/quality metric
collected. No numeric model or reference-screen result fabricated.

## K. Security Analysis
Private credential preserved and never logged. Child tracing/analytics/model
downloads disabled; no customer content processed or public listener created.
No authentication/scanner protection weakened and no unauthorized deployment/training.

## L. Concepts Explained
An execution prerequisite is needed before a feature can be tested. Readiness
diagnostics may inspect presence safely, but only authenticated execution can prove
provider access. A real launch failure cannot be repaired by presenting mocked UI.

## M. Questions and Answers

1. **What failed?** Bootstrap configuration, with a precise missing-variable error,
   before any downstream service/model initialization or browser launch.
2. **How was it reproduced?** One bounded original-app subprocess, exact command,
   environment controls, runtime, stderr and exit code retained in JSON.
3. **Why no automated key fix?** Keys are user-private credentials; manufacturing or
   sourcing an unrelated key would not satisfy access authorization or authenticity.
4. **Why not disable the check?** It would hide the prerequisite and defer failure,
   not produce a functioning summary/QA provider.
5. **Why no provider fallback?** Changing providers silently would alter the original
   baseline, and Ollama support has not been implemented.
6. **What was preserved?** Source/API/QA behavior, UI styling, private env, data,
   upstream history, dependencies and existing services; only evidence was added.
7. **What did previous tests establish?** Mocked/synthetic graph and security behavior,
   not real audio inference, model availability or browser results.
8. **Why no screenshot?** Gradio was never constructed/launched. A source picture or
   approved reference would not be an actual runtime screenshot.
9. **What metrics can be reported?** Failed startup duration and exit status only;
   sample latency/exports/model quality remain unmeasured.
10. **When can work proceed?** After private config is saved and this same STEP_06
    passes actual model/sample/UI/export validation; STEP_07–STEP_15 remain pending.

## N. Remaining Problems
Missing selected provider credential remains the confirmed blocker. Later model,
audio permissions, browser and export behavior are unverified, not separately
diagnosed faults. Existing full typing/privacy/platform issues remain documented.

## O. Final Quality Verdict
**FAIL — STEP_06 BLOCKED.** Resume this step after private credential setup.
Do not advance to STEP_07 or claim completion through STEP_15.


## 14. Requested STEP_06 resumption — 2026-10-24

Re-read the master/current prompt and template, preceding STEP_05 report/quality
review, original entry point, configuration/provider factory, Gradio builder,
pipeline service and source feature matrix. STEP_05 is complete with limitations;
its most recent real suites passed 145 current cases and 113 original cases.
Inherited typing debt is explicit. The remaining prerequisite for STEP_06 is
actual hosted-provider configuration, not an additional dependency installation.

### Actual preflight and validation

- Status-only setup diagnostic: selected provider **openai**, selected credential
  **MISSING**, all **21** direct/dev pins match; existing `.env` not recreated.
- Exact bounded prerequisite command:
  `.venv/Scripts/python.exe -c "from src.utils.config import load_config; load_config()"`.
  It exited **1** after **0.3364 s** with
  `OSError: Required environment variable OPENAI_API_KEY is not set`.
  This is a confirmed readiness failure, not a passing application launch.
- `pytest tests/integration/ -q --tb=short`: **4 passed in 0.94 s**, zero failed/skipped.
  Two temporary SQLite tests and two mocked graph tests remain distinct from a
  real hosted analysis. Visible pytest-asyncio warning remains unsuppressed.
- `git diff --check`: exit 0. Current HEAD remains
  `a37e4634af1d2947fc3c548d54e62bda0b0daf89`. Captured diff retains earlier changes,
  not new production edits: 11 tracked files, 150 insertions, 118 deletions.
- Private configuration byte preservation verified locally; only the boolean is
  saved. No credential contents/digest, private audio, provider request or model
  weights were written into evidence.

[Fresh commands](../baselines/evidence/step06-preflight-20261024T194812Z/commands.json)
and [summary](../baselines/evidence/step06-preflight-20261024T194812Z/summary.json)
record exact outputs, command durations and prerequisite status. The earlier full
app failure remains preserved in its original startup log. This resumption did
not repeat a full app invocation while the same mandatory configuration still
fails; no different server/model/browser outcome is claimed.

### Source assessment and unmet runtime work

Confirmed `app.py` calls `load_config()` before database, Whisper, workflow and
Gradio setup. `build_app` uses original Soft theme and Analyze Call/All MP3 History/
Observability tabs. `process_call` wraps audio in `AudioInput`, invokes the graph,
persists a typed report and generates download paths for PDF/JSON. These are
source findings, not demonstrated runtime capabilities. Existing components,
imports, concepts and answered technical questions remain explained in sections
2–10 and the failure-analysis appendix; no new repository import or runtime
component was added.

Bundled-sample inference, transcript, summary, rubric, actual downloads, history,
observability, browser screenshots and accessibility remain **NOT EXECUTED**.
Working feature count, sample latency, export success, model quality and peak VRAM
remain **Not measured**, rather than zero or passed. Original UI appearance was
preserved; the approved reference is not substituted for an actual screenshot.
No consented training operation occurred and no model/data download was performed.

Changed this report (including required section 13 heading), feature-matrix handoff,
progress note and two fresh evidence files only. No production/test/dependency,
private config or provider behavior change; no commit/push or STEP_07 advancement.

**BLOCKED — FAIL.** The central real-baseline objective remains unmet. Configure a
matching supported provider/key privately in the project `.env`; do not paste
credentials into chat. Then run `scripts/check_project_setup.py` for value-free
readiness and resume this same step. Presence still requires real authentication
and model/sample/UI/export validation. Next eligible work is **STEP_06 resumption**;
STEP_07 is not eligible while this failure remains.

## 15. Quality review of latest STEP_06 attempt — 2026-10-24

Reviewed STEP_06 as the latest attempted step; it is not a completed step.
STEP_05 remains the most recently completed numerical step and already has a
separate quality review. This audit does not reinterpret a blocked attempt as DONE.

| Review requirement | Evidence, findings and decision |
|---|---|
| 1. Acceptance criteria | Exact failed startup/preflight and code-backed feature inventory exist, with no confidential screenshots. However, the central real-demo objective is unmet: launch/sample analysis and exports have not been demonstrated. Overall FAIL. |
| 2. Existing functionality | No production/test source changed in STEP_06. Latest four storage/mocked graph integrations passed in 0.94 s. Recent STEP_05 full suites passed 145 current and 113 original cases. These do not establish live inference compatibility. |
| 3. Architecture/security/performance | Original config boundary correctly rejects missing required credentials before model/UI startup. No new service, public listener, private input or data-processing boundary introduced. No timing-to-error is presented as inference latency. |
| 4. Imports/dependencies | No new repository imports or installed dependencies. All 21 direct/dev pins still match. Existing stack and temporary capture imports are explained in sections 5–6. |
| 5. Automated checks | Verified raw configuration command exit 1 and exact missing-key traceback; it remains a failure. Verified raw integration exit 0 and four passes. Fresh whitespace check passes. Existing mypy failure stays documented. No unchanged suites repeatedly executed solely to duplicate the immediately preceding result. |
| 6. Report/source/Git | All 13 required sections and five existing report artifact links verified. Bootstrap/config/provider/UI/pipeline source inspected in the preceding attempt; report accurately separates source presence from runtime proof. Current Git identity/diff checked. |
| 7. Metrics evidence | Prior preflight command log SHA-256 recorded in this review summary; integration counts/duration and configuration failure agree with raw capture. Original full-app startup failure retained separately. No new demo, export, model-quality or training measurements claimed. |
| 8. Approved UI | Original Gradio preserved. Actual runtime screenshot/reference comparison cannot be completed because startup prerequisite is absent. Visual, responsive and accessibility runtime checks are NOT EXECUTED; no fake screenshot or redesign. |
| 9. Issues/limitations | E06-01 missing selected provider key remains confirmed. Model availability, actual sample permissions, browser/exports, inherited full typing/privacy limits remain explicit. No new in-scope code defect identified. |
| 10. Next dependencies | Selected credential readiness remains false. STEP_06 is BLOCKED and STEP_07 is not eligible. Required next action is privately configured supported provider/key, followed by actual STEP_06 model/sample/UI/export validation. |

[Quality summary](../baselines/evidence/step06-quality-review-20261024T194848Z/summary.json)
and [Git checks](../baselines/evidence/step06-quality-review-20261024T194848Z/git-checks.json)
provide this audit's evidence. Updated only this report, progress and those review
artifacts. No code fix can supply a user's private provider credential. No private
configuration write, dependency install, model download, app retry, commit or push.

**FAIL — STEP_06 remains BLOCKED.** Mandatory configuration and genuine demo
validation are incomplete. Resume this same step after private credential setup;
do not advance to STEP_07.


## 16. Groq configuration, baseline correction and successful execution

### Current outcome and why the changes were necessary

The user explicitly supplied a Groq key and authorized using it. Saved it only in
ignored `.env` with `LLM_PROVIDER=groq`. Actual authenticated model listing succeeded;
the old default `llama-3.3-70b-versatile` returned HTTP 404/model_not_found. Selected
account-accessible `openai/gpt-oss-20b` using the new private `GROQ_MODEL` override.
A synthetic request through the real factory succeeded with nonempty response.
No credential value is reproduced in this report or repository evidence.

Started the actual `app.py`, cached Whisper tiny CPU/int8, graph and Gradio on
127.0.0.1:7860. Child environment disables tracing/analytics/model-hub downloads;
`SPACE_ID` removed to retain loopback binding. Used separate ignored
`data/project28-step06-baseline.db`; did not replace the user's existing call DB.
Bundled sample_01.mp3 is provided upstream for educational/testing use; no training
permission or private customer-data clearance is inferred. No weights downloaded.

### Confirmed defects and exact code corrections

| File | Change and reason | Compatibility |
|---|---|---|
| `src/utils/llm_factory.py` | Added stdlib os and provider-specific model environment override | Explicit model argument wins, then stripped provider override, then historical default. Other provider defaults unchanged. |
| `.env.project28.example` | Comment documenting optional GROQ_MODEL | No real credential; existing private configuration preserved except authorized provider/key/model updates. |
| `pyproject.toml`, `requirements.txt`, `PROJECT28_REQUIREMENTS.lock.txt` | Pin av18.1.0 instead of observed19.0.2 | faster-whisper1.2.1 retained; no other package version changed. Direct/dev pin count now22, installed distribution count127. |
| `src/agents/summarization.py`, `src/agents/qa_scoring.py` | Include actual call UUID in system messages | Real provider rejected null/invalid generated call IDs. Schema and post-validation call-ID assignment preserved; QA weights unchanged. |
| `src/services/pipeline.py` | Write JSON with explicit UTF-8 | Real Windows cp1252 export failed on a Unicode character after persistence; output schema unchanged. |
| `tests/unit/test_llm_factory.py` | Three model precedence/provider-isolation cases | No network/credential needed. |
| `tests/unit/test_audio_decoder.py` | Decode a synthetic 1s silent WAV through real faster-whisper/PyAV | Reproduced pre-fix TypeError: one failed in0.40s, then passed with compatible dependency. No model loaded. |
| `tests/unit/test_summarization.py`, `test_qa_scoring.py` | Assert system prompt carries source call UUID | Existing result/score assertions retained. |
| `tests/unit/test_pipeline_exports.py` | Real UTF-8 JSON/PDF output through service with synthetic report and mocked workflow | Simulates cp1252 default; validates multilingual text round trip and PDF signature. |
| `docs/environment/setup.md` | Documents model override and compatibility pin | Historical STEP_04 installation/version counts remain truthful snapshots. |
| Report, feature matrix, progress and evidence | Current successful results plus earlier failures retained | No history/failed evidence overwritten. |

PyAV19 removed `metadata_errors`, which pinned faster-whisper1.2.1 still passes.
This was verified in the actual traceback and the real decoder regression, and
matches the [upstream issue](https://github.com/SYSTRAN/faster-whisper/issues/1589)
and [PyAV release notes](https://github.com/PyAV-Org/PyAV/releases/tag/v19.0.0).
Downloaded only the compatible26.3MiB wheel, not model/data assets. uv observed
preparation18.07s, uninstall0.030s, install0.178s; not a controlled install benchmark.

The factory resolves a model once before constructing the provider client; blank
overrides fall back. Both agent functions append an authoritative existing UUID
to their system message, avoiding a model-invented identifier while retaining
Pydantic validation and bounded retries. UTF-8 removes Windows locale dependence
at the final JSON boundary. No monkey patch of installed dependencies or schema
relaxation was used. No scoring weights or report contract changed.

New test imports: io and existing faster_whisper.audio.decode_audio exercise real
decoding; unittest.mock.patch/MagicMock isolate provider/workflow calls; builtins
simulates locale-default open; json and pathlib validate generated files; uuid
creates synthetic identities; existing test factories build valid reports. Existing
pytest supplies fixtures/parameterization. No new test-framework dependency.

### Actual runtime results and metric definitions

Final sample: original sample_01.mp3, 1,769,445 bytes, report duration122.74s,
38 transcript segments. Final call ID `80af7bd1-fcbe-4c73-a537-63deda990a2c`.
Real Groq summary and QA both returned HTTP200; final UI displayed Analysis complete,
transcript, summary, QA and download links. Weighted QA result3.2/5 is one generated
assessment, not a measured improvement or validated ground truth. Speaker labels
remain heuristic and visibly unreliable; tiny model output is not quality-certified.

Server-observed callback-to-render duration: **3.518s** (19:59:02.484–19:59:06.002),
one final run with a transcription-cache hit. Earlier uncached transcription node
logged2.3s; that is not final end-to-end latency. Earlier full analysis needed schema
retries and hit HTTP429. No throughput, p95, WER/CER/DER/F1, GPU peak or training gain
measured; CPU/int8 used. Timings must not be compared as controlled speedups.

Actual UI export links fetched with HTTP GET: JSON200, **15,601 bytes**, valid
UTF-8 JSON and complete Pydantic CallReport; PDF200, **3,161 bytes**, valid %PDF magic.
Browser download-event automation timed out, so browser-save completion is **not
certified**. Direct actual endpoint delivery is verified. JSON/PDF content remains
in local temporary exports; evidence stores hashes/metadata rather than raw text.
PDF bytes/signature prove file delivery, not full Unicode glyph/accessibility quality.

History tab loaded both persisted records; observability showed two completed rows,
average3.2 and two completed audit events. One row originated before the JSON export
fix. Therefore the dashboard's 100% completion figure is a database/graph status,
not a truthful end-to-end export success percentage. This inherited metric limitation
is explicitly retained; no claim of two successful UI/export runs.

### Automated validation and evidence

**150 passed in20.57s**, zero failed/skipped. Strict Ruff lint passes; format checks
66 Python files. uv pip check passes127 installed distributions; all22 direct/dev
pins match. Full mypy still exits2 after six initial errors in three files, aborting
on inherited stubs/optional torch/NumPy target issues. No suppression added.
Secret scanner passes changed/new code; the exact supplied key is absent from every
tracked and nonignored file scanned. `.env` and demo database are ignored/untracked.

Evidence:

- [Provider availability diagnosis](../baselines/evidence/step06-groq-20261024T195347Z/model-diagnostic.json).
- [Successful actual model probe](../baselines/evidence/step06-groq-20261024T195625Z/provider-probe.json).
- [Validation commands/results](../baselines/evidence/step06-groq-20261024T195347Z/validation.json).
- [Real export validation](../baselines/evidence/step06-groq-20261024T195347Z/exports.json).
- [Runtime observations and failure history](../baselines/evidence/step06-groq-20261024T195347Z/runtime-summary.json).
- [Secret/ignore checks](../baselines/evidence/step06-groq-20261024T195347Z/security-checks.json).
- [Artifact hashes](../baselines/evidence/step06-groq-20261024T195347Z/seal.json).

The intermediate195433 probe accepted a request with an eight-token budget but
returned empty content; its model metadata still reflected the old constant.
The later195625 record reads the actual selected model and verifies nonempty
content. The intermediate record is not used as successful output evidence.

### UI baseline and approved-reference comparison

Actual screenshots: [empty baseline](../baselines/evidence/step06-groq-20261024T195347Z/gradio-empty.png),
[decoder failure](../baselines/evidence/step06-groq-20261024T195347Z/gradio-decode-failure.png),
[history](../baselines/evidence/step06-groq-20261024T195347Z/gradio-history.png),
[observability](../baselines/evidence/step06-groq-20261024T195347Z/gradio-observability.png).
Screenshots selected to exclude recording transcript/customer fields; history and
metrics show only demo metadata. No screenshot of full transcript/summary published.

Original Gradio Soft follows current dark browser/system preference with purple
controls; it does **not** meet the approved white/neutral/green ERP reference.
Preserving the original appearance is explicitly required for this baseline; no
redesign or new color token introduced. Desktop baseline observed only; mobile,
contrast, keyboard and reduced-motion acceptance are NOT VALIDATED. This is baseline
evidence for later frontend work, not approved product design acceptance.

### Additional questions, limitations and next handoff

1. **Did the credential work?** Yes: authenticated model listing and real inference succeeded; absence is resolved without logging its value.
2. **Why a model override?** Available models differ by account/time. Explicit argument remains highest precedence and fallback behavior is preserved.
3. **Why pin PyAV?** A real upstream API removal broke decoding; the synthetic decoder test reproduces and prevents this compatibility regression.
4. **Why specify UUID?** Structured tools validate before Python can overwrite the result ID; invalid/null IDs must be prevented in the request context.
5. **Why UTF-8?** Windows default text encoding cannot represent every generated Unicode character; the download must round-trip model output.
6. **Is cache-hit latency a cold benchmark?** No; it is labelled as one observed cache-hit callback execution.
7. **Does completed status mean exports succeeded?** Not in the inherited implementation, which persists completion before export. Observability needs later correction.
8. **Is this a trained/production platform?** No. English tiny ASR, heuristic labels, imperfect PII/address handling, raw pre-redaction cache, audit mutability, no tenant auth and free-tier limits remain.

**DONE — PASS WITH LIMITATIONS.** Baseline is genuinely runnable with actual
summary/QA, persistence/history/observability and delivered exports. Limited by
single-sample evidence, free-tier quota, unvalidated accuracy/browser-save/mobile/UI
acceptance, inherited privacy/metrics and full typing debt. Next eligible step is
STEP_07; no STEP_07 implementation or later step was started by this resumption.
No commit, push, timestamp adjustment or published-history change occurred.


## 17. Requested STEP_06 Docker re-execution — 2026-10-24

### Scope, prerequisites and architecture

Re-read the master instructions, full STEP_06 prompt/template, preceding STEP_05
report, existing source and latest Docker operation evidence. The Gradio and
PostgreSQL containers were healthy; Groq configuration already worked. Existing
`app.py`, Analyze callback, service export code and actual Gradio API inventory
were inspected before execution. No new runtime implementation was necessary.

Used the actual Docker Gradio application on `http://127.0.0.1:7861/`. It retains
SQLite at `/app/data/calls.db` and hosted Groq `openai/gpt-oss-20b`, with cached
Whisper tiny on CPU/int8. PostgreSQL remains ready but is not application storage;
Ollama is not silently substituted as provider. No model download, migration,
training, service reconfiguration or STEP_07 advancement occurred.

SHA-256 comparisons verify the container executes the same current entry point,
analysis service, provider factory, summary and QA source as the checkout. Working
HEAD remains `a37e4634af1d2947fc3c548d54e62bda0b0daf89`; pinned original is
`fed4b610742c1337147281fcec8f2cdcc0a79be5`. The captured Git diff still contains
prior changes, not new production edits from this re-execution.

### Actual feature and upstream comparison

| Feature/source | Original and preserved contract | Fresh Docker result |
|---|---|---|
| `app.py`, `build_app` | Gradio startup, three tabs | Healthy endpoint; actual browser rendered |
| Analyze `_run_pipeline`, `process_call` | Reject empty audio, clear stale outputs | One empty-input callback rejected; remaining five outputs empty |
| Intake/ASR graph | Audio validation and typed transcript | Bundled sample01 processed; 31 segments, 122.74s reported duration |
| Summary and weighted QA | Structured Pydantic results and existing weights | Both real Groq requests HTTP200; nonempty summary/QA; score3.05 independently recomputed |
| Report/UTF-8 JSON/PDF | Existing CallReport and export file outputs | Both downloaded by real Gradio client; JSON schema/IDs valid, PDF signature valid |
| History | Existing SQLite records and row list | API callback and browser table load completed row |
| Observability | Existing database metrics/audit dashboard | Three callback outputs; browser shows one completed call/audit event, tracing disabled |
| Streaming/neural speakers/emotion/training/auth | Absent in original | Not implemented or implied by this baseline |

This re-execution invokes original registered Gradio callbacks via gradio-client,
not a new FastAPI service or a mocked graph. Browser history/observability are
verified separately. It does not claim the Analyze button was clicked for this
Docker run; section16 preserves the prior actual native UI button workflow.

### Runtime, downloads and measured results

Uploaded the exact bundled `data/samples/sample_01.mp3`, SHA-256
`992feada7a67a56ee2881e0e2dc6ae8980d3190238be26c58d5b29b323b47989`.
Educational/testing use only; no training consent inferred. The client call,
including upload, queued callback and export downloads, took **5.4757s** for one
sample. Server logs show fresh ASR (no transcription cache hit), **1.7s** ASR node
and **3.4s** summary/QA node. This excludes model startup already completed by the
container and is not a cold-container latency benchmark or p95.

Call ID `f94d4fe5-48f2-432a-984a-030727f7c3db` is consistent across report,
transcript, summary and QA. Final report status completed; 31 segments, duration
122.74s, weighted QA3.05. JSON **13,584 bytes**, valid UTF-8 and CallReport schema;
PDF **3,117 bytes**, valid %PDF signature. Actual files downloaded into ignored
`.local/step06-docker-downloads`; public evidence contains hashes/counts rather
than transcript or summary content. Gradio-client download succeeds; native browser
save behavior remains a separate unvalidated layer after the earlier timeout.

Different segment counts/QA from the earlier Windows run do not establish accuracy
change: OS/runtime, segmentation, cache and hosted output conditions differ. No
reference transcript/labels or controlled benchmark. WER/CER/DER/F1, throughput,
p95, peak inference VRAM and training improvement remain **Not measured**. CPU
inference used; no GPU-heavy operation initiated by this rerun.

### Tests, execution evidence and source integrity

Fresh full suite: **152 passed in21.58s**, zero failed/skipped. Ruff lint passes;
format verifies68 Python files. Full mypy still **FAILS**, exit2 after six initial
errors in three files before abort; inherited typed-stub/optional torch/NumPy target
issues remain unsuppressed. Git whitespace check passes. The additional two cases
relative to section16 are the already-existing Docker preparation tests.

No new function/class/import/dependency was added to the repository. The bounded
capture helpers outside the repository use existing gradio-client1.10.0 for upload,
callback submission and downloads; existing local CallReport and QA weight imports
validate output. Stdlib pathlib/json/hashlib/time/datetime/subprocess/os/sys provide
paths, metadata serialization, integrity, timing, capture and import resolution.
One temporary proof helper initially lacked the checkout on sys.path; corrected
only the temporary helper and reran successfully. This was not an application fault.

The helper first submits empty input and checks failure/clearing, then uploads the
sample using `handle_file`, invokes `/_run_pipeline`, parses downloaded UTF-8 JSON,
checks PDF bytes, and calls history/observability. It stores only redacted metrics.
A second helper hashes the running container's source, compares host bytes and
independently recomputes weighted QA; no duplicated production analysis algorithm.
Earlier section16 explains every prior source/import/dependency correction.

Files changed by this re-execution: this report, source feature-matrix update,
progress note and the new evidence directory below. Runtime writes are confined
to the existing Docker data volume and ignored client-download directory. No source,
test, configuration or package changes; no commits/pushes/timestamp adjustment.

### Actual UI comparison, privacy and limitations

Captured fresh empty/history/observability screens without transcript, personal
sample fields or credentials. Visually inspected current Docker dashboard and the
approved `design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png`: original Gradio is
still dark/purple with tab navigation, while approved product styling is light,
rounded white cards/sidebar and green accents. This **does not pass product UI
style acceptance**; preserving the original is required for STEP_06 baseline.
No new color tokens/styles introduced. Responsive/mobile, contrast, keyboard and
reduced-motion checks remain unvalidated. Screenshots are real browser captures,
not generated replacements or reference metrics.

Dashboard shows one completed call and one audit event after both the negative
input test and successful sample. Its100% reflects stored calls, excluding rejected
empty input; as noted earlier, completion also precedes export generation. Do not
interpret this as an independently measured100% request/export success rate.
Existing raw transcript cache, imperfect PII/address masking, heuristic speakers,
no tenant auth and mutable audit guarantees remain unchanged. No real private
customer recording was introduced. Tracing/analytics/model downloads stay disabled.

### Questions and next handoff

1. **Was the workflow real?** Yes: Docker's original registered callback ran real cached-weight ASR, hosted structured summary/QA and report exports.
2. **Does cached model mean cached transcript?** No. Weights were already present; logs show actual ASR decoding/inference and no transcription-cache hit for this run.
3. **Did downloads work?** Both files were downloaded by gradio-client and validated locally. Browser-native save is not certified by that evidence.
4. **Why are scores/segments different?** Different runtime/segmentation and nondeterministic model output can change observations; no quality improvement is claimed without reference labels.
5. **Did PostgreSQL take over persistence?** No. The baseline remains SQLite; its planned migration is still pending.
6. **Does UI style match the approved product?** No; this preserves original Gradio as before-migration evidence, with the mismatch documented.
7. **What remains failing?** Inherited full mypy, production privacy/auth guarantees, model-quality evidence and broader browser/mobile acceptance remain limitations.
8. **What is next?** STEP_07 shared architecture/compatibility implementation. This re-execution does not implement it or later steps.

**DONE — PASS WITH LIMITATIONS.** All three STEP_06 gates have current execution
proof: actual demo outcome, source-backed inventory and screenshots without
confidential content. Next eligible implementation step: **STEP_07**.

Fresh evidence: [runtime](../baselines/evidence/step06-docker-20261024T201057Z/runtime.json),
[tests/Git/logs](../baselines/evidence/step06-docker-20261024T201057Z/validation.json),
[source and contract proof](../baselines/evidence/step06-docker-20261024T201057Z/source-runtime-proof.json),
[empty screen](../baselines/evidence/step06-docker-20261024T201057Z/gradio-empty.png),
[history](../baselines/evidence/step06-docker-20261024T201057Z/gradio-history.png),
[observability](../baselines/evidence/step06-docker-20261024T201057Z/gradio-observability.png),
[seal](../baselines/evidence/step06-docker-20261024T201057Z/seal.json).


## Follow-on STEP_07 architecture update

The native/Docker captures above remain historical STEP_06 baseline evidence.
STEP_07 now routes Gradio through an injectable shared service while preserving
the existing analysis and report schemas; its real post-refactor regression and
packaging/import checks are in the [STEP_07 report](STEP_07_define_modular_target_structure_and_compatibility_layer_REPORT.md).
No prior run, metric or source-hash snapshot was rewritten.
