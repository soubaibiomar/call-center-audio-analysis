# STEP_11 — Integrate Qwen through a safe model-provider adapter

## 1. Execution header, goal and plain-English explanation

**Latest correction audit: 2026-10-27 —301 tests pass; four confirmed failure groups fixed. See the appended A–O correction record.**

**Status: DONE — PASS WITH LIMITATIONS.** Owner: AI/ML / Codex implementation.
Date: 2026-10-27, Africa/Casablanca. Branch: `feature/project28-foundation`.
Working HEAD: `a37e4634af1d2947fc3c548d54e62bda0b0daf89` (uncommitted implementation).
Verified upstream: `fed4b610742c1337147281fcec8f2cdcc0a79be5`, preserved STEP02 clone.
Environment: Windows11, PowerShell, uv Python3.12.15, Docker Desktop/Linux containers,
RTX4060 Laptop8188MiB; Ollama0.32.4. No Conda, training or model download.

The problem was concrete: setting LLM_PROVIDER=ollama previously fell through to
OpenAI because the factory implemented only three hosted providers. This step adds
an opt-in local Qwen path using the installed LangChain/OpenAI SDK. It keeps original
summary/QA contracts, validates local JSON, rejects unknown providers, bounds local
requests, and records model execution facts without transcript/error-body logging.
The authorized report API now carries those receipts for later analysis/Model Lab UI.
Default private provider selection remains unchanged. No frontend was redesigned.

Read master instructions, this step's complete prompt/report template, STEP06–10
reports, progress, durable-jobs architecture, upstream factory and current source.
STEP10's queue/schema/security gates passed previously; local services were freshly
started through Docker Desktop and revalidated. Missing real OIDC, production load,
retention/privacy controls and clean registry-build limitations carry forward; none
requires bypassing authentication to test isolated signed fixture identities.
Only STEP11 was implemented. STEP12 remains eligible, not started.

Evidence folder: [step11-20261027T085643Z](evidence/step11-20261027T085643Z/README.md).

## 2. Actual upstream versus upgraded implementation

| Surface / actual symbol | Pinned upstream | Before STEP11 / final behavior | Compatibility/rationale |
| --- | --- | --- | --- |
| src/utils/llm_factory.py:get_llm | OpenAI/Gemini/Groq; unknown values fall through to OpenAI | Earlier provider-specific environment overrides retained; new Ollama branch, unknown names rejected | Three supported hosted constructors unchanged; explicit typo rejection avoids unintended cloud execution |
| src/agents/summarization.py:run_summarization | Structured SummaryResult and agent retry loop | Same result and trusted UUID override; shared validated invocation and safe receipts | Function arguments and return schema preserved |
| src/agents/qa_scoring.py:run_qa_scoring | Five weighted dimensions, structured output | Same rubric, weights and recomputed overall score; shared invocation | Original scoring tests pass; no quality improvement claimed |
| src/graph/workflow.py:summarize_and_qa_node | Sequential summary then QA, errors routed to failed | Same order with request-local model_runs capture | Existing PII/injection checks and graph routing retained |
| src/graph/state.py:CallReport; report.compile_report | Report lacks model receipts | Add default-empty model_runs; persist in existing report JSON | Historical records decode; no migration/backfill |
| services/api/schemas.py:Report | No upstream FastAPI equivalent | Existing API adds scoped model_runs; OpenAPI regenerated | Tenant/owner access remains unchanged; no new endpoint |
| src/services/model_runs.py / structured_inference.py | No equivalent | Content-free attempt receipts and bounded validated invocation | Modular addition without new infrastructure |
| scripts/benchmark_local_llm.py | No comparable experiment | Actual serial cached7B/9B synthetic comparison | No weight/data download or training |

Actual broader `git diff --stat` and `git diff --name-status` are saved in evidence,
alongside `git status --short`. The workspace contains accumulated earlier changes;
those totals must not be attributed entirely to STEP11. New files are untracked and
therefore absent from ordinary diff statistics. Audit-specific source diffs compare
saved pre-step snapshots against final code. No commit, timestamp change or push.

## 3. Files explained — created, modified and kept

| Path | Action / purpose | Interface and validation |
| --- | --- | --- |
| src/utils/llm_factory.py | Modify; local SDK construction and configuration policy | get_llm returns BaseChatModel; hosted/local SDK contract tests |
| src/utils/structured_inference.py | Create; shared attempt budget, parse, safe failure | invoke_validated(factory,schema,messages,provider/model/prompt/budget) returns schema instance or sanitized error |
| src/services/model_runs.py | Create; typed receipts and request-local capture | ModelRun, capture_model_runs, record_model_run; isolation/metadata tests |
| src/agents/summarization.py, qa_scoring.py | Modify; use shared invocation | Original public signatures, ID override and QA weighting preserved |
| src/graph/state.py | Modify; default-empty report receipts | CallReport old/new JSON round-trip |
| src/graph/workflow.py | Modify; capture attempts and forward to completed/review report | PipelineState.model_runs; failed state also retains safe receipts |
| src/agents/report.py | Modify; compile optional model_runs into report | Existing JSON/PG persistence stores additive data |
| services/api/schemas.py | Modify; expose receipts in authorized Report | Real PG-to-HTTP integration and owner-denial test |
| src/utils/config.py | Modify provider comment only | Existing non-OpenAI key behavior already supports local selection |
| scripts/benchmark_local_llm.py | Create; explicit reproducible experiment | New output directory; cached model check; serial synthetic fixtures; partial/final receipts |
| tests/llm/test_local_provider.py | Create;17 cases | Hosted compatibility, endpoint restrictions, schema/transport/retry/privacy, graph/report and context behavior |
| tests/api/test_model_runs.py | Create;1 real-service case | Stored report metadata survives authorized HTTP and denies peer |
| requirements.txt, pyproject.toml | Modify; promote existing httpx0.28.1 pin into runtime dependencies | No new installed package/version; uv consistency/setup tests |
| .env.project28.example | Modify commented opt-in configuration | Existing private .env preserved |
| docs/api/openapi.json | Regenerate additive ModelRun/Report schema | Snapshot parity test |
| docs/api/README.md; docs/development/local-models.md | Update/create API and operator guidance | Exact constraints, reproduction and limits |
| This report, PROGRESS.md, STEP09/STEP10 report appendices | Current status and follow-on compatibility documentation | Historical measurements remain historical |
| evidence/step11-20261027T085643Z/ | Create execution evidence and source/integrity manifests | No credentials, transcripts or provider logs published |

Kept: original Gradio UI, ASR implementation/cache, database migrations, job ledger,
RLS/identity rules, S3 policies, injection/PII handling, QA prompts/weights and PDF
format. Existing Ollama configuration and models were inspected, not reconfigured.
Ignored `.local` helpers orchestrated isolated validation; they are not product APIs.

## 4. Code explanation and algorithm

### Factory policy and actual SDK contract

```python
if provider not in DEFAULT_MODELS:
    raise ValueError("Unsupported LLM provider")
# Local branch validates endpoint/model/timeout before constructing the SDK.
ChatOpenAI(model=model_name, base_url=endpoint, api_key=SecretStr("ollama"),
           timeout=timeout, temperature=0, max_completion_tokens=2048,
           max_retries=0, extra_body={"reasoning_effort": "none"}, ...)
```

The first block prevents a misspelled provider from silently selecting a hosted
service. Explicit model wins, then provider-specific environment, then default.
Local default is already-cached qwen2.5-coder:7b; no implicit pull is performed.
Endpoint parsing requires HTTP, the exact /v1 path and an allowed local hostname:
localhost/127.0.0.1/::1/ollama/host.docker.internal. Userinfo, query and fragment are
rejected. Model syntax is bounded to200 safe identifier characters. Timeout is
positive and at most600s, excluding bool/NaN/infinity through bounded comparison.
HTTPX sync/async clients disable environment proxies and redirects. The dummy key
satisfies SDK typing and is not a hosted credential. Local SDK retries0 prevent a
hidden second retry budget. The installed typed constructor uses the alias
max_completion_tokens; actual controlled HTTP requests assert2048 and reasoning none.
The three existing hosted constructor calls remain model+timeout only.

### Validated invocation and safe failure

`invoke_validated` accepts a factory so construction errors are also observed.
It requires an integer1–5 attempt budget; creates/binds a structured client lazily;
uses explicit json_schema for Ollama and each existing provider's previous default
structured method; invokes and validates with the original Pydantic result class.
Every attempt records elapsed perf_counter time, attempt/retry counts, model and
prompt revision, schema name, validity and a fixed safe error code. Only failed
attempts wait min(2**(attempt-1),10)s before another try. SDK local retries are off.
No model or hosted fallback branch exists.

ValidationError maps to schema_invalid; timeout/connection/status exceptions map to
timeout/unavailable/provider_http_error; unknown failures become provider_error.
Neither logs nor the terminal exception concatenate raw exceptions, prompts or
responses. The final agent error retains the recognizable “Failed after N attempts”
contract with the safe code. The trusted call_id overwrite and QA recomputation run
after successful validation. Schema-valid output still requires human evaluation
for factual correctness. No automatic correction of invented content is claimed.

### Metadata through the graph and persistence

`capture_model_runs` uses ContextVar.set/reset in a finally block. Concurrent/nested
executions have separate lists and restore previous context. `record_model_run`
appends to that active list and emits content-free JSON. ModelRun bounds numeric
counts/latency and makes fallback explicitly none. model_version stores the configured
tag, not an invented immutable digest. prompt_revision is the first16 hex characters
of SHA256 over the static system prompt; dynamic transcript/call UUID is excluded.

The sequential graph node returns model_runs alongside summary/QA or failed state.
Both report nodes pass them to the optional compile_report argument. CallReport and
API Report default to an empty list so old persisted JSON remains readable. Existing
report_json storage needs no new column or migration. Authorized report reads expose
receipts through the same owner/tenant checks. Failed jobs retain existing sanitized
job error_code; failed attempt receipts are logged/retained in graph state, without
fabricating a completed report or a Model Lab endpoint.

### Experiment implementation

The script checks `/api/tags` so only cached tags are attempted. Three deterministic
synthetic English dialogs become typed transcript fixtures. Each model performs
summary then QA for each fixture, serially, one attempt. Outputs are validated and
hashed, not stored as text. Per-case files survive interruption; final results include
registry digest, model details, `/api/ps` context/resident memory, timings and schema
validity. A bounded sampler runs nvidia-smi between requests, with0.2s minimum wait;
this observes whole-device memory and can miss short peaks. No ASR/training occurs
inside the comparison. Complexity is proportional to fixtures × models × phases;
model inference dominates, with small receipt and transcript storage.

## 5. Imports and dependency explanation

Installed versions verified: langchain-openai0.3.12, langchain-core0.3.63,
openai1.82.0, pydantic2.11.3, httpx0.28.1. HTTPX was already installed/locked and was
listed as a dev extra; because local production code now imports it directly, its
same exact pin is declared in runtime requirements and moved out of the dev list.
No new package download/version change, Ollama SDK dependency or framework upgrade.

| New import(s) | Origin / meaning / call site / reason |
| --- | --- |
| re; urllib.parse.urlsplit | stdlib; bound model identifiers and parse/validate operator endpoint in factory |
| httpx; pydantic.SecretStr | Existing HTTPX0.28.1/Pydantic2.11.3; explicit proxy/redirect policy and typed dummy SDK key in local branch |
| ChatOpenAI in local branch | Existing langchain-openai0.3.12; reuse tested OpenAI compatibility instead of adding another client stack |
| logging; collections.abc.Iterator | stdlib; content-free receipt log and capture generator type in model_runs |
| contextlib.contextmanager; contextvars.ContextVar | stdlib; exception-safe scoped receipt collection without global cross-call state |
| typing.Literal; pydantic.BaseModel,Field | stdlib + Pydantic2.11.3; typed receipt status/bounds and generated API schema |
| hashlib; time | stdlib; prompt revision and monotonic timing/retry wait in structured_inference |
| collections.abc.Callable; typing.TypeVar | stdlib; typed lazy factory and generic schema-preserving return value |
| BaseChatModel; BaseMessage | Existing langchain-core0.3.63; provider-independent invocation and typed messages |
| APIConnectionError,APIStatusError,APITimeoutError | Existing openai1.82.0; classify transport failure without logging exception bodies |
| BaseModel,ValidationError | Pydantic2.11.3; typed validation and schema-error classification |
| ModelRun,record_model_run; DEFAULT_MODELS | Local modules; emit shared receipts with correct configured/default identifier |
| StructuredInferenceError,invoke_validated | Local; replace duplicated agent loops while retaining agent-specific public errors |
| ModelRun,capture_model_runs across graph/report/API | Local; carry receipts without adding metadata to the LLM's generated result schema |
| argparse,json,math,subprocess,Path,Event,Thread,NAMESPACE_URL,uuid5 | stdlib; explicit experiment CLI, serialization, nearest-rank p95, GPU sampling, fixture identity and files |
| Existing agents/state/capture imports in benchmark | Local; exercise actual inference/validation instead of a separate mock benchmark path |
| pytest,unittest.mock,httpx,ChatOpenAI and existing fixtures in new tests | Existing test/runtime tools; control HTTP boundary while executing the real SDK/parser; real PostgreSQL/HTTP fixture for persistence |

No import starts a model/server on module import. Factory clients are constructed
on demand. An AST import inventory in evidence records exact statements and source
locations, including reused benchmark hashlib/time/httpx and model schema imports.
Alternative native Ollama SDK would allow per-request context/keepalive controls;
this step chose the existing OpenAI-compatible stack and preserved server settings.

## 6. Core concepts explained for a beginner

A provider adapter translates one application interface into a particular model
server protocol. Here `get_llm("ollama")` targets a local OpenAI-compatible endpoint;
`get_llm("groq")` still targets the existing hosted backend. An environment flag
cannot supply missing implementation by itself.

JSON Schema describes an output shape. Pydantic checks actual returned values: a
QA score outside1–5 is rejected rather than trusted because it looks like JSON.
For example, a synthetic billing dialog produces SummaryResult, then that summary
and transcript inform QAScoreResult. Code overwrites call ID and recalculates the
weighted score. A valid object could still contain a false explanation, so schema
reliability is not an accuracy measurement.

A retry repeats the same intended operation after failure. One budget avoids
multiplying retries inside another SDK loop. A timeout bounds a request's waiting,
not the total multi-attempt job or server cancellation. A receipt describes what
actually ran without retaining the customer's words. A mutable model tag names a
version operationally; its registry digest identifies exact cached content for the
benchmark. CPU offload lets a large model run beyond GPU capacity but changes speed
and GPU-memory comparisons. No neural weights change during inference.

## 7. Data structures, ML evaluation, security and privacy

Inputs are original typed redacted transcript/summary messages; outputs are the
same SummaryResult/QAScoreResult classes. No training split, new dataset or consent
assumption is introduced. ModelRuns are optional report metadata; public API omits
internal audio path and uses existing signed identity plus enabled database roles.
Synthetic English fixtures contain no private identities. The separate actual job
uses the previously accepted bundled sample and isolated test tenant/database/S3
prefix with ephemeral RSA identity, not a production authentication bypass.

Local endpoints are operator-controlled and allowlisted; no browser/API user can
submit arbitrary inference URLs or select a remote fallback. Proxy inheritance,
redirects and hosted-key reuse are disabled in the local client. Missing model,
connection, timeout and malformed schema failures stay explicit. Existing RLS,
owner isolation, object integrity, PII/injection and job deduplication tests pass.
Content-free new logs do not solve inherited provider/tracing/private-log risks;
keep tracing disabled for sensitive data. Local HTTP is suitable only for the
trusted host/project network. This is not production auth/TLS certification.
Model tags remain mutable at runtime; benchmark evidence records actual digests.
No ASR/LLM concurrent-GPU capacity or general model quality certification.

## 8. Tests, exact outputs and verification

| Check / command | Environment | Exit/result |
| --- | --- | --- |
| Initial tests/llm run before modules existed | uv Windows | Collection error: missing model_runs; explicit implementation gap, not claimed assertion-level regression proof |
| Initial integrated pytest | Isolated PG/Redis/S3, uv |292 passed/1 failed: stale OpenAPI snapshot; retained before-schema-refresh receipt |
| Final pytest tests/unit tests/security tests/api tests/integration tests/workers tests/llm -q --tb=short --junitxml=… | Real isolated services | **293 passed,0 failed,0 skipped in61.93s** |
| Final focused tests/llm -q --tb=short | Controlled HTTP + actual SDK | **17 passed in2.98s**, including final thinking/token assertions |
| Setup/manifest tests after runtime httpx declaration | uv Windows |10 passed; dependency check146 packages compatible |
| Ruff check src/services/tests/scripts/stubs/migrations/app.py | uv Windows |0; all checks pass |
| Ruff format --check same targets | uv Windows |0;129 files formatted |
| mypy src/ services/ app.py | uv Windows |0;65 source files |
| uv pip check; compileall; hardcoded-key check | uv Windows |0 each |
| Cached CPU/GPU image source-overlay builds | Docker |0 each; no dependency reinstall/network bypass |
| Actual bundled sample queue job | Docker CPU ASR + local Ollama Qwen7B, real PG/Redis/S3 |202 upload, queued/running/finished, attempt1, report/PDF200, same-key replay same job |
| Final deployed-source/hash/health checks | Docker + host |Both workers' reviewed source matches; app/API/PG/Redis/storage healthy; Gradio config200 |
| API default readiness | No real IdP configured |503 intentionally; no security bypass |

Raw command/result JSON, JUnit XML and operational receipts are under evidence.
The initial secret hook flagged non-secret prompt checksums and a deliberate dummy
userinfo URL used to test rejection. Public checksum fields use byte arrays;
historical JUnit labels normalize that dummy URI, and current test IDs name the
case explicitly. evidence-normalization.json records this representation change.
No status/metric was altered and no credential-detection rule was disabled.
A Starlette/AnyIO deprecation and pytest asyncio configuration warning remain
nonfailing. SDK constructor annotation mismatches were resolved with SecretStr and
the installed max_completion_tokens alias. An early HTTP test double incorrectly
patched a class boundary; it was corrected to inject MockTransport into a real
SDK client. The final transport tests exercise actual parsing and one request per
attempt. No failed run is relabeled successful.

A fresh registry-backed full dependency build was not re-proved here: the preceding
step recorded a certificate-routing failure. This step reused verified existing
CPU/GPU dependency images with current source overlays, recorded successful builds,
recreated only project app/API/workers, and compared their source hashes. No
Ollama daemon setting, unrelated service or data volume was altered.

## 9. Analytics and quantitative report

### Reproducible final local-model comparison

Command: `python -m scripts.benchmark_local_llm --output <new-directory>`.
Ollama0.32.4; cached Q4_K_M models; three synthetic English dialogs; summary+QA each;
temperature0,2048 output tokens, one attempt, serial, no ASR; mixed cold/warm calls.
Validity = successful original Pydantic contracts / attempted calls ×100.
p50 is the median; p95 is sorted index ceil(0.95*n)-1. With n6, p95 is the largest
observed value and cannot estimate a production tail reliably.

| Model | Valid / attempted | Schema valid % | p50 s | p95 s | Sampled whole-device maximum MiB | Memory samples |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen2.5-coder:7b |6/6|100|7.207|12.383|6326|166|
| qwen3.5:9b-q4_K_M |6/6|100|22.917|33.146|6324|512|

Ollama reported contexts32768 and65536 respectively. The9B run used CPU/GPU offload
(36%/64% shown by ollama ps); its lower resident GPU allocation is not evidence of
better intrinsic memory efficiency. `/api/ps` resident model bytes were6248223210
and5516904364 respectively; whole-device sampled maxima include other allocations
and are not process-isolated or guaranteed peaks. No server context was changed.
The7B model is code-tuned, not a matched general-assistant variant, so this is a
contract/operational comparison rather than a controlled model-family quality study.

A preceding9B summary request timed out at120.046s with an inappropriate thinking
control for this compatibility route. Partial observations are retained separately.
Switching to documented reasoning_effort=none preceded the successful final run;
other warm/load effects also vary, so do not attribute a numeric speedup solely to
that change. Do not omit the initial timeout when assessing operational reliability.
Hosted-provider comparative p95/accuracy, labeled summary/QA fidelity, WER, sustained
throughput, fairness and true peak per-process VRAM: **Not measured**.

### Actual queued local-model job

`local-worker-http.json`: upload202 in0.438s; completed execution29.087s;
request-to-verified-result30.436s; attempt1, no retries. Summary model receipt
16191.801ms; QA9619.316ms. Both structured outputs valid, model tag recorded,
prompt revisions f8898107c67d94c5 /8557debf6f039254, fallback none.
Authorized report/PDF200; duplicate key returns identical logical job. CPU ASR was
intentional so ASR and LLM did not compete for the8GB GPU. Primary preserved counts:
call_records4/calls4/segments124/audit_log4/transcription_cache1; external identities0,
analysis_jobs0. Test tenants/jobs are isolated. No new neural learning is claimed.

## 10. Questions with answers

1. **Why not only change LLM_PROVIDER?** The original factory had no Ollama branch
   and silently selected OpenAI. This step adds the client policy and makes unknown
   providers fail rather than cause unexpected hosted execution.
2. **Why use JSON Schema plus Pydantic?** Server constraints guide generation;
   application validation rejects a malformed or out-of-range result. Valid shape
   still does not establish truthful summary content.
3. **Why use a smaller Qwen first?** It limits resource risk on8GB and establishes a
   working local contract before testing9B. The cached code-tuned7B is an available
   operational candidate, not proof it is the best call-center language model.
4. **What do the measurements prove?** Both cached models produced6/6 valid contract
   objects on three synthetic English dialogs. The actual queued sample also passed
   CPU ASR/local inference/persistence/API/PDF, with measured receipts. Accuracy,
   multilingual robustness and production capacity remain unmeasured.
5. **What failed?** Initial missing-module tests, an OpenAPI snapshot mismatch,
   constructor/test-double iterations, and one9B120s timeout. Each was investigated;
   final code/schema/tests and corrected thinking control have direct passing evidence.
6. **Could local inference silently fall back to Groq?** No. Provider selection is
   explicit and no fallback code exists. Transport tests observe only the local host;
   receipts explicitly report fallback none.
7. **How are retries bounded?** The shared agent helper allows1–5 attempts and bounded
   exponential waits; local SDK retries are0. Timeout is per request, not a total job
   deadline. Hosted SDK behavior is preserved for compatibility rather than silently
   changing existing retry semantics.
8. **Can old reports still be read?** Yes. model_runs defaults to empty, original
   data fields remain, and tests decode legacy JSON and exercise PG-to-HTTP metadata
   through existing ownership enforcement. No destructive schema migration.
9. **Is the logged model version immutable?** No: it is a configured tag. Benchmark
   records additionally include the actual registry digest; production version
   pinning/model governance remains a later concern rather than an invented guarantee.
10. **Why no new Model Lab screen/screenshot?** This step supplies actual report data
    for the later frontend. No UI renderer changed; preserving the original Gradio
    baseline avoids pretending that a backend receipt implements a dashboard.
11. **Does6.3GB prove ASR and9B can run together?** No. Sampling is whole-device,
    contexts differ and9B offloads to CPU. The actual job serialized CPU ASR and GPU
    LLM; concurrency and sustained GPU pressure need their own explicit validation.
12. **Did the adapter train a model?** No. Cached quantized weights were used only
    for inference. No optimizer, gradients, training audio or claimed improvement.

## 11. Decisions, changes, problems and risks

- Reuse installed OpenAI-compatible LangChain client; avoid another server/SDK.
  Native Ollama could expose context/keepalive options, but changing its configuration
  or introducing a second inference path was unnecessary for this step.
- Keep hosted private defaults unchanged; local is explicit opt-in. Unsupported
  provider fallback changes intentionally to fail-safe rejection.
- Keep schema validation and resource/output budgets; accept safe failure rather
  than bypass validation or return partial fabricated JSON.
- Move common retries into one helper; change unsafe raw exception logging to fixed
  codes for this inference boundary. Existing unrelated logging is not rewritten.
- Use request-local report receipts instead of adding a model registry or migration.
  Failed jobs do not invent completed report metadata; API job errors stay sanitized.
- Runtime httpx pin is explicit because it is now a direct production import.
  Installed package set/version remains unchanged; dependency consistency passes.
- Risks: real OIDC absent; local HTTP trusted network only; original tracing/private
  log privacy; mutable runtime model tags; inherited retention/orphan cleanup;
  per-request rather than whole-job deadline; small synthetic English sample and
  different contexts; CPU offload; fresh clean registry build not revalidated.
  These are deployment/measurement limitations, not concealed failing acceptance gates.

## 12. Deliverables, next handoff and evidence checklist

- [x] Original three hosted provider constructor contracts and regressions pass.
- [x] Local Qwen outputs validate on fixtures; two actual cached variants compared.
- [x] Failures/retries/no-fallback are recorded safely and tested.
- [x] Completed report metadata survives graph/JSON/real PG/authorized HTTP.
- [x] Actual containerized queue job, duplicate replay and report/PDF validated.
- [x]293 tests pass;17 final focused cases; lint/types/dependency/compile checks pass.
- [x] Actual analytics, failed attempts, file/import explanation and upstream comparison.
- [x] Existing primary records and prior evidence integrity checked; no secrets published.
- [x] Progress and earlier report follow-on notes updated; no commit/push.

Next eligible implementation: **STEP_12 — inventory datasets and build
permission-aware splits**. It must read its own complete prompt and prerequisites,
retain analysis-versus-training consent separation and carry forward identity/model
version limitations. No STEP12 work or dataset acquisition was started here.
Safe current reproduction: `python -m pytest tests/llm -q` in the uv environment;
real PG/API checks additionally need private isolated URL fixture files.

## 13. Approved ERP UI design / visual contract verification

**Visual impact: Not applicable — backend inference, persisted receipts and additive
API schema only.** Read UI_DESIGN_SYSTEM.md / UI_ACCEPTANCE_CHECKLIST.md and visually
inspected both reference images; the primary remains
`design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png`. Its white rounded cards,
neutral canvas, dark text and green accents remain the future UI direction.

Actual affected route: existing authorized `/api/v1/calls/{id}/report` and analysis
Report response schema, plus public `/openapi.json`; no route/component renderer
or CSS changed. Future Model Lab/analysis details can display measured model tag,
version, valid/invalid/error, retries, latency and safe error code. Empty historical
receipts should be shown as unrecorded, not guessed; failure is not a success badge.
No prompt/transcript content is added to metadata and no fake numeric dashboard
values are copied from the reference.

Original Gradio remains accessible (config200) and its earlier style is preserved
as a regression baseline; this does not claim it already matches the ERP reference.
Color tokens, focus/keyboard/mobile layouts and contrast are unchanged and were not
newly browser-audited. Actual frontend screenshots were not captured because no
frontend changed. Reference images are design inputs, not implementation evidence.

**Final verdict: STEP_11 DONE — PASS WITH LIMITATIONS. STEP_12 eligible, not started.**


# Failure Analysis and Correction Report

Audit date: 2026-10-27, Africa/Casablanca. Target: current STEP11 implementation.
Evidence directory: `evidence/step11-correction-20261027T091952Z/`.
The implementation record above and its59 sealed artifacts remain historical evidence.
No separate STEP11 quality-review document was present; this audit used its report,
source/diffs, previous receipts and new direct reproductions. The previous verdict
was PASS WITH LIMITATIONS; no prior failed acceptance result is invented.

### A. Executive Summary

Four confirmed root-cause groups were reproduced and corrected: address-only
locality policy accepted remote-backed aliases; local sync clients stayed open;
constructor failure receipts could misidentify the selected model or echo rejected
free-form settings; and the benchmark returned success despite failed outputs.
Eight new regression cases pass. Final full regression:301 passed,0 failed/0 skipped
in50.93s; strict mypy65 source files, Ruff130 files, dependency/compile/key checks pass.
Fresh actual local7B/9B inference and a real Docker queue workflow pass.
**PASS WITH LIMITATIONS**; no next-step implementation or commit/push.

### B. Failure Inventory

| ID | Component / severity | Reproduction | Root cause | Final status |
| --- | --- | --- | --- | --- |
| S11-R01 | Local-model trust policy / P1 | Three remote/unverifiable metadata fixtures accepted by factory before correction | Only endpoint address inspected; no routing/weights metadata check | Fixed; blocked before SDK construction, real local models still work |
| S11-R02 | Sync HTTP lifetime / P2 | Client.is_closed false after success and exhaustion | No context/finally cleanup for agent-owned transport | Fixed; both lifecycle regressions pass |
| S11-R03 | Failure receipts / P2 | Environment-selected model reported as default; invalid setting echoed into receipt | Receipt selector diverged from factory and accepted free-form identifier | Fixed; shared selection plus bounded safe observation |
| S11-R04 | Benchmark execution gate / P2 |0% valid outputs yet normal successful return | Exceptions recorded as rows without aggregate exit gate | Fixed; receipts preserved then exit1; real successful run exits0 |

Machine-readable inventory: `failure-inventory.json`. Four groups identified,
four corrected/validated; zero unresolved confirmed defects in this audit.
R01 is a reproducible policy gap and potential privacy consequence, not evidence
that actual customer content was sent to a cloud provider. No cloud request or real
private content was used to test it. R02 demonstrates open clients, not a measured
production file-descriptor exhaustion or memory incident.

### C. Root-Cause Analysis

**R01:** Ollama supports remote-backed models even when contacted on localhost.
Its official ShowResponse includes remote_model and remote_host; a benign alias
name does not prove local weights. The previous branch constructed a chat SDK
without reading this metadata. Controlled responses declared a remote alias, a
remote host despite model_info, and empty metadata; all were accepted before fix.
Reference: [official Ollama API types](https://github.com/ollama/ollama/blob/main/api/types.go).
The correction fails closed before inference when model locality is unverified.

**R02:** Each local factory call supplied a new HTTPX sync client. Agent completion
and exception exits never called close. Explicit transport inspection after both
paths returned is_closed=false. Network pools need deterministic ownership even
when Python can eventually reclaim other objects. The runner owns its factory-created
sync client and now releases it on every exit; hosted client behavior remains.

**R03:** Initial receipt model_id used explicit override/default, while construction
also used the provider's environment override. When construction failed before the
client existed, the later model_name update never ran. A valid configured missing
model was therefore reported as qwen2.5-coder:7b. Sharing the selector fixes the
mismatch. An additional synthetic invalid setting then proved that raw rejected
configuration could be echoed into metadata; a bounded identifier representation
now reports unresolved instead of free-form input.

**R04:** Benchmark catches inference exceptions so it can preserve observations.
It previously stopped there: after writing0% validity, main returned normally.
A shell or CI runner saw success. The correction separates evidence persistence
from the aggregate success decision and fails the process if any observation fails.

### D. Code Corrections

`resolve_model_name(provider,model)` centralizes explicit > provider environment >
default selection. `get_llm` and failure observations share it. Hosted OpenAI/Gemini/
Groq constructors keep their existing model/timeout contract. `_observed_model_id`
accepts only bounded identifier syntax; other values become unresolved. Actual SDK
model_name updates pass through the same safe representation. This is not a secret
classifier for valid identifiers: model configuration is administrator-controlled.

`require_local_model(endpoint,model,timeout)` opens a short-lived HTTPX context,
posts only {model:identifier} to same-origin /api/show, raises HTTP errors, parses
metadata, and closes the inspection client. Its timeout is min(timeout,10)s;
redirects and environment proxies remain disabled. It requires a nonempty model_info
dict, details.format=gguf and absence of remote_model/remote_host. Missing, malformed
or remote metadata raises the safe LocalModelPolicyError; the SDK is never constructed
and transcript messages are not sent. No model download/daemon mutation occurs.
A returned JSON parse error or inspection transport failure also blocks inference.

`invoke_validated` wraps its existing loop in ExitStack. Immediately after local
factory creation, it registers the HTTPX sync transport's close callback before
structured binding. Return, exhaustion and binding exceptions leave through the
same cleanup boundary. It still reuses one bound client over its attempt budget.
LocalModelPolicyError maps to local_model_required; HTTPX timeout/network/status
errors now map to the same safe codes as corresponding SDK errors. Raw exception
bodies remain excluded. Other providers keep their old transport lifetime behavior.

The benchmark writes observations and final results first, then raises SystemExit(1)
if any row is invalid. Successful real comparisons return0. Inference outputs and
partial evidence are not deleted to satisfy the status gate; no model is promoted
based on this contract-only gate.

### E. Import and Dependency Analysis

- `contextlib.ExitStack`: new stdlib import in structured_inference; registers local
  transport cleanup once and guarantees execution across success/exception paths.
- `re`: new stdlib import there; bounds observed model identifiers and avoids logging
  rejected free-form settings. Factory's existing re import remains for input policy.
- `httpx`: existing pinned0.28.1 direct runtime dependency; additionally used for
  actual metadata inspection, transport type checks and safe exception classification.
- `LocalModelPolicyError,resolve_model_name`: local imports replace DEFAULT_MODELS
  lookup in the helper, providing explicit privacy failure and one selection rule.
- New regression file uses existing json/unittest.mock/httpx/pytest/ChatOpenAI,
  benchmark/agent/capture/fixture imports to exercise public paths with controlled
  metadata/HTTP failures. Actual models are tested separately.

No package/version/lockfile, model checkpoint, GPU driver or migration changed.
No new inference service, native Ollama SDK or training dependency was introduced.
Async inference is not implemented by this synchronous runner; direct factory
consumers remain responsible for their own client lifecycle.

### F. File-by-File Changes

| File | Correction |
| --- | --- |
| src/utils/llm_factory.py | Shared selector, local policy error, metadata preflight before local SDK |
| src/utils/structured_inference.py | Sync client cleanup, shared/safe model observation, HTTPX/policy error codes |
| scripts/benchmark_local_llm.py | Aggregate failure exit after persisting results |
| tests/llm/test_step11_corrections.py | Eight new regressions across four groups |
| tests/llm/test_local_provider.py | Two existing SDK/transport tests isolate metadata preflight; dedicated new tests exercise actual preflight separately |
| docs/development/local-models.md | Required metadata API, locality limits, cleanup and benchmark status contract |
| docs/implementation/PROGRESS.md | Current correction verdict and STEP12 unstarted |
| This STEP11 report | Preserve history, append this A–O record and current audit note |
| New correction evidence directory | Red/green receipts, intermediate/final checks, benchmark/job, hashes/diffs/imports/Git summaries and seals |

No files deleted/renamed in product code. Ignored helper scripts performed packaging
and isolated runtime checks; .env, credentials, existing data and private logs remain
private. General Git diff contains earlier uncommitted STEP01–11 changes; dedicated
before/after snapshots and diffs separate this audit's modifications.

### G. Original versus Improved Repository

Upstream remains fed4b610742c1337147281fcec8f2cdcc0a79be5; current HEAD remains
a37e4634af1d2947fc3c548d54e62bda0b0daf89 on feature/project28-foundation.
The original factory implemented only hosted providers and no local benchmark or
model receipts. This audit corrects the added STEP11 adapter, not the original
hosted constructors. Original summary/QA result types, trusted ID override, scoring
weights, LangGraph order, PII/injection behavior, Gradio and PDF generation remain.
Model selection environment support from earlier steps is now shared with receipts.
No schema migration or destructive record update is needed. New error code values
fit the existing optional string field; authorized HTTP response structure is stable.

### H. Architecture Impact

Flow becomes validated local address/model setting → metadata-only inspection →
local structured SDK inference → original Pydantic validation → safe receipt →
owned sync transport cleanup. The original graph/queue/database/API boundaries
stay in place. Inspection adds one small local HTTP request per constructed client,
not per transcript segment; failed attempts with a bound client reuse it. It adds
up to10s inspection wait before the configured inference request timeout, not a
whole-job deadline. The daemon must support its native metadata API as well as the
OpenAI route; a generic OpenAI-only proxy is no longer sufficient for local privacy.

This trusts the local daemon's truthful metadata and trusted administrator. It
cannot prevent a malicious daemon or alias retarget between inspection/inference;
network egress enforcement and immutable model governance remain deployment work.
Local non-GGUF backends are intentionally unsupported until explicitly validated.
No existing Ollama service was stopped/reconfigured and no model was pulled.

### I. Tests and Validation

- `red.json`: seven focused cases failed in1.69s across the four original groups.
- `red-invalid-model-receipt.json`: additional R03 variant failed in1.47s.
- `green-final.json`: all eight corrections pass in1.88s.
- Final full pytest across unit/security/API/integration/workers/llm:
  **301 passed,0 failed,0 skipped in50.93s**, JUnit+raw command receipts retained.
- Ruff passes;130 files formatted; strict mypy passes65 source files.
- uv dependency consistency, compileall and hardcoded-key checks pass.
- Initial corrected intermediate suite300 passed in45.39s. During the additional
  R03 correction, an indentation mistake caused seven collection errors and static
  failures. The one-line indentation correction restored focused/full green; all
  intermediate failed receipts are retained rather than overwritten.
- Two cached dependency image source-overlay builds and project-only restart pass;
  CPU/GPU deployed source hashes match host. No TLS verification bypass or fresh
  registry dependency-rebuild claim. Earlier registry-build limitation remains.
- Final Gradio config200; API health200; ready503 intentionally without real OIDC.
  Primary counts preserved:4 call_records/4 calls/124 segments/4 audit rows/1 cache,
  0 primary external identities/0 primary analysis jobs. PG/Redis/S3/app/API healthy.
- Fresh actual Docker job: CPU tiny ASR → local Qwen7B with metadata inspection →
  PostgreSQL result; upload202, queued/running/finished, attempt1, report/PDF200,
  same-key replay same job, two valid local model receipts. Isolated test database/
  tenant and ephemeral RSA identity; no production identity bypass.

The existing Starlette/AnyIO deprecation and pytest asyncio configuration warnings
remain nonfailing. No frontend changed; browser visual validation is not applicable.
No new vulnerability scan or production penetration-test certification is claimed.

### J. Performance and ML Metrics

Fresh comparison: same three synthetic English dialogs, summary and QA each,
serial one-attempt requests, existing Q4_K_M cached models, Ollama0.32.4, RTX4060
Laptop8188MiB; metadata inspection enabled. The invalid-model log formatter was
hardened during this audit without changing valid-model inference; final Docker
workflow runs the final source. No weights or prompts were changed.

| Model | Schema-valid/attempted | Valid % | Median s | Nearest-rank p95 s | Sampled whole-device maximum MiB | Samples |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen2.5 Coder7B |6/6|100|7.184|8.200|6138|147|
| Qwen3.5 9B |6/6|100|26.458|33.446|6328|537|

The original STEP11 measurements above remain historical. With only6 observations,
p95 equals the largest observation; different warm/loading/context/offload conditions
prevent causal speedup/regression claims. Sampling includes all device processes,
can miss short peaks and is not isolated per-model maximum. Different contexts and
9B CPU offload still confound direct GPU-memory comparison. No learned model quality,
WER/accuracy, sustained throughput or concurrent-ASR capacity improvement was measured.

Fresh queued sample: upload0.399s; execution28.889s; total30.339s; no retries.
Summary/QA receipts15269.790/10238.935ms; both valid; report/PDF200. These are single
observations, not an SLA. Benchmark failure-gate unit uses controlled failed calls
and persists0% validity with exit1; actual successful comparison exits0. Complete
subprocess wall time was not separately captured for that comparison; individual
measured request times are retained.

### K. Security Analysis

R01 closes a reproduced privacy policy hole without configuring or contacting an
actual cloud model. Synthetic remote metadata is rejected before SDK construction;
only the model ID is posted locally during inspection. No uploaded audio/transcript
is included in metadata lookup. Hosted providers remain explicitly selectable under
their existing policy; no implicit fallback is added. Address/proxy/redirect guards
remain. Malformed/rejected model text is not copied into failure receipts.

Full security/API/RLS/owner/upload/injection/integrity tests pass. Primary external
access remains fail-closed until a real OIDC provider exists. User-held provider
credentials, private SQL URLs and logs are excluded from evidence. Source/checksum
seals verify historical receipts were preserved, not that old source files still
match current intentionally corrected source. No training permission, real-user
role, object policy or model deployment approval was invented.

Remaining trust limits: malicious/mutating local daemon, mutable runtime tags,
trusted-network HTTP, original tracing/private-content logs, production ingress/
rate limits and object retention. Closed HTTP pools reduce a lifecycle risk; this
is not a new authorization or encryption guarantee.

### L. Concepts Explained

Local address and local computation are different properties: a local service can
forward a request elsewhere. Metadata is checked before sensitive input is sent,
rather than discovering remote routing after the model has already answered.
Fail-closed means missing evidence blocks the request rather than assuming safety.

An HTTP client owns reusable network connections. A context cleanup boundary closes
them even when a function returns early or raises. ExitStack gathers these cleanup
actions and executes them automatically. One selector prevents two components from
disagreeing about which model was requested. Safe observation represents invalid
configuration as unresolved without pretending another model actually ran.

A benchmark needs both evidence and an exit decision. Catching failures lets it save
the evidence; returning a nonzero status ensures automation cannot mistake failure
for success. Neither schema validity nor a successful process means a model's
answers are factually correct or that it has learned anything.

### M. Questions and Answers

1. **Why was localhost insufficient?** Ollama may serve remote-backed aliases through
   the local listener. Before this correction, the adapter checked the address but
   never inspected model routing. No actual customer leak was established by the test.
2. **How was this reproduced safely?** Controlled HTTP metadata declared remote_host/
   remote_model for an innocent alias. The pre-fix factory still constructed the SDK;
   the fixed path rejects it before any transcript request. No cloud account needed.
3. **Why require nonempty local GGUF metadata?** It provides an explicit supported
   local-weight contract. Empty/unknown metadata is not affirmative proof of locality.
   Other backends need deliberate compatibility validation rather than permissive fallback.
4. **Can the check stop a malicious administrator?** No. The daemon and operator are
   trusted. Metadata can be dishonest or an alias can change after inspection; stronger
   egress controls and immutable configuration belong to deployment governance.
5. **Why use ExitStack?** The agent can return a valid result, retry, fail binding or
   exhaust attempts. A shared cleanup boundary covers all those exits while retaining
   the existing reusable client over retries. Sync close is proven on success/failure.
6. **Are hosted clients changed?** No. Their constructor parameters and lifecycle
   behavior are preserved; cleanup registration applies only to actual local HTTPX
   sync transports. Existing hosted-provider constructor and agent tests pass.
7. **Why did failed receipts name the default model?** The client-independent receipt
   initialization skipped provider-specific environment selection. Sharing the factory
   selector makes construction and observation agree even if construction fails.
8. **Why not log every rejected model setting?** Invalid free-form configuration can
   contain unintended private text. Receipts keep a bounded identifier or unresolved;
   safe error codes retain diagnostic meaning without echoing arbitrary strings.
9. **Why did an all-failed benchmark exit successfully?** It caught inference errors
   and saved rows but had no aggregate failure condition. It now saves the same rows
   and exits1 when any observation fails; successful real runs remain exit0.
10. **Does the new measurement show an optimization?** No causal claim is justified.
    Workload count is small and load/warm/offload conditions vary. The correction adds
    a metadata lookup; its purpose is trust and correctness, not claimed speedup.
11. **Which imports matter?** ExitStack handles ownership; re bounds observed IDs;
    existing HTTPX provides metadata/transport error types; local selector/policy error
    replaces duplicated model choice. No new package/version/model is installed.
12. **What remains before the next step?** STEP11's contract/regression/model gates
    pass. STEP12 is eligible for its own prompt. Real IdP, production security/load,
    model immutability and clean registry-build validation remain documented limits;
    no STEP12 dataset/training work was started in this audit.

### N. Remaining Problems

No unresolved confirmed code defect from this audit. Real OIDC, production ingress/
TLS/rate limits, retention/orphan cleanup and inherited private log/tracing risks
remain. Local daemon metadata is trusted; alias mutation and immutable runtime
version pinning are not solved. Non-GGUF local model providers are rejected. Direct
factory consumers manage their own lifecycle; this helper exercises synchronous
inference. Fresh registry-backed dependency build and sustained/model-quality/
concurrency benchmarks remain unverified. These limits do not alter the reproduced
red/green results or claim production readiness. UI status remains backend-only N/A.

### O. Final Quality Verdict

**STEP11 — PASS WITH LIMITATIONS.** Four confirmed failure groups corrected and
validated; eight new cases,301 final tests pass, actual local model and Docker
workflow evidence retained. Zero unresolved confirmed failures. Prior records and
sealed evidence preserved. STEP12 eligible, NOT STARTED. No commit or push.
