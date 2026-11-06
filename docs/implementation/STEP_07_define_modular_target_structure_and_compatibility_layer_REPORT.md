# STEP_07 — Modular target structure and compatibility layer

> **DONE — PASS WITH LIMITATIONS.** Date: 2026-10-24, Africa/Casablanca.
> **Latest correction: 2026-10-25.** Full strict mypy and Docker startup errors
> are resolved;175 tests pass. See the follow-up correction record at the end.
> Lead: Platform. Windows11/PowerShell, uv-managed Python3.12.15; Docker Linux runtime.
> Branch `feature/project28-foundation`; working HEAD
> `a37e4634af1d2947fc3c548d54e62bda0b0daf89` plus documented uncommitted work.
> Original upstream `fed4b610742c1337147281fcec8f2cdcc0a79be5`.
> User's STEP_X07 interpreted as STEP_07, matching their final instruction.
> [Prompt](../../prompts/STEP_07_define_modular_target_structure_and_compatibility_layer_PROMPT.md),
> [template](../../report_templates/STEP_07_define_modular_target_structure_and_compatibility_layer_REPORT.md).

## 1. Objectives, prerequisites and completed work

STEP_06 now has genuine native/Docker Gradio analysis, report downloads and current
PASS WITH LIMITATIONS; its missing credential blocker is resolved. Read master,
full STEP_07 prompt/template, preceding reports/architecture, source, manifests,
Docker configuration and Git changes before implementation. The earlier blocked
STEP_07 report is preserved as a [historical snapshot](evidence/step07-20261024T201609Z/previous-blocked-report.md),
whose relative links describe its original location. This report supersedes that
blocked status; no history is rewritten or step falsely skipped.

Implemented an injectable shared analysis service, lightweight request/result and
port contracts, an internal future-API adapter, Gradio rewiring, package-discovery
correction, import/cycle mapping, compatibility tests and transition architecture.
Kept one existing analysis/persistence/export implementation. Rebuilt only the
project app container; PostgreSQL, Ollama and unrelated services were not reconfigured.
No FastAPI routes/auth, PostgreSQL migration, worker, new web UI or training claimed.

## 2. Actual upstream versus modified architecture

| Path/symbol | Original at pinned upstream | Actual STEP_07 behavior | Compatibility |
|---|---|---|---|
| `src/ui/tabs/analyze.py::build_analyze_tab` | Callback calls process_call directly | Constructs AnalysisService with existing runtime dependencies; callback calls analyze | Same components, inputs and six outputs; upload/mic remain filepath |
| `src/services/pipeline.py::process_call` | Owns graph, persistence, formatting and exports | Still owns them; returns typed report alongside old fields | Existing function signature and numpy-tuple support retained |
| `PipelineResult` | Seven-field dataclass in pipeline module | Canonical contracts class, same first seven fields/order/defaults plus optional report | Legacy pipeline import reexports identical class; internal dataclass extension, not changed HTTP schema |
| `src/services/analysis.py` | Absent | Injected workflow/engine/audit and lazy legacy invocation | No model/database/UI/config setup on import/construction |
| `services/api/analysis.py::analyze_call` | Absent | AnalysisPort consumer returns CallReport or AnalysisError | Internal Python adapter; future HTTP authorization remains required |
| `src/graph/state.py` and summary/QA source | Existing Pydantic models, weighted rubric | Byte/schema unchanged from STEP_06; all graph logic retained | JSON-schema equality verified for summary, QA and report |
| `pyproject.toml` discovery | Auto-discovered wheel exports agents/graph/services without src | Explicit src/src.* and services/services.* discovery | Fixes canonical src.* installation; accidental old wheel top-level aliases are not supported |
| `Dockerfile`, CI | Original source copies/check scopes | Copies API package; lint/format/compile include new boundaries | Same runtime requirements and service configuration |

[Transition architecture](../architecture/transition.md) documents current versus
planned boundaries, interfaces, ownership and the approved AppShell contract.
Only the API directory needed now was created. apps/web, services/workers and ml
are documented future boundaries, not empty directories presented as implementation.

## 3. Every new/modified file and purpose

| File | Action and responsibility | Verification |
|---|---|---|
| `src/services/contracts.py` | New AnalysisRequest, PipelineResult, AnalysisPort, AnalysisError | Compatibility, failure, import and wheel tests |
| `src/services/analysis.py` | New WorkflowPort/AuditPort and AnalysisService | Shared execution, wrong-result rejection, guarded imports |
| `services/__init__.py`, `services/api/__init__.py` | New transport package boundaries | Source/installed-wheel imports |
| `services/api/analysis.py` | New internal typed-report adapter | Same report identity, failed/missing report errors |
| `src/services/pipeline.py` | Reexport moved result class; populate report field on success | Legacy/shared/API and existing export regressions |
| `src/ui/tabs/analyze.py` | Route callback through injected service | Real rebuilt Gradio callback and unchanged six outputs |
| `scripts/map_project_imports.py` | New AST/static dependency mapper and Tarjan SCC analysis | Synthetic cycle/relative import tests, actual source maps |
| `tests/unit/test_analysis_compatibility.py` | New 11 cases: six consumer/status combinations, two failure states, missing input, wrong result and import guard | Full suite and focused execution |
| `tests/unit/test_import_map.py` | New two cases: nonexecuting cycle and relative resolution | Focused/full suite |
| `pyproject.toml` | Explicit Python package discovery | Reproduced failed old wheel, clean fixed-wheel install |
| `Dockerfile` | Include services package | Rebuild, original app import and live analysis |
| `.github/workflows/ci.yml` | Expand existing Ruff/compile scopes | Equivalent checks executed locally; remote CI not claimed |
| `docs/architecture/transition.md` | New module/transport/packaging/security/UI migration contracts | Reviewed against actual implementation |
| `docs/architecture.md` | Identify original diagrams as baseline; link current transition | Link/source review |
| This report, progress, STEP_06 handoff, feature-matrix note and evidence | Actual results and ordered next-step readiness | Links/hash seal and tracker checked |

No application source removed, runtime dependency added or dataset modified.
Generated wheel/build targets and client downloads are ignored under .local/build;
old generated build output was archived intact under .local to avoid stale-wheel
contents. The existing editable project metadata was refreshed with uv --no-deps.

## 4. Important code, classes, functions and data flow

`AnalysisRequest` is a frozen dataclass carrying trusted audio path and optional
caller/department metadata. It validates no public upload ownership; that belongs
to a future authenticated transport. None intentionally reaches the legacy missing
input behavior. Gradio already produces paths for both supported audio sources.

`PipelineResult` preserves original fields and adds `report: CallReport | None` at
the end. Its old pipeline import points to the same class. Existing callbacks still
select transcript, summary, QA and download paths explicitly. Consumers serializing
the whole internal dataclass must account for the additive field; the public
Pydantic report schema is unchanged. No pickle compatibility guarantee is invented.

`AnalysisService` receives initialized collaborators rather than constructing them:

```python
result = process_call(
    request.audio_file, request.caller_id, request.department,
    self.workflow, self.engine, self.audit,
)
if not isinstance(result, PipelineResult):
    raise TypeError("Legacy pipeline returned an unsupported result")
return result
```

The import of process_call occurs inside analyze, so importing/constructing the
service does not load reporting/database/model/UI modules. The guard rejects an
unexpected collaborator contract. Existing process_call owns validation, graph
invocation, errors, persistence and export lifecycle; its summary/QA algorithms are
not copied. Engine/audit ownership remains with bootstrap, not this wrapper.

The API adapter accepts AnalysisPort, invokes it once, rejects failed/missing report
results and returns the same typed report object. It raises AnalysisError, not a
transport-specific HTTP response. A future FastAPI route must authenticate, resolve
managed resources and translate/sanitize errors before returning a Pydantic response.
`flagged_for_review` is preserved in report.status even when a report was produced;
computational success does not mean human approval.

`map_imports(root)` discovers src/services modules, parses AST without imports,
resolves local absolute/relative module references and builds an adjacency list.
Tarjan depth-first traversal tracks discovery indexes, low links and a stack to
identify multi-module or self-loop strongly connected components. Nested and
type-only imports are included conservatively. Dynamic imports, implicit parent
initializer execution and external-package cycles are not measured. Complexity is
linear in parsed source plus graph vertices/edges for this small repository.

Setuptools discovery now packages canonical src.* and the explicit services.api
package. The old wheel's failed import is independently reproduced under isolated
Python outside the checkout. The corrected wheel omits tests/scripts and accidental
agents/graph root names. Isolated import needs no runtime dependencies because these
entrypoints are lazy; actual analysis still requires declared dependencies.

## 5. Imports and dependency explanations

No third-party dependency or version added. Python3.11+ stdlib supplies dataclass
for request/result/service records, Path for trusted paths, Protocol for structural
interfaces, TYPE_CHECKING for deferred annotations, Mapping for workflow inputs/
outputs, and built-in exceptions. SQLAlchemy Engine and local CallReport imports
are type-only in new entrypoints. Local contracts are runtime imports; the legacy
pipeline import is lazy. This preserves import safety without a plugin/container
framework or a new network service.

The mapper uses ast for syntax traversal, json for evidence output, Path for source
files and TypedDict for its structured result. Tests use existing pytest8.3.5,
stdlib uuid/json/pathlib, unittest.mock for controlled workflows, os/sys/subprocess
for a fresh guarded process, and existing synthetic factories. Import audit hooks
forbid connections, subprocesses, writes/mkdir/removal while importing entrypoints;
assertions also exclude Gradio/faster-whisper/SQLAlchemy/config modules.

Existing mypy1.15.0 and Ruff0.11.8 remain. uv builds with the already-declared
setuptools backend in isolated build environments; it does not install that backend
as an application runtime requirement. Existing gradio-client1.10.0 exercises the
real registered callback. Docker retains all existing runtime pins and cached models.

## 6. Concepts explained from first principles

A modular monolith is one deployable application with explicit internal boundaries.
An adapter translates a consumer's interface to existing behavior. A Python port is
an expected interface, not a TCP port: AnalysisPort says callers may analyze a request
and receive a result without depending on a concrete graph or UI. Dependency
injection passes workflow/engine/audit into the service; dependency inversion lets
the transport depend on a protocol rather than model initialization details.

For example, Gradio needs formatted fields and download paths, while a future API
needs CallReport. Both invoke the same service and receive the same analysis; only
presentation differs. Deterministic synthetic tests check this without paying for
or confusing nondeterministic language-model outputs with a compatibility oracle.
A graph cycle means a static dependency path returns to its starting module; type-
only/deferred cycles need interpretation rather than automatically implying failure.
A wheel is an installation artifact: working from a repository directory does not
prove that its packaged imports work elsewhere.

## 7. Data, security, performance and reliability

No new public HTTP endpoint or permission boundary. Requests are trusted internal
paths; never forward arbitrary external filesystem paths into them. Future routes
need identity, per-resource authorization, managed uploads and sanitized failures.
Existing Pydantic contracts, QA weighting, PII stages, cache, audit and report logic
remain. Legacy raw pre-redaction cache, incomplete address/PII masking, mutable audit,
best-effort persistence and completion-before-export metrics remain limitations.
This step does not claim to fix those independent concerns.

Tests use synthetic audio/report fixtures; the real smoke uses the already approved
bundled educational/testing recording and existing Groq credential privately. Raw
exports stay ignored; screenshots exclude transcript/customer fields. No new model
weight/data download, GPU-heavy operation, training, registry or promotion occurred.
A single delegated call adds a small Python wrapper, not a distributed hop; its
specific overhead was not isolated or benchmarked. New imports perform no runtime
setup; app.py's existing bootstrap side effects are intentionally retained/tested.

## 8. Actual tests, static analysis and acceptance gates

| Check | Actual outcome |
|---|---|
| Full pytest tests/ -q --tb=short | **165 passed in22.10s**, zero failed/skipped; original regressions included |
| Focused new compatibility/import map suite | **13 passed in1.26s** after corrections |
| Ruff check src/ services/ tests/ scripts/ app.py | Exit0, strict lint passes |
| Ruff format --check same scope | Exit0,76 files formatted |
| Targeted mypy --follow-imports=skip on four new modules/tools | Exit0; checks new files with imported implementation bodies excluded |
| Full mypy src/ | **Exit2, FAIL**: same six initial errors/three files before abort; not suppressed |
| Original app import/build in rebuilt Docker | Exit0, actual cached tiny model loads and demo builds against isolated temporary SQLite path |
| Guarded new service imports | Pass; no filesystem writes, database/network/process setup or heavy runtime imports |
| Original wheel isolated import | Expected exit1: no module named src, defect reproduced |
| Corrected wheel isolated import | Exit0 outside checkout; new entrypoints found with no runtime setup |
| uv pip check / readiness diagnostic | Pass, all22 direct/dev pins match; no new dependency version |
| Existing four hooks plus explicit new-source detect-secrets | All pass; no scanner weakened |
| Compile app.py src/ services/ and whitespace | Exit0 |
| Schema/source preservation | SummaryResult, QAScoreResult and CallReport schemas equal; app/state/summary/QA source hashes match pre-step capture |

Initial focused tests already passed but exposed two lint/layout findings (exception
suffix and a long line); corrected names/format. Targeted typing exposed mapper
collection annotations and an Any legacy-boundary return; added explicit annotations
and the checked result contract. Those are corrected; full-app inherited typing
failure remains. No ignored test/failure is called passed. Remote CI not executed.

All three step gates pass: original app imports, directory boundaries documented,
and new service entrypoints import without setup. The import smoke uses source app.py
in Docker; the wheel test separately verifies installed service packages, not a
packaged app.py command or inference without dependencies.

## 9. Analytics, runtime and benchmark evidence

| Metric and sample scope | Actual observation | Interpretation |
|---|---|---|
| Static modules/edges, pinned original | 33 modules,47 edges,0 cyclic components | AST src-only baseline |
| Static modules/edges, current src plus API package | 38 modules,54 edges,0 cyclic components | Added boundaries, no static cycle detected |
| Installed import failure | One original-wheel attempt fails; one corrected-wheel attempt imports new entrypoints | Reproduced packaging improvement, not model performance |
| Canonical business implementation copies | process_call, run_summarization, run_qa_scoring, compile_report each defined once | Scoped duplication check, not universal code-clone metric |
| Real Gradio callback after migration | **7.8365s**, one upload+callback+download request | Includes an existing transcription-cache path; not controlled latency/p95 |
| Real report |31 segments; QA2.65; completed | Model-generated observation, not accuracy or improvement |
| JSON/PDF downloads |13,359 bytes /3,124 bytes; valid schema/UTF-8/PDF signature | Actual artifacts; PDF glyph/accessibility not certified |

Real call ID `937a4048-7e4d-4bf9-ae5a-0c1ed9d0c741`; the sample digest equals
STEP_06's recording. Weighted QA independently recomputed and matches. Same six
Gradio callback outputs remain nonempty on success. Nondeterministic hosted summary/
QA differs from the earlier3.05/3.2 observations across runs; deterministic
fixtures and exact schemas, not those stochastic values, establish compatibility.
No quality label, WER/DER/F1, p95, throughput, wrapper overhead or peak VRAM measured.
Server log summary confirms a transcription-cache hit (ASR node0.0s),7.5s
summary/QA, one provider HTTP400 followed by two HTTP200 responses and no429.
Existing bounded retry recovered; the initial structured-provider failure is
retained as an observed reliability limitation, not hidden as a clean first attempt.
Raw failed-generation content was not published. See runtime-log-summary.json.

## 10. Technical questions and detailed answers

1. **Why not rewrite the pipeline?** It already centralizes analysis/persistence/exports. Delegating preserves tested behavior and avoids a second QA implementation.
2. **What does dependency injection change?** The service receives resources built by bootstrap. Tests can supply controlled collaborators, and future transports can share the same runtime without importing app.py.
3. **Why keep a legacy result alias?** Existing imports and positional construction remain valid. The optional report is appended so old fields stay stable; full dataclass serialization gains that field and must be reviewed by new consumers.
4. **Does the API adapter create FastAPI?** No. It is an internal protocol consumer; HTTP identity, ownership, uploads, response errors and server factory belong to STEP_09.
5. **Why lazy imports and TYPE_CHECKING?** Tools/transports can inspect contracts without loading models or reading configuration. They defer runtime implementation loading until an actual analysis is requested.
6. **Why fix packaging now?** A verified old wheel cannot import canonical src.* outside the checkout. Explicit discovery makes the architecture installable rather than dependent on a working-directory accident.
7. **How do tests establish unchanged QA?** Controlled reports preserve exact dimensions/summary/status/export payloads across three callers, and the original weighted-scoring suite still passes. Live model wording/score is not a deterministic oracle.
8. **Why retain flagged_for_review?** A computed report may still require human review. Flattening that status to approval would alter business semantics and mislead future interfaces.
9. **What does the import graph omit?** Dynamic imports, implicit package-initializer effects and external cycles. Runtime import guards and actual app/wheel smoke checks cover separate observable risks.
10. **Why no empty apps/web or ml tree?** Those boundaries need no implementation yet. Their ownership and UI/data contracts are documented rather than presented as fake working services.
11. **What remains risky?** The inherited privacy/cache/audit/export-order and full typing issues. A small adapter does not provide authentication, durable jobs or production guarantees.

## 11. Decisions, problems, corrections and remaining limitations

Selected a modular monolith, structural protocols and stdlib dataclasses; avoided a
DI framework, duplicate graph, new provider and premature microservices. Preserved
the original entrypoint and visual baseline. Build isolation handles existing
setuptools requirements; runtime dependencies unchanged. Existing editable metadata
refreshed. Old generated build output archived to prevent stale packaging contents.

The initial package failure is fixed and both before/after evidence retained.
Current Ruff/new-module typing/import/compatibility gates pass. Whole-project mypy
remains failed and the restricted targeted check does not replace it. Old accidental
wheel root aliases are not compatibility promises; canonical src.* paths are the
supported repository imports. Provider free-tier/network limits and nondeterminism
remain. No commit/push or adjusted timestamp schedule performed.

## 12. Deliverables, evidence and next-step readiness

Primary evidence:

- [Before-source hashes](evidence/step07-20261024T201609Z/source-before.json), [old wheel failure](evidence/step07-20261024T201609Z/packaging-before.json), [fixed wheel](evidence/step07-20261024T201609Z/packaging-after.json).
- [Upstream import map](evidence/step07-20261024T201609Z/imports-upstream.json), [current map](evidence/step07-20261024T201609Z/imports-current.json).
- [Before schemas](evidence/step07-20261024T201609Z/contract-schemas-before.json), [after schemas](evidence/step07-20261024T201609Z/contract-schemas-after.json).
- [Tests/static/app/Git commands](evidence/step07-20261024T201609Z/validation.json), [compile/hooks checks](evidence/step07-20261024T201609Z/delivery-checks.json).
- [Live Gradio result](evidence/step07-20261024T201609Z/live-gradio.json), [summary](evidence/step07-20261024T201609Z/summary.json), [artifact seal](evidence/step07-20261024T201609Z/seal.json).
- [Transition contracts](../architecture/transition.md).

Checklist: implementation exists; compatibility/import tests executed; packaging
failure reproduced/fixed; original app imports; exact schemas preserved; screenshot
baseline captured; no invented model metrics; limitations retained. STEP_08 is the
next eligible implementation step. Existing PostgreSQL is available, but no schema
migration/import/recovery is marked done. API/auth/worker steps remain unimplemented.
Stop here for the user's next instruction; no advancement to STEP_08 in this task.

## 13. Approved ERP UI design / visual contract verification

Gradio is rewired internally but its visible components, status banners and six
callback outputs are preserved. No CSS, color token or new UI route introduced.
Actual [empty screen](evidence/step07-20261024T201609Z/gradio-empty.png),
[history](evidence/step07-20261024T201609Z/gradio-history.png),
[observability](evidence/step07-20261024T201609Z/gradio-observability.png) show the rebuilt application after
shared-service execution, without transcript/customer content or credentials.
History includes the new completed row; dashboard shows two stored calls and two
audit events. Those are stored-run metrics, not a request/export success benchmark.

Compared with the approved Commercially reference: original dark/purple Gradio still
differs from light neutral background, rounded white cards/sidebar, dark text and
green actions. This is preserved original baseline, not product design acceptance.
The transition document explicitly defines the future shared AppShell, accessible
components, navigation landmarks, focus/keyboard/reduced-motion behavior and
loading/empty/error/review/completed contracts. It does not claim React components
already exist. Mobile, contrast, full keyboard and responsive acceptance await the
frontend steps. No redesign is silently added to this architecture step.

**PASS WITH LIMITATIONS — ready for STEP_08.**

# Failure Analysis and Correction Report

### A. Executive Summary

Revalidated on **2026-10-25** following the attached automated-diagnosis request.
STEP_07 is the latest implemented step; the older quality-review FAIL at
19:50 UTC on October 24 was a prerequisite preflight, preceding the subsequently
implemented and validated adapters. It is preserved, not treated as today's result.
Working HEAD remains `a37e4634af1d2947fc3c548d54e62bda0b0daf89`;
upstream remains `fed4b610742c1337147281fcec8f2cdcc0a79be5`.

Fresh execution found **three failure groups: one verification defect corrected,
two unresolved non-blocking limitations for STEP_07**. No new production defect
was established. All **165 tests pass in 25.79s**. The original app imports and
builds natively with cached tiny CPU/int8 inference resources. New entrypoints
still import without setup. Whole-project mypy still fails. Docker Desktop now
fails to start, so current container health/end-to-end checks cannot pass.
STEP_07 retains PASS WITH LIMITATIONS; restore Docker before executing STEP_08's
database migration. No next-step implementation was attempted.

Evidence directory: [fresh revalidation](evidence/step07-revalidation-20261025T073355Z/).
All 18 previously sealed artifacts and all 17 recorded implementation/document
hashes matched before this documentation update. The earlier report is copied to
`report-before.md`; original logs and failed attempts remain intact.

### B. Failure Inventory

| ID | Failure | Component | Severity | Reproduction | Root cause | Status |
|---|---|---|---|---|---|---|
| RV07-01 | Old wheel incorrectly appears importable in today's recheck | Verification isolation | P3 | `wheel-before.json`: exit0 with `-I` | Refreshed editable installation is loaded through site initialization and supplies missing source packages | Corrected verification: `-I -S` reproduces missing src; fixed wheel passes |
| RV07-02 | Full application type check aborts | Inherited typing/dependency compatibility | P2 | `full-mypy.json`: exit2, six initial errors in three files | Missing ReportLab/faster-whisper typing metadata, absent optional torch, NumPy stub syntax exceeds configured Python3.11 target | Unresolved; same previously documented failure, not a new adapter regression |
| RV07-03 | Docker engine unavailable; container checks fail | Local Docker Desktop environment | P2 | `app-import.json` and `compose-health.json`: exit1; Desktop launch also fails | Secrets Engine cannot access/rename its existing engine.sock during startup | Unresolved; no destructive Docker reset or state alteration attempted |

Counts refer to this revalidation, not all historical development findings. The
old wheel packaging defect was already corrected during implementation; today's
wheel-only comparison validates that correction again. The historical provider
HTTP400 recovered through existing retry and is retained as a separate observed
reliability risk; it was not reexecuted or falsely counted as newly corrected.

### C. Root-Cause Analysis

`-I` removes ordinary working-directory/PYTHONPATH influence but still initializes
site packages. After the editable installation was refreshed, its import hook
provided canonical `src.*` even when the inserted old wheel target lacked src.
The initial exit0 therefore did not establish that the old wheel was correct.
Adding `-S` disables site initialization. With only the selected target inserted,
the old artifact fails with `ModuleNotFoundError: No module named 'src'`; the fixed
artifact imports both service and API adapter. Both commands run outside the
checkout under `.local`. This distinguishes packaging behavior from environment
leakage without reverting source or uninstalling the user's project.

The full mypy errors arise before comprehensive source analysis. Installing stubs
alone would leave the NumPy target mismatch and additional inherited typing debt.
Changing the supported Python target, installing an unnecessary training runtime
or suppressing dependency checks would not establish correctness. New-file mypy
passes with its limited scope explicitly recorded.

Docker's missing Linux named pipe is a symptom. The host backend log identifies
the startup cause: `starting services: initializing Secrets Engine`, followed by
failure to rename `engine.sock` to `engine.sock.stale` because the file cannot be
accessed. The per-user executable was located from the installed Docker CLI and
launched once. No project configuration fault was demonstrated: Compose config
validation passes. See `docker-startup-cause.json`; no factory reset, volume
deletion, socket manipulation or unrelated-container change was performed.

### D. Code Corrections

The verification command changed from `python -I -c ...` to
`python -I -S -c ...`, with the target directory inserted explicitly into
`sys.path`. The fresh interpreter imports `AnalysisService` and `analyze_call`,
then checks that Gradio, SQLAlchemy, faster-whisper and project configuration were
not loaded. This proves lightweight installed entrypoint imports, not inference
without dependencies. The corrected command and both outcomes are preserved in
`wheel-before-no-site.json` and `wheel-after-no-site.json`.

No production implementation, test, dependency, exception policy or security
control changed during this review. Existing compatibility tests already cover
three consumers, two report statuses, JSON/PDF export, missing input, failed or
missing report, unsupported legacy result and guarded imports. Additional tests
duplicating those cases were unnecessary. Temporary verification drivers remain
under ignored `.local/`; exact executed subprocess arguments and outputs are in
the evidence files.

### E. Import and Dependency Analysis

No application import or dependency was added, removed or updated. Verification
uses existing Python stdlib `subprocess`, `pathlib`, `json`, `hashlib`, `time`,
`datetime`, `shutil`, `os` and `concurrent.futures`: execute isolated commands,
record results/timing, preserve reports, verify hashes and run independent checks.
The two mypy commands were serialized because they share cache state. No model,
dataset or package download was required. The current uv dependency check passes
for the existing 127 installed distributions.

### F. File-by-File Changes

| Path | Action and purpose |
|---|---|
| `docs/implementation/STEP_07_define_modular_target_structure_and_compatibility_layer_REPORT.md` | Append this A–O diagnosis, results, limitations and current handoff; retain original report |
| `docs/implementation/PROGRESS.md` | Record current review and distinguish STEP_08 eligibility from Docker execution readiness |
| `docs/implementation/evidence/step07-revalidation-20261025T073355Z/` | Create per-command JSON, prior-report snapshot, integrity checks, root-cause record and final summary/seal |
| `.local/step07_revalidate.py`, `.local/step07_finish_checks.py`, `.local/step07_docker_recheck.py`, `.local/step07_native_recheck.py`, `.local/step07_finalize_review.py` | Ignored local diagnostic and evidence-finalization drivers; no application functionality |
| `.local/step07-revalidation-path.txt`, `.local/step07-revalidation-native.db` | Ignored evidence pointer and isolated synthetic startup database |

No source deletion, rename, staging, commit, push or timestamp adjustment.

### G. Original vs Improved Repository

Upstream's pipeline defines the original result record and Gradio calls its
orchestration directly. STEP_07 preserves that orchestration while moving the
result contract and adding an optional typed report, injectable service and
internal API consumer. Explicit packaging now includes canonical src/services
namespaces; the original wheel layout omitted src. Existing weighted QA,
summary/state schemas and export paths remain protected by regression tests.
No new copy of those business algorithms was introduced.

Git history and the actual tracked diff were inspected; untracked implementation
files were inspected directly rather than omitted from review. The pre-review
17-file inventory matches exactly, including code, tests, configuration and
architecture documents. This review changes verification evidence/documentation
only. Earlier-step modifications in the mixed working tree were preserved.

### H. Architecture Impact

Call flow remains Gradio or internal API adapter → injected AnalysisService →
legacy process_call → original graph/persistence/exports. Lazy implementation
imports and type-only annotations keep transport inspection independent of
runtime startup. The API adapter is not a public HTTP endpoint or FastAPI route;
authentication, resource ownership and safe uploads remain future requirements.
The verification correction changes no runtime interaction or report contract.

### I. Tests and Validation

All commands below were executed using the existing uv-managed Python3.12.15
environment. JSON files preserve exact arguments, stdout/stderr, exit status and
wall time. Pytest's own measured duration differs from total subprocess wall time.

| Fresh check | Result | Evidence |
|---|---|---|
| `python -m pytest tests/ -q --tb=short` | **165 passed, 0 failed/skipped, 25.79s**; wall29.840s | `pytest.json` |
| Ruff check src/services/tests/scripts/app | Exit0, wall0.323s | `ruff.json` |
| Ruff format --check same scopes | Exit0, 76 files formatted, wall0.322s | `format.json` |
| Targeted four-file mypy --follow-imports=skip | Exit0, wall0.946s; excludes imported bodies | `targeted-mypy.json` |
| Full mypy src/ | **FAIL**, exit2, six initial errors, wall3.018s | `full-mypy.json` |
| uv pip check | Exit0, wall3.279s,127 packages | `dependencies.json` |
| Existing source key guard and explicit detect-secrets on step code/tests | Both exit0 | `secrets.json`, `detect-secrets-new-code.json` |
| compileall app.py src/ services/ | Exit0, wall0.309s | `compile.json` |
| Compose config --quiet | Exit0, wall0.547s | `compose-config.json` |
| Current Docker health / original app import | **FAIL**, exit1, engine unavailable | `compose-health.json`, `app-import.json` |
| Old wheel, isolated without site | Expected exit1, missing src | `wheel-before-no-site.json` |
| Fixed wheel, isolated without site | Exit0, imports without runtime setup | `wheel-after-no-site.json` |
| Native original app import/build, offline cached tiny, isolated SQLite | Exit0; model and workflow/demo build | `native-app-import.json` |
| Prior artifact seal / implementation hashes |18/18 and17/17 match before report changes | `prior-evidence-integrity.json`, `implementation-integrity.json` |
| Git diff --check | Exit0 | `git-diff.json` |

Pytest emits an existing pytest-asyncio warning about an unset default fixture
loop scope; it is not a failed test. No check was disabled to get green output.
Fresh hosted-provider analysis, container end-to-end inference, remote CI,
PostgreSQL migration, worker tests and frontend build were **NOT EXECUTED** in
this review. Docker prevents the container checks; the other implementations are
outside STEP_07. The sealed October24 successful live callback remains historical
evidence, clearly separated from today's native startup and synthetic regressions.

Acceptance traceability: actual import mapping/boundaries and AppShell contracts
are documented; shared service/API consumer exist and compatibility cases pass;
new entrypoints are side-effect-free; the existing app freshly imports natively.
All STEP_07 gates pass. This does not certify current Docker availability.

### J. Performance and ML Metrics

No training, model promotion or accuracy benchmark ran. WER, DER, F1, accuracy,
GPU peak memory, service-wrapper overhead, p95 and throughput are **Not measured**.
Today's full-suite duration is25.79s; comparison with the earlier22.10s is not a
controlled performance experiment. No speedup or regression claim follows.
Native startup used the existing tiny checkpoint on CPU/int8, with offline flags.
The older one-call7.8365s/31segments/QA2.65 result remains a cache-hit smoke result,
not a repeated current measurement or evidence of model-quality improvement.

### K. Security Analysis

Existing security tests pass as part of the full suite. Both source key guard and
step-code detect-secrets checks pass. Hash validation confirms no implementation
or security configuration changed before documentation updates. Evidence excludes
credential values, transcripts and report contents. The native smoke uses an
isolated ignored SQLite path and makes no analysis request or training invocation.
Docker state/volumes and unrelated Ollama configuration were not altered.

This is bounded regression verification, not a penetration test or production
security certification. Legacy raw cache/PII masking, audit mutability and lack of
public transport authorization remain disclosed in section7 and the transition
document. Future routes must enforce ownership and sanitize errors. No bypass or
new public exposure was introduced to unblock tests.

### L. Concepts Explained

An editable installation points Python back to working source; useful in
development, it can hide a broken distribution. Isolation must remove that path
when testing the wheel itself. `-I` and `-S` address different influences: isolated
mode controls environment/search-path behavior; no-site mode skips installed
site hooks. A hash compares exact bytes, so it establishes artifact continuity,
not code correctness. A native smoke proves local app construction; Docker health
proves a separate deployment boundary. One cannot substitute for the other.

### M. Questions and Answers

1. **Which step actually needs diagnosis?** STEP_07 is the latest implemented step. The older preflight FAIL concerned missing STEP_06 prerequisites; subsequent implementation/evidence supersedes that state without deleting it.
2. **Why did the old wheel unexpectedly pass?** Python still initialized site packages under -I. The refreshed editable install supplied source imports missing from the wheel, contaminating the test environment.
3. **How was that cause demonstrated?** The same old target fails under -I -S while the fixed target passes. Source was not reverted and installed dependencies were not removed.
4. **Why choose -S instead of uninstalling the project?** It gives a fresh wheel-only import environment using stdlib and the selected target, preserving the user's editable installation and runtime environment.
5. **Did this require an application fix?** No. The prior explicit setuptools discovery correction remains valid; only the revalidation method needed correction. Production hashes matched the sealed inventory.
6. **Why does whole-project mypy remain red?** It encounters dependency typing gaps and a Python-target/NumPy-stub syntax mismatch before full analysis. The six initial messages are not an exhaustive inventory of application type errors.
7. **Does targeted mypy replace the full check?** No. It checks four new files while skipping imported implementation bodies. Both outcomes are reported so a limited pass cannot hide the full failure.
8. **Why did Docker recovery stop?** Desktop's own log shows inaccessible secrets-engine socket state. Resetting or deleting Docker-managed state risks unrelated services/data and is unnecessary to establish the STEP_07 native import gate.
9. **How was compatibility checked without a fresh hosted call?** Deterministic consumer/status cases, real SQLite/JSON/PDF operations and all existing regressions passed. Earlier sealed live evidence remains available, but is not relabeled as a current run.
10. **Are auth, migrations and workers broken?** They are not implemented by this architecture step. The internal adapter is not an exposed server. Treating future work as an implemented-but-failing feature would misstate scope.
11. **How was performance affected?** No production code changed and wrapper overhead was not measured. Test duration is recorded for reproducibility, not interpreted as inference performance.
12. **How can future packaging checks avoid this defect?** Run canonical entrypoint imports from a wheel-only target with site initialization disabled, or a clean disposable interpreter; ensure the installed module origin belongs to that target.

### N. Remaining Problems

RV07-02: inherited whole-project typing failure remains unresolved. RV07-03:
Docker Desktop cannot initialize its secrets-engine socket, so live app/Postgres
container readiness is currently unavailable. Restore Desktop without resetting
project volumes, then run `docker compose --env-file .env.docker -f
compose.local.yml up -d --no-build --pull never postgres app` and verify health
before STEP_08. If Desktop still fails, investigate the named socket/startup error
with its host logs; no destructive recovery is implied by this handoff.

The historical recovered provider error, incomplete privacy/auth safeguards and
original Gradio styling remain previously disclosed limitations. No UI source
changed here. Existing screenshots and the approved-reference comparison in
section13 remain applicable; no fresh responsive/contrast acceptance is claimed.

### O. Final Quality Verdict

**PASS WITH LIMITATIONS.** Three current verification/environment failure groups
identified; one corrected and validated, two unresolved as explicitly described.
Zero newly confirmed production defects; no blocking STEP_07 acceptance failure.
All165 tests pass, native app import succeeds and installed service entrypoints
pass their isolated check. Full mypy and current Docker checks are not passed.
STEP_08 remains the next eligible implementation step, with Docker recovery
required before its database work. Stop here; do not advance during this review.

# Follow-up Error Corrections — 2026-10-25

### A. Executive Summary

The user explicitly requested correction of the remaining errors. **Both previously
unresolved groups are fixed:** full strict application typing now passes, and Docker
Desktop starts with healthy app/PostgreSQL containers. This replaces the unresolved
state in the preceding historical appendix without deleting its evidence.

Full current suite: **175 passed in21.23s**, zero failed/skipped. Strict mypy checks
**39 files** without ignored errors or skipped application bodies. A fresh analysis
through the rebuilt Docker app completes and exports valid JSON/PDF. No STEP_08
implementation, schema migration, commit or push occurred.

Evidence: [error-fix commands and artifacts](evidence/step07-error-fixes-20261025T073924Z/).
The original failure logs, earlier reports and sealed evidence remain unchanged.

### B. Failure Inventory

| ID | Failure | Component | Severity | Reproduction | Root cause | Status |
|---|---|---|---|---|---|---|
| FIX07-01 / RV07-02 | Full strict mypy aborts, then exposes77 application errors | Development toolchain and application annotations | P2 | Prior six-error abort; expanded77-error log retained | Old parser/stubs and incomplete signatures, ORM descriptor types, optional results and dynamic-provider boundaries | Fixed: strict39-file check exit0; no error suppression |
| FIX07-02 / RV07-03 | Docker Desktop cannot initialize Secrets Engine | Local environment | P2 | Prior engine.sock error; zero-byte ReparsePoint confirmed; Linux API unavailable | Stranded inaccessible runtime socket | Fixed: preserve parent runtime directory and restart; engine29.9.2, app/Postgres healthy |
| FIX07-03 | Valid JSON array/string/number breaks history listing | History service | P2 | AST-extracted prior `_safe_loads('[]')` returns list; `.get` raises AttributeError | JSON validity was mistaken for dictionary shape | Fixed: non-object JSON falls back to empty display data; three real SQLite regressions |
| FIX07-04 | Structured provider dictionary fails despite valid schema data | Summary/QA boundary | P2 | Prior summary function with synthetic valid dict raises missing call_id attribute | Library return type is model-or-dict; caller assumed concrete model | Fixed: validate through requested Pydantic model before use; valid/invalid cases for both agents |

Two prior error groups corrected, plus two related behavior gaps exposed by the
typing review: **four identified, four corrected, zero unresolved in this inventory**.
The earlier wheel-isolation correction remains valid and is not counted again.

### C. Root-Cause Analysis

Mypy1.15 could not parse the installed NumPy stub syntax while targeting Python3.11.
Mypy2.4 parses the dependency stubs with the same Python3.11 target; it then reports
77 errors in19 files, rather than stopping at the initial six. The errors include
bare dict/list/sessionmaker parameters, unannotated callbacks and resources, ORM
Column descriptors interpreted as row values, None flowing into required state,
untyped faster-whisper/soundfile interfaces and model-or-dict provider results.

Docker host logs identified a failed rename of the zero-byte engine.sock, whose
attributes were Archive/ReparsePoint. The installed per-user Desktop executable
was stopped with `docker desktop stop --force --timeout20`; process absence and
directory contents were checked. Source/destination absolute paths were verified
under LOCALAPPDATA. The containing directory, with only that runtime socket, was
preserved as `docker-secrets-engine.preserved-20261025T073932Z`, then Desktop was
restarted. The engine came up without resetting settings, deleting volumes or
modifying Ollama configuration. This matches the reported Windows socket failure
in [Docker's issue tracker](https://github.com/docker/for-win/issues/15064);
successful recovery here is established by local execution, not the issue report.

### D. Code Corrections

`Mapped[T]`/`mapped_column` describe SQLAlchemy row values and retain the same
columns/types/nullability/defaults/indexes. The independently captured pinned
upstream SQLite CREATE TABLE/INDEX fixture matches all three current tables.
Session factories are `sessionmaker[Session]`; database parameters and the SQLite
connect callback now use concrete Engine/Connection/ConnectionPoolEntry types.
Missing database resources raise explicit ValueError before initialization.

Workflow/Audit protocols moved into lightweight contracts, breaking no public
imports from analysis.py because they remain imported there. Pipeline and UI
consumers share these ports. LangGraph's heterogeneous state remains explicitly
dynamic at its port; Engine, report/result types and application function bodies
are checked. The request itself retains its trusted-path contract, and the legacy
pipeline retains its numpy microphone-tuple compatibility.

Summary/QA now execute `RequestedModel.model_validate(structured_llm.invoke(...))`
before assigning UUID or computing weighted score. Existing model instances are
retained; dictionaries are validated; malformed output follows the existing
bounded retry/failure path. QA weights and prompts were not changed by this fix.

History decodes JSON and returns it only when it is a dict. Intake uses explicit
fallback errors and rejects an absent detected format. Graph success now requires
both concrete results; error state always carries a string. PII redaction uses
separate names for regex Match and tuple candidates, with identical matching logic.
Typed ASR segments preserve the existing heuristic assignment/confidence formula.
Optional torch still imports only when device selection runs, via importlib.

Gradio callbacks and resource signatures are annotated; history correctly returns
State rather than the previously declared Markdown. The Blocks context manager's
untyped self-return is narrowed with cast. No controls, layouts, CSS, routes or
callback output order changed. The live six-output request proves the wiring.

### E. Import and Dependency Analysis

Development dependencies: mypy1.15.0 → **2.4.0**, and
**types-reportlab4.4.10.20260508** added for consumed ReportLab4.4 APIs. The uv-managed
Windows environment now has131 distributions, four more than before; the refreshed
freeze records new checker dependencies ast-serialize, librt and pathspec plus the
ReportLab stub package. All23 direct/dev pins match. Existing runtime model,
provider, database and audio versions remain unchanged.

New imports, grouped by purpose: sqlalchemy.orm Mapped/mapped_column supply typed
declarations; sqlalchemy.engine Engine and sqlalchemy.pool ConnectionPoolEntry
describe existing resources; sqlite3.Connection describes the existing DBAPI
callback. collections.abc Mapping/Callable and typing Any/TypedDict/cast express
heterogeneous external dictionaries, parser callables, ASR records and the known
Gradio context return. TYPE_CHECKING/numpy.typing NDArray annotate legacy audio
without adding a new eager array import. importlib loads optional torch dynamically.
CompiledStateGraph names the existing compiled graph. ReportLab Flowable describes
the PDF story elements. Local WorkflowPort/AuditPort imports replace untyped resource
parameters. None of these adds a network service or training runtime.

Local `.pyi` files describe the consumed faster-whisper1.2.1 and soundfile0.13.1 APIs;
they are not runtime replacements. Segment fields are concrete; transcription
options and array payloads remain explicitly dynamic. This bounded scope is
documented in `stubs/README.md`, following [mypy's stub mechanism](https://mypy.readthedocs.io/en/stable/stubs.html).
Strict mode, Python3.11 target and missing-import errors remain enabled. No
ignore_missing_imports, disabled error code or blanket application Any replacement.

### F. File-by-File Changes

| Files | Purpose |
|---|---|
| `pyproject.toml`, `PROJECT28_REQUIREMENTS.lock.txt` | Pin checker/stubs, configure local stub path, refresh portable editable freeze |
| `.github/workflows/ci.yml` | Add full strict mypy; include stubs in Ruff lint/format |
| `stubs/faster_whisper/__init__.pyi`, `stubs/soundfile.pyi`, `stubs/README.md` | Consumed external interfaces and coverage limitations |
| `src/database/models.py`, `src/database/connection.py` | Schema-preserving typed ORM and sessions/callbacks |
| `src/security/audit.py`, `src/security/pii_redactor.py` | Typed resources/details, missing-resource guard and distinct match variables |
| `src/services/contracts.py`, `src/services/analysis.py`, `src/services/pipeline.py` | Shared ports and concrete boundary signatures; preserve single orchestration |
| `src/services/history.py`, `src/services/observability.py` | Typed engines and object-shaped history JSON |
| `src/agents/intake.py`, `src/agents/transcription.py` | Required-value guards, optional torch load, typed ASR/cache interfaces |
| `src/agents/summarization.py`, `src/agents/qa_scoring.py` | Pydantic structured-result validation |
| `src/agents/report.py`, `src/graph/workflow.py` | Typed resources/PDF elements/compiled graph and definite success/error values |
| `src/ui/app_builder.py`, three files under `src/ui/tabs/` | Resource/callback/return annotations; preserve rendering |
| `src/utils/audio.py`, `src/utils/formatters.py` | Typed heterogeneous parser and JSON display boundaries |
| `tests/unit/test_typing_corrections.py`, `tests/fixtures/sqlite-schema-upstream.json` | Ten regression cases and independently derived schema fixture |
| This report, `docs/implementation/PROGRESS.md`, `docs/architecture/transition.md`, evidence directory | Accurate correction/handoff, current port ownership and reproducible commands |

Exactly21 existing application files changed relative to the pre-fix hash capture;
the evidence lists every path. Local diagnostic drivers/downloads stay ignored
under `.local/`. Docker's preserved runtime directory is outside the repository;
its exact source/destination is recorded in docker-runtime-recovery.json. Nothing
was deleted. Earlier-step changes in the mixed working tree were preserved.

### G. Original vs Improved Repository

Pinned upstream uses unannotated service/resource/callback boundaries and Column
declarations; current code describes the same database schema and call flow with
checked types. Original provider consumers assume model attributes; current code
validates either supported structured-return shape. Original history assumes any
valid JSON is a dict; current code handles scalar/array stored values safely.
The schema snapshot comes from the pinned upstream Git object, not current model
metadata. Existing Gradio, weighted QA, heuristic diarization, cache and exports
remain. Unimplemented future neural/transport features are not claimed.

### H. Architecture Impact

One shared process_call still owns orchestration. Common protocols now live in
contracts so both legacy and injected consumers can use them without a cycle.
Static map still reports zero cyclic components. This is typing/reliability repair,
not a new service or migration. PostgreSQL connectivity is verified; the app still
uses its existing SQLite volume. No Alembic migration or database conversion ran.

### I. Tests and Validation

Exact command arrays, stdout/stderr, exit status and wall times are in evidence.

| Command / check | Fresh outcome |
|---|---|
| `python -m pytest tests/ -q --tb=short` | **175 passed in21.23s**, no failures/skips; wall23.258s |
| New repair regressions |10 passed in0.61s: four provider cases, three malformed JSON shapes, two missing resources, one schema check |
| `python -m mypy src/ services/ app.py` | Exit0, **39 source files**, wall1.621s |
| Ruff check and format --check across source/services/tests/scripts/stubs/app | Both exit0 |
| uv pip check / setup diagnostic | Exit0;131 packages compatible;23 direct/dev pins match |
| compileall / four pre-commit hooks / explicit new-code secret scan | All exit0 |
| Docker engine / Compose health | Exit0; engine29.9.2, both project containers healthy |
| Rebuilt Docker app import, isolated temporary SQLite | Exit0; cached tiny CPU/int8 model and demo build |
| Authenticated PostgreSQL TCP `select1` using mounted secret | Exit0; returns1; password not printed |
| Fresh real Gradio callback and JSON/PDF checks | Completed, six outputs,31segments, QA2.7 independently recomputed |
| SQL schema compatibility | Three tables and indexes match pinned upstream fixture |
| Whitespace / Git/source review | Exit0; original history preserved |

Development corrections: two import-order lint findings were formatted. The first
new QA test incorrectly expected4.3, but the actual fixture gives every dimension4
and therefore independently yields4.0; the test expectation/comment was corrected,
without changing production weights or fixtures. All175 cases then pass. A local
provenance driver needed its checkout path and SummaryResult namespace supplied;
that driver is separate from application code. Old behavior reproductions are
recorded without reverting the working tree. An existing pytest-asyncio default-loop
deprecation warning remains advisory, not a failed test. Remote CI and Python3.11
runtime execution were not run; local strict checking targets3.11 on Python3.12.15.

### J. Performance and ML Metrics

Fresh one-call wall time **4.2369s** includes upload, existing cached transcription,
hosted summary/QA and downloads. The bundled sample SHA is unchanged. Output:
31segments, QA2.7, JSON13,082bytes, PDF2,981bytes. Both artifacts validate; transcript
and customer content are not published. This stochastic, cache-path smoke is not
a quality benchmark or proof of speedup over prior calls. No training, model
promotion, WER/DER/F1, p95, throughput or peak-VRAM measurement occurred.

### K. Security Analysis

Existing security tests, source-key guard and detect-secrets checks pass. Desktop
recovery preserves its runtime artifact and existing volumes; no factory reset,
WSL unregister, model pull or Ollama setting change. The project app retains
loopback ports/read-only-root/no-new-privileges configuration. PostgreSQL credentials
come from the ignored mounted secret and are not included in command output.
Pydantic validates untrusted provider shapes before use, and malformed stored JSON
cannot crash history listing. This does not establish public auth/tenant isolation,
complete PII masking or cache privacy; existing limitations remain.

### L. Concepts Explained

A type checker follows possible values before execution; describing an optional
value does not make None safe, so success paths must establish real results.
Mapped[str] means a row instance exposes a string while its class attribute still
supports SQL expressions. A stub describes an external interface without changing
the implementation. Pydantic validation turns a structured dictionary into a
validated application model. A stranded socket is runtime coordination state, not
the PostgreSQL database; preserving its parent directory allowed regeneration
without deleting database/model volumes.

### M. Questions and Answers

1. **Were the two remaining errors actually fixed?** Yes. Full strict mypy returns0 and Docker now exposes a working Linux API with healthy project containers. The corrected app was rebuilt and exercised.
2. **Was strictness reduced?** No. Python3.11 targeting and strict checks remain; the full command includes app.py and both package trees, and is now a CI step. Explicit dynamic JSON/provider options are documented boundary types.
3. **Why update mypy?** The old parser aborts on installed dependency syntax. The newer pinned checker parses it while retaining the supported target and reveals real application errors for correction.
4. **Why not install PyTorch to satisfy mypy?** Device probing treats it as optional. Dynamic import preserves that contract and CPU fallback without installing a large unused runtime merely for annotations.
5. **Did ORM annotations migrate the database?** No. Independent upstream CREATE TABLE/INDEX definitions match all three models; existing persistence tests and real stored-data startup pass.
6. **Why move protocols into contracts?** Both pipeline and service need them. A common lightweight owner avoids a reciprocal implementation dependency while preserving imports through analysis.py.
7. **What changed for provider dictionaries?** They are now converted and validated against SummaryResult/QAScoreResult before attribute use. Invalid shapes remain bounded failures instead of masquerading as successful typed results.
8. **How were new behavior gaps proved?** Prior functions extracted from Git reproduce the list.get and dict.call_id failures against synthetic data. Current end-to-end service regressions cover the corrected shapes.
9. **Why preserve Docker's socket parent?** Individual socket access failed, and the verified directory contained only a zero-byte runtime entry. A timestamped rename retains evidence while Desktop recreates usable runtime state.
10. **Did Docker recovery delete recordings or models?** No. No volume deletion, factory reset, WSL unregister or model download command ran. Existing app/Postgres volumes were reused.
11. **Is the live QA score a model improvement?** No. It is one generated output whose weighting was independently checked. No labeled quality evaluation or training was performed.
12. **What is now ready next?** STEP_08 can begin with working Docker/Postgres and passing application checks. Its migration, recovery tests and report still need implementation under a separate step invocation.

### N. Remaining Problems

No unresolved failure remains in this correction inventory. External-library stubs
cover consumed APIs only. Hosted models remain nondeterministic; complete privacy,
auth, durable-job and approved frontend acceptance remain future work. Docker's
preserved socket artifact should remain until recovery is accepted; recurrence
after an unclean shutdown is possible. The pytest-asyncio warning is advisory.
No UI styles changed; original Gradio design deviations in section13 remain.

### O. Final Quality Verdict

**PASS — the requested errors are corrected and validated.** The implementation
step remains **PASS WITH LIMITATIONS** for the already disclosed product/privacy/UI
scope, rather than claiming production readiness. Full typing and Docker are no
longer blockers. STEP_08 is next eligible; no advancement performed in this task.

## STEP_08 follow-on storage handoff — 2026-10-25

STEP_08 subsequently implemented PostgreSQL/Alembic while retaining this shared
analysis service and SQLite compatibility. The local Compose app now uses the
restricted PostgreSQL role;193 tests pass, including real database integration.
The original STEP_07 measurements/status above remain historical evidence.
See the [STEP_08 report](STEP_08_migrate_sqlite_persistence_to_postgresql_with_alembic_REPORT.md)
and [schema/recovery guide](../database/schema.md) for current persistence and
STEP_09 readiness. No STEP_09 implementation is implied by that handoff.
