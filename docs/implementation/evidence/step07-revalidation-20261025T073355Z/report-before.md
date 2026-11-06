# STEP_07 — Modular target structure and compatibility layer

> **DONE — PASS WITH LIMITATIONS.** Date: 2026-10-24, Africa/Casablanca.
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
