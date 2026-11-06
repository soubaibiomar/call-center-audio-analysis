# STEP_09 — Typed FastAPI endpoints and authentication boundaries

## 1. Execution header

- **Status:** DONE — **PASS WITH LIMITATIONS**.
- **Owner:** Platform / Codex implementation. Date: 2026-10-25, Africa/Casablanca.
- **Branch:** `feature/project28-foundation`.
- **Working HEAD:** `a37e4634af1d2947fc3c548d54e62bda0b0daf89`.
- **Verified upstream HEAD:** `fed4b610742c1337147281fcec8f2cdcc0a79be5`, clean clone at
  `C:/Users/omar/Projects/Project28-Upstream-Baseline-Step02`.
- **Environment:** Windows 11 / PowerShell; uv-managed Python 3.12.15;
  Docker Desktop PostgreSQL 17.11; RTX 4060 8 GB available, native analysis selected
  CPU/int8. No training or GPU benchmark ran.
- **Scope:** STEP_09 only. STEP_01–08 prerequisite reports and actual service,
  database, graph, tests and design specifications were inspected. STEP_08's
  latest correction gate passed. STEP_10 has not been implemented or advanced.
- **Evidence:** [step09-20261025T083345Z](evidence/step09-20261025T083345Z/).
  Earlier blocked STEP_09 report is preserved there as `previous-preflight-report.md`.
- No commit, push, timestamp adjustment, public deployment or history rewrite.

## 2. What was built and why

The original call analysis can now be called through a typed, versioned HTTP API.
An authenticated upload invokes the existing AnalysisService and LangGraph path;
existing reports, transcripts, QA scores and PDFs can be retrieved with explicit
tenant and owner authorization. Dashboard and paginated call contracts support the
future approved ERP interface without introducing a new frontend.

The factory does not load a model at import or startup. Health and schema remain
available without a provider key, identity provider or database. Protected access
requires a valid signed identity plus an enabled mapped PostgreSQL user. Agents
see their calls; supervisors/admins see their tenant. Cross-owner/tenant/missing
resources return the same 404. Token role claims cannot escalate privileges.

The user confirmed **they do not have an OIDC provider**. Default external access
therefore stays fail-closed. Implementation was exercised using ephemeral RSA
signatures and real PostgreSQL RLS/runtime credentials, including a real loopback
HTTP sample analysis. This validates the code boundary, not a real provider's
login, discovery, tenant-claim issuance, key rotation or organization membership.
No issuer, account, provider or production token was invented.

The primary database was backed up privately before the additive identity
migration. Its four existing reports and all associated rows were preserved.
The Gradio Docker app was rebuilt and restarted with final source and remained
healthy. Its trusted-local access model is unchanged.

## 3. Original implementation versus this working tree

| Area | Actual pinned upstream | Upgraded implementation and exact symbols | Compatibility / rationale |
|---|---|---|---|
| Integration entry | `app.py` launches Gradio; no project-owned `/api/v1` factory | `services/api/app.py:create_app`, versioned APIRouter | Additive interface; no replacement of Gradio |
| Shared orchestration | `src/services/pipeline.py:process_call` performs graph, persistence, exports | STEP_07 AnalysisService reused by HTTP `analyze_call`; optional `AnalysisRequest.downloads` | Existing callers default to downloads enabled |
| Identity | No external JWT-to-user boundary | `auth.py:Authenticator.authenticate`, `provision_identity.py:link_identity` | Externally verifiable RS256 identity; database owns access/roles |
| Tenant context | SQLite, no request identity | STEP_08 PostgreSQL RLS plus `src/database/scope.py:database_identity` | Gradio retains legacy default; API overrides only current request |
| Report storage | Legacy CallRecord and best-effort persistence | `persist_report` passes verified tenant/owner to normalized `store_report`; API treats failure as failure | Legacy behavior preserved outside identity context |
| Read scope | Gradio local history reads | `call_query`, `read_report`, dashboard/job filters | Same-tenant owned resources or authorized supervisor/admin scope |
| Output | CallReport includes intake audio path / trace | `schemas.py:Report.from_report` strips these; original typed transcription/summary/QA retained | Public DTO deliberately smaller; legacy JSON export remains original |
| PDF text | Dynamic text parsed as ReportLab markup | `src/agents/report.py:generate_report_pdf` escapes generated free text | Prevents untrusted image/markup interpretation; regression tested |
| Work execution | Synchronous analysis | Same, 201 on success, 429 while process busy; stored job read-only endpoint | No fictional broker, progress, 202 or worker implementation |
| API documentation | No versioned application schema | `docs/api/openapi.json`, `scripts/export_api_schema.py` | Deterministic generation, snapshot tested |
| Frontend | Gradio baseline | No React/CSS changes; typed empty/error/progress contracts | ERP visual build remains a later step |

`git diff --stat` at capture: **39 tracked files changed, 502 insertions and 238
deletions** across the accumulated STEP_01–09 working tree. This is **not** a
standalone STEP_09 diff: earlier uncommitted work is preserved. New untracked
files are absent from ordinary `git diff`; `git-status.txt` records them explicitly.
See evidence `git-stat.txt`, `git-name-status.txt`, `git-status.txt` and the final
source manifest. The matrix above distinguishes inherited work from this step.

## 4. Files and interfaces

| File | This step | Purpose / inputs / outputs |
|---|---|---|
| `services/api/app.py` | Created | Factory, ASGI boundary, routes, lazy analysis, bounded uploads, safe HTTP errors |
| `services/api/auth.py` | Created | Bearer token → verified enabled Principal; signed tenant and mapped database user |
| `services/api/settings.py` | Created | Explicit environment → immutable validated configuration; no test defaults |
| `services/api/schemas.py` | Created | Typed health/identity/call/page/dashboard/report/job/error responses |
| `services/api/provision_identity.py` | Created | Operator CLI and idempotent mapping function; refuses reassignment |
| `src/database/scope.py` | Created | ContextVar identity and exception-safe context manager |
| `services/api/db/models.py` | Modified STEP_08 file | ExternalIdentity tenant/user foreign keys and issuer/subject uniqueness |
| `services/api/db/settings.py` | Modified STEP_08 file | Current schema marker `0002_identity` |
| `services/api/db/admin.py` | Modified STEP_08 file | Runtime identity mapping access SELECT-only |
| `migrations/versions/0002_external_identities.py` | Created | Add mapping table, indexes, ENABLE/FORCE RLS, scoped policy, read grant; refuse populated downgrade |
| `src/database/connection.py` | Modified | Begin hook uses request identity, otherwise existing legacy tenant |
| `src/agents/report.py` | Modified | Persist with current identity; escape PDF free text |
| `src/services/contracts.py` | Modified STEP_07 file | Backward-compatible optional `downloads=True` request field |
| `src/services/analysis.py` | Modified STEP_07 file | Pass download override only when disabled |
| `src/services/pipeline.py` | Modified | API skips unused export temp files; failure on scoped persistence errors; remove owned successful intake copy |
| `requirements.txt`, `pyproject.toml` | Modified | Direct API/runtime pins; httpx test pin |
| `PROJECT28_REQUIREMENTS.lock.txt` | Refreshed | Actual uv freeze with portable editable `-e .` |
| `.env.project28.example` | Modified | Commented OIDC configuration; no credentials |
| `.github/workflows/ci.yml` | Modified | Disposable PostgreSQL service and API/DB tests; hosted CI not run |
| `scripts/prepare_ci_database.py` | Created | CI-only disposable migrations/role bootstrap and ignored URL files |
| `scripts/export_api_schema.py` | Created | Model/database/secret-free schema generation |
| `tests/api/test_api.py` | Created | 37 signature, RLS, ownership, input, service, failure, concurrency, PDF and schema cases |
| `docs/api/README.md`, `docs/api/openapi.json` | Created | Run/configure/provision/error/contract documentation and generated schema |
| `docs/architecture/api-boundary.md` | Created | Identity, resource scope, synchronous execution and worker handoff decision |
| This report, `docs/implementation/PROGRESS.md`, evidence directory | Updated/created | Actual results, limitations, tracker and durable execution evidence |

No source files were deleted. `services/api/analysis.py` remains the original
STEP_07 adapter and is now called from the HTTP route. Existing `CallReport`,
`TranscriptionResult`, `SummaryResult` and `QAScoreResult` are reused rather than
forking the analysis contracts. Migration 0001 is unchanged.

## 5. Important code and data flow

### Factory and transport boundary

`create_app(settings, engine, analysis_factory)` accepts explicit dependencies for
tests and normal environment-backed startup. An owned engine is disposed at
lifespan exit; an injected engine remains the caller's responsibility. The
factory rejects SQLite because authenticated multi-tenant operation depends on
the PostgreSQL boundary. Model compilation is lazy inside the first analysis.

`Boundary.__call__` ignores non-HTTP ASGI lifespans and creates a new request UUID
for HTTP. For `/api/v1` it verifies authentication **before** multipart parsing.
It rejects invalid/oversized Content-Length and wraps `receive` to count actual
body bytes, including chunked requests. The body cap is audio limit plus 64 KiB
framing allowance. `checked_send` adds no-store/request-ID headers. Exceptions
before response start produce sanitized envelopes; an already-started response
cannot safely be replaced. FastAPI exception handlers normalize validation,
HTTP, database and unexpected exceptions without echoing bodies or exception text.

`principal` exposes HTTPBearer security in OpenAPI and returns the already verified
request principal. It does not bypass middleware or trust arbitrary request input.
The dependency is shared by all versioned routes.

### Signature verification and authorization

```python
claims = jwt.decode(token, key, algorithms=["RS256"],
                    audience=settings.audience, issuer=settings.issuer,
                    options={"require": ["iss", "aud", "sub", "exp", "iat", tenant_claim]})
```

The fixed algorithm prevents algorithm substitution. The key is an operator-pinned
PEM or key from the configured JWKS URL, never a token-supplied URL. Require means
claims must exist; PyJWT also checks their signed values, expiration, issue time
and optional not-before. The code then validates UUID tenant, bounded nonempty
subject, numeric timestamps and a positive lifetime of at most one hour. Malformed
or invalid signatures/claims return 401; provider key-network failure returns 503.

`Authenticator.authenticate` next opens a transaction scoped to the verified
tenant, joins ExternalIdentity to User by both user ID and tenant, and requires
enabled agent/supervisor/admin. Unknown, disabled or legacy service identities are
403. `Principal.owner_filter` returns the agent's user ID; supervisory roles use
tenant scope. Roles claimed inside the JWT are ignored.

`call_query` always filters tenant and, for an agent, owner. Call detail, report,
transcript, QA, PDF, list, dashboard and job-associated calls share it. The database
also applies tenant RLS. Foreign resources and nonexistent IDs share the same 404
to avoid exposing resource existence. Jobs with no authorized associated call are
not visible. Pagination bounds limit response size; order is timestamp plus ID.

### Request-local persistence

```python
token = _identity.set(DatabaseIdentity(tenant_id, user_id))
try:
    yield
finally:
    _identity.reset(token)
```

`DatabaseIdentity` is immutable. ContextVar stores identity in the current execution
context, rather than mutating a shared engine tenant. The database begin listener
uses it for graph cache and audit transactions; report persistence also passes its
owner to `store_report`. Reset always runs after success or exception. The route
enters this scope **inside** the thread executing the shared synchronous service.
Without it, Gradio uses the existing legacy tenant/user.

### Upload, analysis and output

The upload endpoint reads at most configured audio limit plus one byte, validates
content with the existing audio detector and uses a private TemporaryDirectory
with generated UUID filename. Client filenames are not paths. Metadata has 255
character bounds. TemporaryDirectory and UploadFile close in all exit paths.

`invoke` acquires one process-local semaphore without waiting. Busy requests get
429 and Retry-After. It constructs AnalysisService once and calls the unchanged
`analyze_call` adapter with `downloads=False`. No duplicate pipeline is added.
The pipeline still invokes original intake/transcription/summary/QA/report nodes.
API report-persistence failure returns failure, rather than pretending it stored a
result. The semaphore releases in `finally` even if initialization or inference
fails. Other analysis failures become generic 502.

After a successful graph return, API mode removes only an intake file in the OS
temp directory with the exact `call_<report UUID>_` naming convention. It does not
delete arbitrary report paths. API mode skips original JSON/PDF temporary exports;
PDF is instead generated on authorized demand. Free text is XML-escaped before
ReportLab paragraph rendering, preventing image/markup interpretation. Failed
graphs can still leave upstream intake copies: this limitation is explicit.

`Report.from_report` validates a smaller DTO from original report data. Pydantic
ignores internal extra fields; intake path and trace ID are not public properties.
Dashboard counts use authorized rows and SQL aggregation; an empty average is
null. Job progress is null because no worker has measured progress. These are
truthful contracts for future frontend loading/empty/error states.

## 6. Imports and dependency justification

Runtime pins: FastAPI **0.162.0**, Pydantic **2.11.3**, Starlette **0.52.1**,
Uvicorn **0.54.0**, python-multipart **0.0.32**, PyJWT **2.15.1** with crypto,
cryptography **50.0.2**, SQLAlchemy **2.0.41**, Alembic **1.20.1**.
Test client: httpx **0.28.1**, pytest **8.3.5**. Python stdlib is 3.12.15 locally.
FastAPI/Uvicorn/multipart already existed transitively through Gradio and are now
direct pins because this project imports/runs them directly. PyJWT is new; its
crypto extra reuses installed cryptography. No training dependency was introduced.
`uv pip check` passes all 136 installed packages. Freeze is evidence of this
environment, not a universal cross-platform binary lock.

Every import introduced by the new modules or changed behavior is explained below;
symbols grouped in a row share a source module, not an assumed equivalence.

| Import source and symbols | Origin / meaning / reason and location |
|---|---|
| `collections.abc: AsyncIterator, Callable, Iterator` | stdlib: lifespan return type, injectable service factory, scoped context generator |
| `contextlib: asynccontextmanager, contextmanager` | stdlib: deterministic async app cleanup and synchronous identity reset |
| `contextvars: ContextVar` | stdlib: per-execution identity, avoids process-global tenant mutation |
| `dataclasses: dataclass, field` | stdlib: immutable settings/identity/principal; hide URLs/PEM in repr |
| `pathlib: Path` | stdlib: private config reads, bounded generated upload paths, artifact output |
| `tempfile: TemporaryDirectory` | stdlib: per-upload folder removed on all exits |
| `threading: BoundedSemaphore` | stdlib: single inference at a time per API process |
| `typing: Annotated, Any, cast, Literal` | stdlib: FastAPI dependency/field metadata, constrained dynamic role conversion, explicit enum-like responses |
| `uuid: UUID, uuid4` | stdlib: validate IDs; generate request/upload/test identifiers |
| `datetime: datetime` | stdlib: typed timestamps in HTTP schemas |
| `os` | stdlib: explicit environment configuration and isolated-test opt-in |
| `urllib.parse: urlsplit` | stdlib: require bounded HTTPS issuer/JWKS without embedded credentials |
| `argparse` | stdlib: operator identity-link command arguments |
| `json` | stdlib: deterministic OpenAPI/evidence serialization and schema snapshot comparison |
| `secrets` | stdlib: random disposable CI role credential; never logged |
| `xml.sax.saxutils: escape` | stdlib: turn untrusted PDF free text into literal text |
| `fastapi: FastAPI, APIRouter` | third party: app factory and versioned route registry |
| `fastapi: Depends, Query, File, Form` | third party: shared principal dependency and bounded request metadata |
| `fastapi: HTTPException, Request, UploadFile` | third party: transport errors, request state/headers, multipart spooled-file interface |
| `fastapi.exceptions: RequestValidationError` | third party: sanitized 422 handler without echoing sensitive input |
| `fastapi.responses: JSONResponse, Response` | third party: error envelopes and authenticated PDF bytes |
| `fastapi.security: HTTPBearer, HTTPAuthorizationCredentials` | third party: OpenAPI bearer scheme and typed credentials; real verification is middleware |
| `starlette.concurrency: run_in_threadpool` | third party ASGI framework: blocking signature/DB/analysis work off event loop |
| `starlette.exceptions: HTTPException as StarletteHTTPException` | third party: normalize router/parser HTTP failures too |
| `starlette.types: ASGIApp, Message, Receive, Scope, Send` | third party typing: application callable, message dictionary, request stream, connection context, response sender |
| `pydantic: BaseModel, ConfigDict, Field` | third party: runtime boundary validation, ORM attribute reads, numeric constraints |
| `jwt` | third party PyJWT: signed decode; test encode only for ephemeral fixtures |
| `jwt: PyJWKClient` | third party: fixed-endpoint signing-key retrieval/cache |
| `jwt.exceptions: PyJWKClientConnectionError, PyJWTError` | third party: distinguish retryable key-network failures from invalid credentials |
| `cryptography.hazmat.primitives: serialization` | third party: PEM public-key loading and fixture public-key serialization |
| `cryptography.hazmat.primitives.asymmetric.rsa: RSAPublicKey` | third party: assert RSA key type and minimum size; no private production key |
| `sqlalchemy: Select, select, func, text, create_engine` | third party: typed scoped SQL, aggregates, readiness/migration SQL, managed connection pools |
| `sqlalchemy.engine: Engine, make_url` | third party: injected connection pool and private disposable CI URL construction |
| `sqlalchemy.exc: SQLAlchemyError` | third party: safe retryable database error translation |
| `sqlalchemy as sa`, `alembic: op` | third party: migration table/column/constraint definitions and transactional DDL |
| `alembic: command`, `alembic.config: Config` | third party: CI reviewed migrations through an explicit owner connection |
| `services.api.analysis: analyze_call` | local: STEP_07 transport-neutral service adapter, original typed report |
| `services.api.auth: Authenticator, Principal` | local: verified identity lookup and immutable authorization scope |
| `services.api.settings: ApiSettings` | local: validated external auth/config boundary |
| `services.api.schemas: CallItem, CallPage, Dashboard, ErrorResponse, Health, Identity, JobStatus, Report` | local: the named HTTP DTOs for routes/error documentation |
| `services.api.db.models: ExternalIdentity, User, Call, Job` | local: operator-owned identity links, enabled users, authorized calls, existing persisted job state |
| `services.api.db.settings: database_url` | local: private URL/file loading reused without credential output |
| `services.api.db.admin: provision_runtime` | local CI helper: least-privilege runtime grants, not normal app startup |
| `src.database.connection: get_engine, init_db, session_scope` | local: tenant-aware pool, schema marker guard, transaction cleanup |
| `src.database.models: CallRecord` | local: original full report storage after scoped canonical-call lookup |
| `src.database.scope: current_identity, database_identity` | local: begin-hook/report ownership and exception-safe request scope |
| `src.graph.state: CallReport, QAScoreResult, SummaryResult, TranscriptionResult` | local: reuse original report/QA/summary/transcription validation |
| `src.services.contracts: AnalysisPort, AnalysisRequest` | local: injected service protocol and transport-neutral input including export flag |
| `src.utils.audio: detect_audio_format, validate_audio_file` | local: existing byte-signature/file-size validation and generated suffix |
| `src.agents.report: generate_report_pdf` | local lazy import: render original authorized PDF on demand |
| `src.graph.workflow: compile_workflow` | local lazy import: preserve real graph; no alternate inference pipeline |
| `src.security.audit: AuditLogger` | local lazy import: same audit sink using request-scoped engine transactions |
| `src.services.analysis: AnalysisService` | local lazy import: same orchestration as Gradio |
| `src.utils.config: load_config` | local lazy import: existing private provider/model configuration only at first analysis |
| `services.api.app: create_app` | local schema exporter/tests: build schema without model/database/secret loading |

Test-only additions: `time` measures signed token clocks; `pytest` provides
fixtures/parameterized assertions; cryptography `rsa` generates ephemeral 2048-bit
keys; `fastapi.testclient.TestClient` executes ASGI requests; SQLAlchemy `Session`
seeds synthetic owner data and `DBAPIError` verifies denied runtime writes;
`concurrent.futures.ThreadPoolExecutor` and `threading.Event` coordinate a real
overlapping-request test; `types.SimpleNamespace` supplies only the JWKS test key;
`src.services.contracts.PipelineResult` is the controlled concurrency fixture's
return contract. `reportlab.lib.utils` is monkeypatched to fail if untrusted PDF
markup requests an image. `services.api.provision_identity.link_identity` tests
operator linkage; `Authenticator` and its HTTP/key-network exceptions test JWKS
selection/outage. `tests.conftest.make_intake_result`, `make_qa_scores`,
`make_summary`, `make_transcription`, `make_wav_bytes` and integration `add_report`
produce synthetic reusable fixtures; `compile_report` assembles the real contract.
None is a production identity, benchmark model output or training observation.

Alternatives: a shared static API key cannot express externally verified tenant
identity; local token issuance would invent an auth authority. SQLite cannot
enforce these PostgreSQL row policies. A duplicate graph or fake async queue would
break compatibility/truthfulness. Swagger/ReDoc pages are disabled to avoid adding
an unintended product UI. No training or inference service split is needed here.

## 7. Concepts from first principles

**ASGI** is an asynchronous application interface: a server passes request context
and receive/send functions. Reading the body is an operation, so middleware can
authenticate before paying for a large upload. FastAPI builds routes on Starlette;
Uvicorn supplies the actual HTTP server. Blocking database/model work belongs in a
thread here so it does not stop the event loop servicing health requests.

**JWT verification** checks a signed statement using a trusted public key. Decoding
JSON alone proves nothing. Issuer says who issued it; audience says which API may
accept it; expiration bounds its lifetime; subject identifies a provider account.
This application's database decides whether that account is enabled and which
calls it can read. For example, an agent's valid token with `roles:["admin"]` still
gets 404 for a peer's call because the role comes from User, not that token field.

**Pydantic** checks the shape and constraints of boundary values. UUID routing
rejects malformed IDs with 422; a response model guarantees a predictable report
shape. It does not replace authorization or sanitize rendered HTML automatically.
The public DTO explicitly omits internal intake paths, and PDF text is escaped.

**RLS and owner authorization** solve different scopes. PostgreSQL row policies
keep tenant A from tenant B. Application SQL additionally keeps agent A from a
peer in the same tenant. A supervisor can see that peer only because the enabled
database user has a supervisory role. Both scopes are verified in tests.

**Null versus zero:** no calls means count zero; no measured QA average or job
progress means null. A future UI can display an empty/unmeasured state without
claiming zero quality or zero-percent completed work.

**Synchronous versus queued:** a 201 here means the request finished analysis and
stored a report. A durable queue would acknowledge submission before completion
and must separately track retries/idempotency/ownership. That is STEP_10; this step
does not imply it exists.

## 8. Data, security, reliability and performance

The identity table adds tenant/user composite foreign keys, unique
tenant/issuer/subject, indexes and ENABLE/FORCE RLS. Runtime can only SELECT
identity mappings; operator CLI cannot silently reassign existing subjects. The
current primary has **zero** mapped external identities: real sign-in is disabled.
The legacy service user stays disabled. No key, token, owner/runtime password,
private SQL URL or private RSA key is included in public evidence.

Requests cannot choose tenant/owner via upload fields. Verified context propagates
to graph cache, compatibility records, normalized reports and audit transactions.
Parameterized SQL and UUID/metadata/pagination validation restrict inputs. API
responses omit internal paths, use no-store and sanitize exceptions. Unknown
resources use uniform 404. Token size, key size, upload/body size and inference
concurrency are bounded. No wildcard CORS or public listener was added.

Read queries aggregate/count on the database and bound page size to 100, offset
to 10,000. Signature/DB resolution occurs per request, enabling immediate local
disablement; this adds latency compared with trusting cached roles. JWKS caches
keys for 300 seconds with a three-second retrieval timeout. Model initialization
is lazy and shared per process. Run one process on this machine; the semaphore
does not impose a distributed concurrency limit.

Limitations: no real IdP integration; no public deployment/rate-limit/gateway
validation; original Gradio remains trusted-local and must not be exposed as an
auth bypass. Existing hosted inference and original graph/provider logs can carry
call content; those logs stay private. A provider returned structured-output 400s
on an earlier live attempt and original retry logic recovered. Retry behavior is
not proof of provider reliability. Failed graphs may retain an intake temp copy;
successful API intake/upload artifacts are cleaned. There is no durable S3 audio
store, queue, request idempotency or automatic retry of POST. A committed report
followed by a later response/audit failure can require operator reconciliation.

Only consented bundled sample_01 and synthetic data were used. No gradient update,
dataset release, ASR improvement, emotion model, real diarization or Qwen adapter
was implemented or claimed. Device selection measured `('cpu', 'int8')`; peak
VRAM, throughput under load, WER and security penetration coverage are **Not
measured**.

## 9. Executed verification and acceptance gates

Commands used the repo's `.venv/Scripts/python.exe`; PostgreSQL tests were enabled
with the private isolated `.local/step08_test_admin_url` and
`.local/step08_test_app_url` file paths, not credential strings in command logs.

| Check | Actual result | Evidence |
|---|---|---|
| `python -m pytest tests/unit tests/security tests/api tests/integration -q --tb=short --junitxml=<evidence>/tests.xml` | **235 passed, 0 failed, 0 skipped, 27.60 s**, one Starlette/AnyIO deprecation warning; pytest-asyncio configuration warning also emitted | `tests.json`, `tests.xml` |
| API cases within that run | **37 passed**, including real RSA signature and restricted PostgreSQL checks | `test-metrics.json` |
| Ruff check `src/ services/ tests/ scripts/ stubs/ migrations/ app.py` | Pass, exit 0 | `ruff.json` |
| Ruff format check same scope | Pass, **101 files** | `format.json` |
| `python -m mypy src/ services/ app.py` | Pass, **52 source files** | `mypy.json` |
| `uv pip check --python .venv/Scripts/python.exe` | Pass, **136 packages compatible** | `dependencies.json` |
| `python -m compileall -q src services scripts app.py` | Pass | `compile.json` |
| `python scripts/check_hardcoded_keys.py` | Pass | `hardcoded-keys.json` |
| Pre-commit over explicit source/API/docs/config paths | Ruff, formatting, detect-secrets and hardcoded-key hook pass | `hooks.json` |
| Fresh separate PostgreSQL migration 0001→0002→0001→0002 | Pass; **14 tables including version**, populated identity downgrade refused; one row preserved | `migration.json` |
| Final Docker build / app recreation / Gradio config | Build/up exit 0; `/config` **200**, containers healthy | `docker-regression.json` |
| Primary preservation before/after recreation | **4** legacy + **4** canonical calls, **124** segments, **4** audit, **1** cache, **0** identities; exact count parity | `docker-regression.json` |
| Live loopback Uvicorn real sample | **201**, completed in **38.2086 s**, **38 segments**, generated QA **3.8/5**; persisted call list total 1; five reads/downloads **200** | `live-http.json` |

The live run used an ephemeral RSA fixture and isolated tenant with the **real
default AnalysisService/LangGraph, cached tiny Whisper and configured hosted
provider**, not the synthetic graph used by fast contract tests. Five reads were
metadata, transcript, QA, public report and PDF. The provider-generated QA number
is a result for one sample, not calibrated ground truth or model improvement.
Server bound loopback only and was stopped after verification.

Acceptance mapping:

- [x] Factory/versioned router: `create_app`, APIRouter, health/schema snapshot tests.
- [x] Typed calls/transcript/report/job contracts: generated OpenAPI and HTTP tests.
- [x] Authenticated identity and per-resource checks: RSA claim/signature tests,
  real database mapping/RLS, disabled-user revocation, owner/tenant/role checks.
- [x] Invalid input/error documentation: 401/403/404/413/415/422/429/502/503 tests,
  sanitization and chunked-body checks, `docs/api/README.md`.
- [x] Legacy workflow callable through adapter: HTTP upload contract with actual
  shared pipeline/persistence, plus real model/provider loopback run.
- [x] Regression: full local suite and rebuilt Docker Gradio; original comparison
  run **113 passed in 10.68 s**, recorded independently in `upstream-tests.json`.
- [ ] Real external-provider login/key rotation/tenant membership integration:
  **not executed; user has no provider**, explicitly remaining.
- [ ] Hosted GitHub CI and production ingress/load tests: not executed.

Failures encountered: initial full run **219 passed / 1 failed**, because the new
populated-downgrade exception text did not match the existing safety-test wording.
The refusal itself worked; wording was corrected and the final 235-case run passed.
Initial lint/type checks found formatting and two actual boundary typing mistakes
(nullable report JSON, AuditLogger engine passed positionally); corrected before
runtime validation. An initial live evidence write failed because its private
folder pointer contained a newline; stripped the pointer and repeated the full
live check. Only the successful repeat supplies published latency/sample metrics.
The secret hook initially flagged the intentionally invalid basic-auth URL used
to test URL rejection. Its literal synthetic fixture now has an explicit inline
allowlist comment; the scanner remains enabled. Initial and final hook outputs
are retained. No credential was removed from scanning globally.

## 10. Analytics and benchmark interpretation

| Metric | Baseline / formula / sample | Observed result | Interpretation |
|---|---|---|---|
| Versioned domain endpoint count | Pinned upstream had **0** project-owned versioned domain operations; enumerate current OpenAPI paths, one operation each | **12** schema operations: 2 public health/readiness + 10 protected domain operations; `/openapi.json` adds a thirteenth accessible HTTP route | Counts exclude Gradio-generated endpoints and framework docs; no frontend route count claim |
| Health p95 response ms | No comparable upstream endpoint, baseline **Not measured**; 5 warmups then 100 sequential pooled loopback HTTP requests; nearest rank `sorted(samples)[ceil(.95*n)-1]` | **1.070 ms**, n=100 | Single process/native Windows, no production concurrency/load claim |
| Authenticated call-list p95 ms | Same formula, 5 warmups + 100 requests, RSA token + real runtime PG mapping/RLS + empty owned-call page before upload | **9.423 ms**, n=100 | Includes signature, enabled-user lookup and list/count queries; not inference latency |
| Denial-focused API cases | JUnit case-name selection documented in `test-metrics.json`; count parameterized cases, not every assertion | **15 passed cases** within 37 API cases; original dedicated versioned-auth cases **0** | Includes invalid signed claims, disabled/unmapped/service users, bad credentials, ownership/tenant and revoke behavior |
| Real analysis duration | One consented sample; elapsed HTTP wall clock through real graph and persistence | **38.2086 s**, n=1; 38 transcript segments, QA3.8 | Functional evidence, no accuracy/speedup claim; provider variability/retries apply |
| Primary retained data | Exact counts before/after final Docker refresh | All six checked counts unchanged | Count preservation plus previous STEP_08 parity evidence; not a fresh full byte-level archive comparison |

Raw latency samples and conditions are in `live-http.json`. RTX 4060 8 GB was not
used for native inference. Production p95, peak RAM/VRAM, sustained throughput,
distributed contention, WER and security benchmark results are **Not measured**.

## 11. Technical questions and answers

**Q1. Why add FastAPI when Gradio already works?**
Gradio remains useful for the local human workflow. A typed HTTP contract lets a
future React client or authorized integration request data without relying on
Gradio component IDs. Both call AnalysisService, so QA/report behavior has one
implementation.

**Q2. Why are 401, 403 and 404 different?**
401 means identity could not be verified and includes a Bearer challenge. 403 means
the signed account is not enabled/mapped to an allowed role. 404 means the resource
is absent or outside the caller's scope. The last two resource cases deliberately
look identical to avoid disclosing a peer's or another tenant's calls.

**Q3. What does Pydantic guarantee?**
It validates field types, numeric ranges and UUIDs and produces machine-readable
schema. It does not grant permissions, prove a signature or make HTML safe. Those
are handled separately by Authenticator, scoped SQL and PDF escaping.

**Q4. Can a token containing an admin role bypass ownership?**
No. After verifying issuer/audience/signature, the API reads the enabled User role
from PostgreSQL on every request. A dedicated test signs an agent token with
`roles:["admin"]` and still receives 404 for the peer's call. Runtime cannot write
identity mappings to self-promote.

**Q5. Why not provide a local test login since no provider exists?**
A production-default fixture would turn tests into an unintended authority. The
default stays unavailable; test keys exist only in test/smoke processes with
explicit synthetic configuration. A real provider must own account login and
trusted tenant claims before external access can be enabled.

**Q6. What happens if persistence, inference or JWKS fails?**
Scoped persistence/inference failures return generic 502; unavailable database or
JWKS returns 503. The request scope and inference gate reset in finally blocks.
Errors contain a request ID, not provider details or SQL credentials. A failure
after a committed report may need reconciliation; POST is not idempotent yet.

**Q7. Does the job endpoint mean a queue exists?**
No. It reads existing PostgreSQL job state and checks its associated call. No
submission endpoint creates a fictional background job. Progress is null until a
worker measures it. STEP_10 must implement durable submission, retries and ownership
propagation independently of the current request ContextVar.

**Q8. Why retain both RLS and explicit owner/tenant SQL?**
RLS enforces tenant boundaries even when a query forgets a tenant predicate.
Application predicates additionally implement ownership, which the shared
tenant-only RLS policy does not express. Restricted runtime permissions keep
operator-managed user/identity configuration outside normal requests.

## 12. Decisions, limitations and handoff

Decisions: retain synchronous shared-service execution; use fixed RS256 external
verification plus database mapping/roles; require PostgreSQL for authenticated
API; no provider defaults; additive 0002 migration; disable unused API temp exports;
strip internal report metadata; escape generated PDF text. Full architecture
decision: [api-boundary.md](../architecture/api-boundary.md).

Open risks and limits: actual IdP integration/tenant-claim trust/rotation unverified;
public deployment and rate limiting unverified; inherited private provider logs,
trusted Gradio access and failed-graph intake retention remain; process-local
concurrency and synchronous requests are not durable execution. Hosted CI has been
prepared but not run. Deprecation/configuration warnings are documented. No
production-readiness, calibrated QA, model learning or load-capacity claim.

**Next eligible implementation step: STEP_10**, asynchronous job pipeline and
idempotency, after review of these explicit limitations. It must preserve tenant
and owner from the authenticated submission into broker/worker transactions,
define retry/deduplication/error states, and maintain these contracts. An external
IdP is a dependency for real-user deployment, not a reason to invent one or bypass
the boundary during isolated worker development. Do not assume ContextVar crosses
processes. This execution stops at STEP_09.

Next safe local command: `python scripts/export_api_schema.py`, or launch the
documented loopback factory using the restricted private connection. Without real
OIDC configuration its protected access remains disabled as intended.

Evidence checklist:

- [x] Actual source and upstream comparison, tracked diff and untracked inventory.
- [x] Generated schema and HTTP/denial/invalid-input tests.
- [x] Real restricted PostgreSQL ownership/RLS and safe migration recovery checks.
- [x] Full fresh local regression/type/lint/dependency results.
- [x] Real cached-model/provider loopback execution and raw latency samples.
- [x] Final Docker refresh and four original reports retained.
- [x] Private backups/secrets kept outside published artifacts.
- [x] Limitations, user missing-provider answer and STEP_10 handoff explicit.

See [API operations](../api/README.md), [OpenAPI](../api/openapi.json),
[progress](PROGRESS.md), [execution evidence](evidence/step09-20261025T083345Z/).

## 13. Approved ERP UI design / visual contract verification

Read `design/UI_DESIGN_SYSTEM.md`, `design/UI_ACCEPTANCE_CHECKLIST.md` and visually
inspected `design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png`: white rounded cards,
light-neutral canvas, quiet borders, dark text, green accents. Its mock values
were not used as real metrics. This step implements **backend contracts only**;
no frontend/CSS/React components were created and no new screen screenshot is
claimed. Visual styling, desktop/mobile responsiveness, contrast and keyboard
testing are **Not applicable to this code change / not yet verified for a future
frontend**, not passed by inference.

Specific routes support that future interface: `/api/v1/dashboard` gives actual
scoped counts and null averages; `/calls` gives bounded table data and truthful
empty arrays; `/calls/{id}/qa` preserves five dimensions and review flags;
`/jobs/{id}` returns actual state and null unmeasured progress. Errors have stable
code/message/request_id/retryable fields for accessible recovery panels. A future
green/neutral UI must render strings as text, announce loading/errors and support
keyboard access; the API does not choose chart palettes or manufacture progress.

Original Gradio layout and colors remain the regression baseline, not a certified
Commercially-style product UI. Final rebuilt Gradio config returned 200 with
primary rows intact. Swagger/ReDoc pages are disabled, so framework documentation
does not introduce an unintended blue-themed product screen. There are no new
visual tokens, blue/pink accents or model-result screenshots to audit here.

**Decision: PASS WITH LIMITATIONS — STEP_09 is implemented and validated locally;
real external-provider integration and deployment remain explicitly unverified.**
