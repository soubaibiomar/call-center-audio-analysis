# STEP_10 — Durable Redis background processing

**Latest GPU update:** missing runtime libraries corrected; cached tiny Whisper on
CUDA/float16 and a durable GPU job now pass. See the correction appendix below;
earlier GPU-unverified statements are retained as historical execution scope.

## 1. Header and execution context

**Status: DONE — PASS WITH LIMITATIONS.** Owner: Platform / Codex.
Date: **2026-10-26**, Africa/Casablanca. Windows11, PowerShell, uv-managed
Python3.12.15, Docker Desktop (engine29.9.2), PostgreSQL17.11, RTX4060 8GB available.
Branch `feature/project28-foundation`; working HEAD
`a37e4634af1d2947fc3c548d54e62bda0b0daf89`; independently preserved upstream
`fed4b610742c1337147281fcec8f2cdcc0a79be5`.

Read the master/index, complete STEP10 prompt, STEP08/09 implementation evidence,
STEP09 correction results, service/database/graph source, existing migrations,
API contracts and approved design rules. STEP09's four correction groups were
resolved and its **244-case** regression gate passed before proceeding; its A–O
appendix is finalized and historical evidence retained. No separate later quality
review document exists beyond that report/evidence.

Execution evidence: [step10-20261026T142036Z](evidence/step10-20261026T142036Z/).
The previous blocked/preflight report is copied into that directory rather than
discarded. No commit, push, adjusted timestamp or public deployment occurred.
Only STEP10 is implemented here; STEP11 is not started.

## 2. Goal and actual outcome

Authenticated users can upload audio and receive a **202 job ID**, while a separate
worker runs the existing call-analysis pipeline. PostgreSQL owns the state and
result, Redis/Dramatiq delivers work, and private S3-compatible storage keeps
verified audio. Duplicate submissions and duplicate deliveries preserve one
logical result. Failures, bounded retries, cancellation and timings are persisted.

The real default Docker CPU worker processed the bundled sample through
**queued → running → finished**. Upload returned202 in0.4272s; measured worker
execution8053.99ms, queue wait732.346ms, report/PDF reads200, and repeat upload with
the same key returned the same job. This used cached tiny Whisper/int8 and the
existing configured hosted provider, not a synthetic neural result.

Gradio and the synchronous API compatibility path remain functional. CPU/GPU
queues and resource definitions are separate; **GPU inference was not executed**.
No training, new checkpoint, model promotion or new frontend is claimed.

The user has no real OIDC provider. The normal API therefore remains fail-closed
for protected access. Tests/demo used ephemeral RSA identities and enabled users
in the isolated test database, not a production test-login switch.

## 3. Existing versus upgraded implementation

| Area | Actual upstream / preceding implementation | STEP10 behavior and symbols | Compatibility |
|---|---|---|---|
| Submission | Upstream Gradio synchronous; STEP09 synchronous HTTP201 | `routes/jobs.py:jobs_router`, authenticated multipart POST/jobs202 | Existing Gradio and `/calls/analyze` retained |
| Queue | No Redis/Dramatiq worker | `QueueBroker`, separate `analysis_cpu` / `analysis_gpu` actors | Additive delivery boundary |
| Lifecycle | STEP08 generic Job requires an existing call; no durable submission logic | New `AnalysisJob` ledger with owner/key/hash/state/attempts/times/metrics | Existing Job and GET fallback remain |
| Idempotency | No submission/delivery protection | `submit` fingerprint/unique key, advisory locks, deterministic call UUID | Per tenant + owner; never cross-user deduplication |
| Analysis | Original intake/ASR/summary/QA/report pipeline | Same AnalysisService; `JobExecution` supplies deterministic ID and commit hook | Legacy callers see no hook and retain random IDs |
| Persistence | Original report transaction, post-report audit | Report/canonical segments/job finished state commit together | No duplicate stored result after retry; audit still outside transaction |
| Audio | Original temp files; STEP09 request workspace | Private S3 object, MD5 upload check, persisted SHA256 and worker verification | Worker creates its own disposable workspace |
| Cancellation | No durable cancellation | queued→cancelled; running→cancelling; commit guard refuses cancelled result | Cooperative; no false claim of stopping ASR immediately |
| UI data | STEP09 job state/progress null | Added nullable call ID, queue, errors, timestamps and measured metrics | Existing legacy job fields retained; no fake percentage |
| Deployment | App/PostgreSQL Compose | Add Redis, object store, CPU worker, loopback API; GPU opt-in | Existing volumes/services preserved; no unrelated service changes |

The repository still contains accumulated uncommitted STEP01–10 changes. Ordinary
`git diff --stat` and `--name-status` cover tracked files, not all newly created
files; both outputs plus complete untracked status are preserved in evidence.
This is not presented as an isolated STEP10 commit. Previous source/history is
preserved; the inventory below identifies the actual step-specific surface.

## 4. File inventory and interfaces

| Path | Change | Purpose and inputs/outputs |
|---|---|---|
| `services/workers/__init__.py` | New | Worker package; no import-time model/broker startup |
| `services/workers/settings.py` | New | Private JSON config → immutable QueueSettings, limits/tenant allowlist |
| `services/workers/storage.py` | New | UUID-scoped private S3 put/get, length and hash checks |
| `services/workers/jobs.py` | New | Admission/idempotency, scoped reads/cancellation, persisted failure/backoff |
| `services/workers/runner.py` | New | Exclusive execution, owner check, shared service, atomic completion hook |
| `services/workers/broker.py` | New | Redis actor declaration and PostgreSQL outbox dispatch/redelivery |
| `services/workers/runtime.py` | New | CPU/GPU CLI, one inference thread, dispatcher, graceful stop |
| `services/api/routes/__init__.py`, `jobs.py` | New | Versioned authenticated upload/cancel route group |
| `services/api/app.py` | Modified | Register job routes and scoped durable-job read before legacy fallback;409 envelope |
| `services/api/schemas.py` | Modified | Backward-compatible expanded JobStatus; unmeasured progress remains null |
| `services/api/db/models.py` | Modified | New AnalysisJob mapping, constraints, owner/call foreign keys and dispatch index |
| `services/api/db/settings.py` | Modified | Reviewed current revision0003_jobs |
| `migrations/versions/0003_durable_jobs.py` | New | Additive ledger/outbox, ENABLE/FORCE RLS, runtime grants, safe downgrade guard |
| `src/services/job_execution.py` | New | Optional request-local deterministic result ID and before-commit callback |
| `src/agents/intake.py` | Modified | Use job ID only inside job execution; workspace behavior preserved |
| `src/agents/report.py` | Modified | Invoke optional completion callback in the report transaction |
| `src/agents/transcription.py` | Modified | Explicit cpu/cuda override for dedicated workers; original autodetection otherwise |
| `stubs/ctranslate2.pyi` | New | Accurate type for the used CUDA capability symbol, no runtime implementation |
| `infrastructure/compose/queue.local.yml` | New | Digest-pinned Redis/S3, private secrets, volumes, resource limits and worker/API services |
| `infrastructure/compose/bootstrap-storage.sh` | New | Idempotent private bucket + non-admin runtime IAM policy provisioning |
| `scripts/prepare_queue_local.py` | New | Exclusive private file creation; existing credentials/config preserved |
| `tests/workers/conftest.py` | New | Real S3/Redis/PG settings plus isolated signed-user fixtures |
| `tests/workers/test_durable_jobs.py` | New | Twelve recovery/idempotency/integrity/authorization/state tests |
| `tests/workers/restart_child.py` | New | Actual child worker killed during a controlled synthetic inference stage |
| `tests/api/test_api.py` | Modified | Expected documented API paths12→14; existing checks retained |
| `requirements.txt`, `pyproject.toml`, `PROJECT28_REQUIREMENTS.lock.txt` | Modified | Direct runtime pins, SDK stubs and actual portable environment freeze |
| `.env.project28.example` | Modified | Commented private queue-config path; no credentials |
| `docs/api/README.md` | Modified | Current durable routes, states and operational-guide link alongside sync compatibility |
| `docs/api/openapi.json` | Regenerated | Actual14-path contract; generation equality tested |
| `docs/development/background-jobs.md` | New | Reproducible setup/HTTP/recovery/security/limitation guide |
| `docs/architecture/durable-jobs.md` | New | Delivery/state/transaction/worker architecture decision |
| This report, `PROGRESS.md`, evidence | New/updated | Executed proof, historical failures, metrics and handoff |

No source files deleted. STEP09 correction files/report remain in place; those
corrections are distinguished from the new STEP10 behavior. Migration0001 remains
unchanged. Private backups, provider output and generated credentials remain in
ignored `.local/`; none are release artifacts.

## 5. Important code and algorithms

### Admission, object integrity and stable request identity

`submit(engine, storage, settings, principal, data, key, queue, caller, department)`
computes SHA256 over audio and a separate fingerprint over hash + queue + metadata.
A transaction-scoped advisory lock serializes admission for that tenant. It checks
an existing tenant/owner/key before checking capacity, so a duplicate still returns
the same job at capacity. Changed input gets409. Capacity counts nonterminal jobs,
default32 per tenant; a new request at capacity gets429.

The server generates a UUID job ID and object key. S3 put supplies Content-MD5,
SHA256 metadata and length; HEAD confirms uploaded metadata/length. Only after
storage succeeds is the job row added and committed. A storage failure cannot
return a job ID. A DB failure after object put can leave an orphan object: reviewed
object garbage collection is a remaining limitation, not concealed as atomic S3/SQL.

Workers fetch at most expected length+1 and recompute SHA256 against the trusted
job row. A tampered object fails permanently before analysis, with
`audio_integrity_failed`. Real MinIO also rejected deliberately incorrect MD5 with
**BadDigest**; the runtime identity cannot list/administer buckets.

### Database authority and at-least-once delivery

`QueueBroker.dispatch` iterates the operator-configured tenant allowlist, establishes
RLS scope and selects due queued/retrying/running/cancelling rows with
`FOR UPDATE SKIP LOCKED`. It sends only `(tenant UUID, job UUID)` and records the
publication time. Default15s republishing recovers missing/ambiguous delivery.
If send fails, the DB transaction rolls back and the job remains recoverable.

A publish may reach Redis before its acknowledgement is lost; a dedicated test
creates exactly that ambiguity and proves duplicate messages still yield one
analysis. PostgreSQL rows, not queue length, determine the user-visible status.
Each queue has a separate Dramatiq actor and worker consumer. Dramatiq inference
retries are disabled (`max_retries=0`) so they cannot multiply the DB attempt budget.

### Exclusive execution and atomic completion

`JobRunner.run` validates both UUIDs and allowed tenant, then acquires a session
advisory lock for the job. That connection is held until execution finishes; the
lock survives short DB commits and is released by PostgreSQL on process death.
A concurrent duplicate fails to acquire it and performs no inference.

`_run_locked` checks queue, terminal state, due time, attempts and current enabled
owner. It increments attempts and records running/start time **before** inference.
It downloads verified audio, establishes its own tenant/owner context and temporary
workspace, and invokes the existing AnalysisService. No duplicate ASR/QA/report
implementation is introduced. The service/model is created lazily and reused.

```python
with job_execution(JobExecution(UUID(job_id), commit)):
    analyze_call(service, AnalysisRequest(path, caller, department, downloads=False))
```

The context supplies a deterministic call UUID to original intake. `persist_report`
calls the optional hook in its existing transaction after normalized rows are
available, before commit. The hook locks/rechecks the job, rejects cancellation or
an unexpected call ID, sets its call ID/status/finish time/metrics and lets the
same SQL transaction commit both result and completion. If the hook raises, report
and canonical rows roll back. Legacy synchronous calls have no hook.

After commit, a retry sees finished and performs no analysis. Even an audit failure
after report commit cannot turn that job into failed/retry it: `record_failure`
preserves terminal states. A dedicated post-commit failure test checks this.
Computation before a crash may repeat; this is not exactly-once inference/billing.

### Retry, failure and cancellation

`record_failure` stores sanitized reason/timing/attempt counters. Default maximum3
attempts; configuration is bounded1–5. Delay is:

```python
min(300, settings.backoff_seconds * 2 ** max(0, attempts - 1))
```

Default base5 seconds. A due-time check prevents early duplicate messages from
executing. Exhaustion becomes failed; integrity failure is permanent. Failure
codes include analysis_failed, audio_integrity_failed, owner_disabled,
attempts_exhausted and report_not_committed. No raw provider/SQL exception is stored
in the new ledger. Finished metrics measure first-start queue wait and successful
attempt execution; failed metrics include last attempt duration/retry counters.

`owned_job` applies tenant and optional owner filters for reads and cancellation.
Queued/retrying cancellation is immediately cancelled. Running cancellation first
becomes cancelling; the completion hook refuses committing a result, then failure
reconciliation records cancelled. This cooperates at commit boundaries rather than
pretending to interrupt an in-flight hosted request or ASR operation instantly.

### Process entrypoints and deployment

`python -m services.workers.runtime cpu|gpu` starts one inference thread and an
independent dispatcher loop. SIGTERM/SIGINT request shutdown. CPU explicitly uses
Whisper cpu/int8. GPU has a separate queue/resource reservation and checks CUDA
capability; no silent CPU fallback. Actual GPU runtime/inference remains unverified.
Training is not present and cannot be requested via these jobs.

The overlay adds local Redis AOF, MinIO named storage, a restricted storage IAM
identity, CPU worker and loopback API. GPU is profile-only. Existing app/PostgreSQL
volumes stay intact. S3 and Redis credentials are mounted privately; the API/worker
do not receive storage root credentials. MinIO browser is disabled. Shared source
is read-only with owned tmpfs workspaces in long-running application containers.

## 6. Imports, versions and dependency rationale

New direct runtime dependencies: **dramatiq[redis]2.2.1**, **redis8.1.0**,
**boto3 1.43.118** (botocore1.43.118, s3transfer0.19.3, jmespath1.1.0 resolved).
Dev-only **boto3-stubs[s3]1.43.118** supplies S3Client typing; the installed generated
S3 stubs are1.43.106. AWS's supported dateutil constraint resolved
python-dateutil3.0.0→2.9.0.post0; actual dependency compatibility passes. No Conda,
training dependency or silently changed model was introduced.

Local server images are pinned to observed digests: Redis7.4 mirror
`57e4255cc971b1c8d6f8a6ca283ac01bc3ecdd914273ef6bfaede87aaecd6541`; cached MinIO
RELEASE.2025-02-07T23-21-09Z
`640c22768ed5dbc92eacc14502a1b06a1c708fa60431345c78dfc22917062e93`.
Cached release functionality was tested; a current security/patch assessment is
required before production. No TLS verification was disabled to obtain images.

| Imported module / symbols | Origin, meaning, use and reason |
|---|---|
| `argparse` | stdlib: restrict worker queue/CLI modes |
| `base64`, `hashlib` | stdlib: encode S3 MD5; compute SHA256 integrity/fingerprints and stable advisory-lock keys; MD5 is not the trust hash |
| `json`, `os`, `pathlib.Path` | stdlib: private configuration, environment overrides and generated owned file paths |
| `dataclasses.dataclass, field` | stdlib: immutable config/context; hide credentials from repr |
| `collections.abc.Callable, Iterator` | stdlib: injected shared-service factory and context generator contracts |
| `contextlib.contextmanager`, `contextvars.ContextVar` | stdlib: restore optional deterministic result/commit-hook state after each attempt |
| `datetime.UTC, datetime, timedelta`, `time.perf_counter` | stdlib: UTC persistence, due/backoff comparisons and measured elapsed execution |
| `uuid.UUID, uuid4` | stdlib: validate tenant/job IDs and generate new logical job identities |
| `typing.Annotated, Literal, cast, TYPE_CHECKING` | stdlib: bounded request contracts, explicit SDK/untyped constructor boundary and type-only SDK client import |
| `logging`, `signal`, `threading.Event` | stdlib: sanitized dispatcher warnings and cooperative process shutdown |
| `secrets` | stdlib: generate private local credentials without public defaults |
| `dramatiq.actor, Worker` | third party: declare separate queue actors and run a single inference thread |
| `dramatiq.brokers.redis.RedisBroker` | third party: actual Redis delivery, namespaces and heartbeat recovery; constructor has an explicit typed boundary |
| `dramatiq.middleware.Retries` | third party: disable a second inference attempt budget; PG controls retry/backoff |
| `redis.Redis` | third party, recovery validation: authenticated durable marker/PING; no Redis flush |
| `boto3.client`, `botocore.config.Config` | third party: S3v4 client, explicit credentials/region, path addressing, timeouts/retry limits |
| `botocore.exceptions.BotoCoreError, ClientError` | third party: translate upload storage/network failures to sanitized503; inspect real denial/BadDigest in tests |
| `mypy_boto3_s3.client.S3Client` | dev/type-only: precise SDK operation inputs/outputs; no inference/runtime behavior |
| `sqlalchemy.select, func, text`, `Engine`, `Session` | existing third party: scoped queries/counts, parameterized locks, pool/transaction and completion callback contract |
| `sqlalchemy as sa`, `alembic.op`, `postgresql.JSONB` | existing third party: frozen additive DDL, owner constraints, lifecycle checks, numeric JSON metrics |
| `fastapi.APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile` | existing third party: authenticated route group, bounded multipart/idempotency header, typed request state and errors |
| `starlette.concurrency.run_in_threadpool` | existing third party: S3/SQL admission outside the async event loop |
| `ctranslate2.get_cuda_device_count` | existing Whisper dependency: reject unavailable GPU execution; local stub describes that one real symbol |
| `services.api.auth.Principal` | local: verified tenant/user/role; no raw token crosses broker |
| `services.api.db.models.AnalysisJob, User` | local: authoritative ledger and enabled owner lookup |
| `services.api.schemas.JobStatus` | local: typed honest states, timestamps, optional call ID and metrics |
| `services.workers.settings.QueueSettings` | local: explicit private limits/allowlist/addresses |
| `services.api.db.settings.database_url` | local: mutually exclusive private database URL/file loading for workers; never log the value |
| `services.api.routes.jobs.jobs_router` | local: attach typed durable upload/cancel routes to the authenticated versioned router |
| `services.workers.storage.AudioStore, IntegrityError` | local: verified UUID object access and permanent tampering signal |
| `services.workers.jobs` lifecycle helpers | local: scoped admission, read/cancel, UTC clock, lock keys, failure/backoff and terminal-state authority |
| `services.workers.runner.JobRunner`, `broker.QueueBroker` | local: execution/delivery separation; no alternative inference stack |
| `src.database.connection.get_engine, init_db, session_scope`, `database_identity` | local: schema guard, transaction cleanup and verified worker tenant context |
| `src.services.job_execution.JobExecution, current_execution, job_execution` | local: optional deterministic call/atomic-commit hook; legacy behavior unchanged when absent |
| `src.services.contracts.AnalysisPort, AnalysisRequest`, `services.api.analysis.analyze_call` | local: reuse STEP07 service contract and typed report adapter |
| `src.graph.state.CallReport`, `src.utils.audio_workspace.audio_workspace`, `src.utils.audio.validate_audio_file` | local: original report, attempt-owned files and original input validation |
| Lazy `compile_workflow`, `AuditLogger`, `AnalysisService`, `load_config` | local: actual existing graph/provider/audit construction only on first worker inference |

Tests additionally import pytest, TestClient, ThreadPoolExecutor/Event, dataclasses
replace/asdict, subprocess/sys, existing synthetic report/audio factories and
CallRecord. They create controlled faults, real child processes and real storage/
SQL/delivery observations. They are not production identity issuers or replacement
neural implementations. Exact parsed imports are recorded in `source-imports.json`.

Reference consulted for actual API semantics: [Dramatiq2.2.1 source guide](https://github.com/Bogdanp/dramatiq/blob/v2.2.1/docs/source/guide.rst).
Original FastAPI/Pydantic/SQLAlchemy versions remain as previously pinned. Windows
freeze is environment evidence, not a portable binary lock for every platform.

## 7. Concepts from first principles

A **queue** carries work requests between independent processes. Putting a UUID
into Redis does not make the result durable by itself: a message might be delivered
twice or a worker might die before acknowledging it. The **job ledger** records
what the application owes the user, independently of transport state.

An **outbox** means storing pending delivery alongside authoritative application
state. Here a due job row itself is the outbox. If publication acknowledgement is
lost, replay is expected. **Idempotency** then makes repeated requests/deliveries
refer to the same logical work, rather than pretending duplicates never happen.

An **advisory lock** is an application-selected PostgreSQL lock. A short tenant
lock serializes admission; a different job lock prevents simultaneous execution.
Releasing a crashed process's connection releases its execution lock. Neither lock
grants permission to other tenants; RLS and verified ownership still apply.

An **atomic transaction** commits all SQL effects or none. The optional report hook
places job completion inside the result transaction. It cannot make hosted model
calls or S3 put atomic with PostgreSQL. Repeated computation after a pre-commit
crash therefore remains possible, while duplicate committed reports are prevented.

**Object storage** addresses bytes by key, not host filesystem paths. UUID-derived
keys prevent filename traversal. Worker SHA256 recomputation verifies the fetched
bytes match the trusted ledger. MD5 covers the S3 upload protocol; it is not used
as a security identity or an authorization decision.

**CPU/GPU separation** selects different consumers and resource availability. It
does not mean all upstream stages became separate microservices or that GPU
inference was benchmarked. **Cancellation** is cooperative: the state can reject
the result even while an already issued computation needs time to finish.

## 8. Security, reliability, data and model handling

The existing signed-identity boundary runs before multipart parsing. New routes
also use the shared dependency so OpenAPI declares bearer access. Tenant/owner
are never accepted as upload fields. Idempotency keys are bounded ASCII; file names
are ignored as paths; existing upload/body/metadata limits remain.

AnalysisJob has a tenant FK, composite owner/call FKs, unique tenant/owner/key,
valid queue/state/attempt constraints, dispatch index and ENABLE/FORCE RLS.
Runtime has CRUD only on operational data; user and identity administration remains
owner-only. Worker scopes come from private operator allowlists and stored rows,
not a trusted user_id supplied in a Redis message. Owner enablement is checked at
start. Agents read/cancel only owned jobs; other resources return404.

S3 is private; no presigned/public object route or credentials go to clients.
Separate runtime storage user has only GetObject/PutObject for the project tenant
prefix; bucket listing/admin is denied. Root provisioning keys never enter API/
worker containers. Redis is password protected, AOF-backed, bounded memory and
no-eviction. Local ports are loopback; remote deployment must use proper TLS,
provider/ingress/rate-limit policies and reviewed patched images.

New failure records contain reason codes and numeric measurements, not raw
exceptions/audio/transcripts. Existing graph/provider logs and legacy audit detail
can contain call content; those remain private and are a disclosed inherited
limitation. No training is authorized by upload, no gradient update ran and no
model improvement is inferred from a successful job.

Durable S3 objects currently require operator retention/GC; failed DB admission
can orphan an object. Calls' SQL retention can also remove their linked job while
an object still needs reviewed cleanup. Native hard-kill temp artifacts may need
cleanup; Docker tmpfs is disposable. The post-report audit is not part of the new
completion transaction. These are production-hardening limits, not hidden features.

## 9. Verification and actual results

Isolated PostgreSQL owner/runtime files were enabled through
PROJECT28_TEST_ADMIN_URL_FILE and PROJECT28_TEST_APP_URL_FILE. Local S3/Redis used
private `.local/queue_host.json`; no test requiring these services was skipped.

| Executed check | Actual result | Evidence |
|---|---|---|
| `python -m pytest tests/unit tests/security tests/api tests/integration tests/workers -q --tb=short --junitxml=<evidence>/tests.xml` | **256 passed,0 failed,0 skipped in43.84s** | tests.json / tests.xml |
| Worker cases within full run | **12 passed**, real Redis/PG/S3 with controlled graph faults | JUnit cases under tests.workers |
| `ruff check src/ services/ tests/ scripts/ stubs/ migrations/ app.py` | Pass | ruff.json |
| `ruff format --check` same paths | Pass, **120 files** | format.json |
| `mypy src/ services/ app.py` | Pass, **63 source files** | mypy.json |
| uv dependency compatibility, compileall, hardcoded-key scan | All pass | dependencies/compile/hardcoded-keys JSON |
| Explicit-path pre-commit hooks | Ruff, format, detect-secrets, hardcoded-key checks pass | hooks.json |
| Fresh migration0003 and empty base down/up; `alembic check` | Pass, **15 tables including version**, job RLS enabled/forced; no metadata operations | fresh-migration.json |
| Primary additive migration + private archive | Revision0003 applied to primary/test; backup size/hash recorded, bytes kept private | migration-upgrade.json |
| Actual loopback HTTP → Docker default CPU worker |202, queued/running/finished; report/PDF200; repeated upload same ID | real-worker-http.json |
| MinIO incorrect Content-MD5 | Rejected **BadDigest** | operational-checks.json |
| Redis/object-store scoped service restart | AOF marker and S3 bytes/hash retained | service-restart.json |
| Final API missing-IdP default | health200, ready503, protected calls503 | operational-checks.json |
| Primary compatibility preservation |4 legacy/4 canonical calls,124 segments,4 audit,1 cache,0 identity links,0 new primary jobs; Gradio config200 | operational-checks.json |

The twelve worker cases cover concurrent duplicate submission and conflicting key;
admission saturation; transient retry then finish; exhausted terminal failure;
queued/in-flight cancellation rollback; object tampering/private bucket access;
CPU refusing GPU jobs; HTTP job ID/owner checks; actual Redis duplicate delivery;
process kill while running then restart; post-commit audit failure; overlapping
deliveries; and lost publication acknowledgement. One case may cover multiple
assertions; these are test-case counts, not fabricated coverage percentages.

The kill/restart test runs the real production JobRunner/QueueBroker in child
processes with synthetic inference, abruptly kills the first after running begins,
then starts a replacement and verifies attempts2 with exactly one stored report.
This proves recovery mechanics without pretending that its synthetic graph ran ASR.
The separate real bundled-sample Docker run validates the actual configured model.

Warnings: Starlette/AnyIO deprecation and pytest-asyncio loop-scope configuration
warning remain. Hosted GitHub CI, production load and actual GPU inference were
**NOT EXECUTED**. No TS/ESLint/Playwright check applies: no frontend changed.

Acceptance mapping:

- [x] Upload returns job ID: actual signed loopback POST/jobs202 and real worker run.
- [x] Retry cannot duplicate a logical analysis result: unique request identity,
  exclusive execution, atomic completion, actual duplicate/crash/ack-gap tests.
- [x] Failure reasons and metrics persisted: exhaustion/tampering tests read terminal
  codes, attempts/timestamps and durations from restricted PostgreSQL sessions.
- [x] Worker restart, duplicates, recovery and saturation: real-service cases above.
- [x] Authorized object storage/integrity: private IAM denial, BadDigest and worker SHA failure.
- [x] CPU/GPU queue separation: distinct consumers/resources; CPU refusal test.
- [ ] Actual GPU inference/production provider identity/remote deployment: explicitly unverified.

## 10. Measured analytics and interpretation

Upstream had no equivalent durable queue. Baseline queue wait/jobs-per-minute/
retry rate are **Not measured**, not invented zero-performance values.

| Metric | Actual execution and formula | Observed value / limitation |
|---|---|---|
| Queue wait p95 | Twelve synthetic coordination jobs, real S3/Redis/PG, one worker thread; nearest rank sorted[ceil(.95*n)-1] over persisted first-start waits | **557.692ms**, n12 |
| Jobs/minute |12 finished /0.8597463 elapsed seconds ×60; timing includes tiny-audio admission and coordination | **837.456 jobs/min**, **synthetic coordination only**, short sample; not ASR/production capacity |
| Retried jobs |1 deliberately faulted job /12 | **8.333%** injected scenario, not observed provider reliability |
| Retry attempt rate |(13 attempts−12 jobs)/13 | **7.692%** injected scenario |
| Failures | Synthetic batch:1 failed attempt, all12 eventually finished | **0 terminal failures** in that batch; terminal failure behavior separately exercised by tests |
| Real sample queue wait | Stored actual first-start timing | **732.346ms**, n1 |
| Real sample worker execution | Measured elapsed storage/inference/persistence through completion hook | **8053.986ms**, n1; CPU tiny/int8 + configured hosted provider |
| Real sample upload / overall | Observed HTTP timing / until duplicate/read verification finished | **0.427247s /9.920295s**, n1 |

Raw samples, all batch metrics, conditions and counts are in
coordination-benchmark.json and real-worker-http.json. The batch graph returns
synthetic typed content and intentionally fails once; it measures mechanics, not
neural throughput. The real sample has no accuracy ground truth. No speedup against
earlier samples is claimed because hardware/process/provider conditions differ.
WER/DER/F1, peak RAM/VRAM, sustained/distributed throughput and production p95 are
**Not measured**. No training/model promotion occurred.

## 11. Technical questions and answers

**Q1. Why not FastAPI BackgroundTasks?** An API process restart must not forget
accepted work. Workers need independent resources, bounded attempts and a durable
ledger. BackgroundTasks alone does not supply those guarantees.

**Q2. Is delivery exactly once?** No. Redis publication acknowledgements and worker
acknowledgements can be lost. Replays are expected; locks, deterministic result
identity and the SQL completion transaction prevent duplicate committed results.
Pre-commit model computation/hosted billing may repeat after a crash.

**Q3. Why store state in PostgreSQL?** It remains authoritative across Redis/worker
restarts and can atomically finish a job with its report. Queue length cannot tell
a user whether their report committed or was cancelled.

**Q4. What happens when a request key is reused?** Same owner/tenant and identical
audio/metadata returns the same job, even when the queue is full or the job ended.
Changed content or queue/metadata gets409. A different user never learns another
user's job through shared audio hashing.

**Q5. Why both MD5 and SHA256?** S3 Content-MD5 supplies transport-integrity checking
and was negatively tested against MinIO. The trusted job's SHA256 is recomputed by
the worker to detect changed stored bytes. Neither hash grants authorization.

**Q6. Can cancellation stop inference immediately?** Not safely for every upstream
ASR/hosted call. Running becomes cancelling; the shared report transaction refuses
to commit after cancellation and records cancelled when control returns. Queued
work cancels without executing.

**Q7. How does an interrupted worker recover?** PostgreSQL drops its session lock
on process death. Due running rows can be republished and a replacement claims
the next bounded attempt. The actual child kill/restart test produced one result.

**Q8. Why are GPU results missing?** Resource/queue separation is implemented, but
no CUDA inference validation ran. The optional worker must use a verified CUDA
runtime and cannot silently consume GPU work as CPU. CPU is the tested default.

**Q9. What if audit fails after the report commits?** The job already finished
atomically with its report, so a replay must not duplicate analysis. A dedicated
test checks that invariant. Audit reconciliation remains a disclosed limitation.

**Q10. Does analysis authorize training?** No. Jobs only run the existing inference
workflow. Training has no endpoint/worker here and requires separate dataset,
consent, evaluation and promotion steps.

## 12. Problems, decisions, remaining limits and handoff

Docker Desktop was initially stopped. The guessed system-wide executable path was
absent; inspected its registered per-user installation and started that installed
copy. No reset, volume deletion or unrelated service reconfiguration was used.
DockerHub Redis download hit certificate validation failure; used an official mirror
without weakening TLS. MinIO latest locations denied access; an already cached,
digest-identified release included its CLI and passed actual S3/IAM/integrity tests.
That older image needs a production patch assessment.

Initial Compose tmpfs flow-list commas produced an invalid mount item; quoted
the complete mount values and reran actual startup. Initial type checks identified
Dramatiq's constructor/actor overload typing and an untyped CUDA capability symbol;
used the documented decorator form, explicit callable boundary and a one-symbol
stub. Test fixture registration/import style and formatting were corrected without
deleting checks. A private benchmark script initially could not import repository
test helpers; supplied its repository import path and collected only the successful
run's metrics. These were setup/test-harness issues, not fabricated successful runs.
An exact PowerShell runbook check exposed an appended CRLF being interpreted as a
shell command after bootstrap. The supported Python helper now passes normalized
script bytes directly; actual bootstrap succeeds and preserves private file hashes.

Decisions: modular monolith + independent workers; PostgreSQL authority/outbox;
private S3; per-owner request keys; bounded persisted attempts; cooperative cancel;
atomic report completion; retain legacy APIs; no training and no automatic step11.
Architecture: [durable-jobs.md](../architecture/durable-jobs.md).
Operations: [background-jobs.md](../development/background-jobs.md).

Remaining: no real IdP; GPU/remote TLS/ingress/rate-limit/load validation absent;
explicit worker tenant onboarding; object retention/GC and possible orphan objects;
native hard-kill temp artifacts; original private provider/audit content; audit
outside completion transaction; possible repeated pre-commit inference costs;
cached storage image patch review; hosted CI for real queue services not run.
No blocking failure remains for the tested local CPU scope.

**Next eligible step: STEP_11 — integrate Qwen through a safe model-provider
adapter.** Keep the new worker's AnalysisPort boundary, tenant identity, deterministic
ID, commit callback, private storage and attempt budget intact. No model/provider
replacement or large download is authorized by declaring this step done. STEP11
must execute its own prompt and real provider/model tests. It is not started here.

Evidence checklist:

- [x] Current prompt/source/prerequisite inspection and preserved failed history.
- [x] Actual HTTP202, private storage, real Redis/SQL and real model worker path.
- [x] Retry/duplicate/crash/cancel/saturation/failure/integrity regressions.
- [x] Fresh migration roundtrip and model-metadata comparison.
- [x] Full fresh256-case suite, lint/format/types/dependencies and operational checks.
- [x] Actual metric samples/conditions with synthetic versus model distinction.
- [x] Original four primary reports and associated row counts preserved.
- [x] Explicit missing-provider/GPU/production/privacy limitations.

## 13. Approved ERP UI design / visual contract verification

Backend-only change: no React, CSS, chart, page or new product screen. Read the
approved Commercially green/neutral contract and preserve Gradio as baseline.
Desktop/mobile screenshots, contrast, keyboard and responsive checks are **Not
applicable to this change**, not passed by inference. No blue/pink product theme,
Swagger UI or MinIO browser screen was introduced.

Specific frontend contracts are truthful: upload202 supplies a stable job ID;
GET/jobs/{id} supplies queued/running/retrying/cancelling/finished/failed/cancelled,
attempts, nullable call ID, failure code, timestamps and real timing metrics.
Unmeasured progress remains null. Future green/neutral ERP upload/table screens
must announce actual state, offer cooperative cancel/recovery and avoid a fake
percentage or premature completion. Gradio config200 and existing tests preserve
the original interface; its styling is not certified as the final ERP design.

**Final decision: PASS WITH LIMITATIONS — local CPU durable jobs are implemented
and executed; real IdP, GPU inference and production readiness remain unverified.**


# Failure Analysis and Correction Report — GPU runtime

2026-10-26. This appendix supersedes the earlier GPU-runtime limitation for the
verified tiny Whisper workflow only. STEP11 has not been started.

### A. Executive Summary
Hardware and Docker CUDA enumeration worked, but actual transcription failed in
the former CPU-derived GPU worker image. A dedicated GPU image now installs the
missing runtime libraries. Real CUDA transcription, complete durable GPU job,
260 regression cases and original CPU preservation checks pass.

### B. Failure Inventory
| ID | Failure | Component | Severity | Reproduction / cause | Status |
|---|---|---|---|---|---|
| GPU01 | Library libcublas.so.12 missing at first encoder execution | GPU worker image | P1 | Cached tiny model loaded, but real10-second transcription raised RuntimeError; base CPU image lacked cuBLAS/cuDNN | Corrected and hardware-tested |

No primary data loss or driver defect was observed. The initial failed verification
and raw library probes remain in the separate GPU-verification evidence directory.

### C. Root-Cause Analysis
Docker injected libcuda.so.1 and exposed one RTX4060, so capability checks alone
passed. User-space cuBLAS12, cuBLASLt12 and cuDNN9 were absent. Faster Whisper's
model constructor did not execute the encoder, so its apparent success concealed
the problem until real transcription. This is an image ABI/dependency defect,
not a need to replace a trained model or downgrade the working host driver.

### D. Code Corrections
Dockerfile.gpu extends the existing application image and installs pinned Linux
NVIDIA runtime wheels. Build-time ldconfig registers their library directories
without hardcoding a Python minor-version path. Compose worker-gpu selects the
new project28-app:gpu image; worker-cpu retains its previous image.
verify_cuda_runtime checks device count and loads all three required SONAMEs before
any job is consumed, with explicit errors and no CPU fallback. The public hardware
probe consumes lazy transcription results and verifies actual cuda/float16 output.

### E. Import and Dependency Analysis
New GPU-only packages: nvidia-cublas-cu12==12.9.2.10,
nvidia-cudnn-cu12==9.27.0.42, nvidia-cuda-nvrtc-cu12==12.9.86. NVRTC is a declared
cuBLAS dependency. CPU requirements, host Python packages, model and driver remain
unchanged. New stdlib ctypes.CDLL verifies library loading. The probe uses existing
ctranslate2/faster_whisper, json output, subprocess for ffmpeg, TemporaryDirectory
for owned clip cleanup, Path for files and perf_counter for real elapsed time.
Controlled startup tests use pytest monkeypatches; those are not GPU benchmarks.

Primary runtime guidance: https://github.com/SYSTRAN/faster-whisper#gpu confirms
CUDA12/cuDNN9 requirements and Linux NVIDIA wheels. Package versions and dependencies
were checked against PyPI metadata and executed in the built GPU image.

### F. File-by-File Changes
Created Dockerfile.gpu, requirements.gpu.txt, scripts/check_gpu_runtime.py and
tests/unit/test_gpu_runtime.py. Modified services/workers/runtime.py and
infrastructure/compose/queue.local.yml. Updated docs/environment/GPU_VERIFICATION.md,
docs/development/background-jobs.md, docs/architecture/durable-jobs.md, PROGRESS.md
and this report. New immutable GPU-correction evidence directory. No source files
removed, no CPU image retagged, no credentials changed, no commit or push.

### G. Original vs Improved Repository
Pinned upstream remains the Gradio baseline, with no separate durable GPU worker
image. STEP10 added CPU/GPU delivery separation but initially shared a CPU image.
The correction makes the GPU image runnable while preserving the original CPU
analysis path and the STEP10 identity/idempotency/commit contracts.

### H. Architecture Impact
Only GPU runtime provisioning/startup changes. GPU and CPU retain separate queues
and one inference thread each. The shared AnalysisService, S3 checks, PostgreSQL
job authority, cancellation and atomic completion behavior are unchanged. The
normal local GPU worker is now running; test identities were confined to an
isolated database/namespace and one-off verification containers.

### I. Tests and Validation
- Initial actual GPU transcription: RuntimeError for missing libcublas.so.12;
  driver library loadable, cuBLAS/cuBLASLt/cuDNN probes failed.
- Corrected public probe: `docker compose --env-file .env.docker -f compose.local.yml
  -f infrastructure/compose/queue.local.yml --profile gpu run --rm -T --no-deps
  worker-gpu python -m scripts.check_gpu_runtime` passed actual CUDA kernels.
- Real GPU worker HTTP demo:202 → queued/running/finished, one attempt, report/PDF200,
  repeated request same logical job ID. Ephemeral RSA fixture, not a real IdP.
- Full pytest unit/security/API/integration/worker suite: **260 passed,0 failed,
  0 skipped in42.57s**. Four added startup rejection cases passed.
- Ruff/format: pass,122 Python files; strict mypy:63 source files; dependency,
  compile and hardcoded-key checks pass. Known deprecation/config warnings remain.
- CPU image ID compared with pre-fix ID: unchanged. Primary report preservation
  and live process/dependency receipts are recorded with correction evidence.

Raw commands/results: `evidence/gpu-correction-20261026T150543Z/`.

### J. Performance and ML Metrics
Cached tiny Whisper, explicit cuda/float16,10-second clip, one English segment:
load0.97705s; actual transcription0.71097s. Whole-GPU sampled maximum267MiB during
that short probe, including background/display use; not an isolated or guaranteed
peak and not a large-model memory budget. Real full bundled-sample GPU job:
queue wait746.771ms, measured worker execution7644.977ms, upload0.45204s, overall
client verification9.39050s, one attempt. These are single functional samples,
not a controlled CPU speedup, production throughput or accuracy measurement.
No WER/DER/F1, training improvement or model promotion is claimed.

### K. Security Analysis
Only the GPU image gained NVIDIA runtime packages. TLS checks were not disabled;
root installs happen at image build, runtime stays appuser/read-only with owned
tmpfs and one reserved NVIDIA device. Missing runtime fails before consuming jobs.
No CPU fallback, secret publication, public deployment or production fixture user.
Existing tenant/owner controls, private object storage and deduplication tests pass.

### L. Concepts Explained
The driver exposes a GPU; user-space libraries implement operations requested by
CTranslate2. Reporting a CUDA-capable device does not install cuBLAS/cuDNN. A lazy
transcription iterator must be consumed to run the encoder/decoder. A separate
image supplies those libraries without imposing their size on CPU-only services.
Linux ldconfig lets the dynamic loader locate the wheel-installed shared libraries.

### M. Questions and Answers
1. **Why did nvidia-smi succeed while Whisper failed?** It proved driver/hardware
   visibility, while transcription needed missing user-space runtime libraries.
2. **Why did model construction pass?** Encoder execution was deferred; consuming
   actual transcription results is necessary to test kernels and all dependencies.
3. **Why a separate image?** CPU services need no CUDA libraries; their image ID
   remains unchanged and they can continue running independently.
4. **Why install NVRTC?** The selected cuBLAS release declares it as a dependency;
   all three GPU packages are pinned and installed only in the Linux GPU layer.
5. **Why ldconfig?** Wheel libraries live outside standard loader directories;
   registration makes SONAME lookup work without editing Windows PATH or assuming
   a particular Python minor-version directory.
6. **Why add startup checks?** Wrong images should reject GPU startup before
   accepted jobs waste attempts on a deterministic missing-library failure.
7. **Could the green result be CPU fallback?** The probe checks actual model device
   cuda and compute type float16; the GPU worker explicitly sets cuda, and no
   missing-device fallback is permitted.
8. **Do the unit tests prove GPU execution?** No. They test rejection paths; separate
   Docker transcription and durable GPU-job runs establish actual hardware execution.
9. **Does267MiB prove every model fits8GB?** No. It is a sampled whole-device maximum
   for a short tiny-model probe. Other models, concurrency and training need their
   own memory/load evidence.
10. **Were models or the host driver changed?** No. Existing cached tiny weights,
    driver610.88 and host CPU environment remain; the change supplies container
    runtime libraries and preserves current inference/authorization contracts.

### N. Remaining Problems
Real IdP/production ingress and rate limits, other GPU models/training and sustained
GPU load remain unverified. Object retention/GC and inherited private provider logs
remain prior STEP10 limitations. Single-sample timings do not establish capacity
or accuracy. No new model or next implementation step was executed.

### O. Final Quality Verdict
**GPU runtime defect: PASS — corrected and validated on the actual RTX4060.**
**STEP10 overall: PASS WITH LIMITATIONS** for the remaining documented deployment,
identity, retention and model/load scope. CPU and GPU workers remain available.


# Failure Analysis and Correction Report — Queue Revalidation

Audit date: 2026-10-26. Scope: the current STEP_10 implementation and its runtime;
no STEP_11 implementation, migration, model training, commit or push was performed.
Prior implementation and GPU correction sections above are historical records.
Evidence: `evidence/step10-correction-20261026T154515Z/` (relative to this report).

## A. Executive Summary

**PASS WITH LIMITATIONS.** Four confirmed failure groups were reproduced and fixed.
All 275 tests pass in 46.68s with no skipped tests. A real queued Docker GPU job
finished, produced readable report/PDF, preserved idempotency and included corrected
attempt metrics. Runtime source hashes match reviewed host source. Existing primary
report counts remain intact. Remaining limits are deployment/identity/load scope
and a registry certificate failure affecting a clean rebuild.

## B. Failure Inventory

| ID | Severity | Confirmed failure | Resolution/evidence |
| --- | --- | --- | --- |
| S10-R01 | P1 | Valid compact/uppercase tenant IDs strand work without an attempt | Canonical UUID allowlist; unit + real PG/S3 and GPU validation |
| S10-R02 | P2 | Invalid numeric settings reach runtime arithmetic/admission | Strict integer counters and finite bounded intervals |
| S10-R03 | P2 | Successful completion drops attempt/retry metrics | Persist counters on claim and merge completion metrics |
| S10-R04 | P2 | CRLF password makes Redis health probe falsely fail | Trim trailing whitespace; real before/after probe and healthy Redis |

`failure-inventory.json` maps each cause to reproduction, correction and execution
artifacts. Four identified, four corrected, zero unresolved confirmed code defects.
These are root-cause groups, not a count of individual failed assertions.

## C. Root Cause and Reproduction

R01: UUID construction validated identity but retained the original spelling.
JobRunner normalized incoming UUIDs, then compared unequal strings. New regression
work remained queued before the fix despite a logically authorized tenant.

R02: positivity alone accepts NaN/infinity, fractions and booleans in Python's numeric
hierarchy. Unbounded republish values raised actual timedelta ValueError/OverflowError
in `red-interval-consequences.json`. Retry delays were already capped by runtime;
the correction also makes their input domain explicit. No historical outage or
backoff overflow is invented. Capacity and attempt budgets now have integer semantics.

R03: replacing the whole metrics dictionary at success discarded persisted retry
history. First-success and retry-then-success regressions expose both paths.

R04: the Windows-created secret contains CRLF. Redis accepts its password line,
while shell command substitution removed LF but retained CR in REDISCLI_AUTH.
Authenticated application ping succeeded; the original probe failed WRONGPASS.
The unchanged secret with corrected probe succeeds. No credential was exposed or
rotated, and the AOF volume was retained.

## D. Code Changes and Important Components

`QueueSettings.__post_init__` checks counters as ints excluding bool, bounds
capacity to 1–10000 and attempts to 1–5. Intervals accept int/float excluding bool:
retry base (0,300] and republish (0,86400] seconds. Chained comparisons reject NaN,
infinity and huge integers without unsafe float conversion. UUIDs are converted to
canonical strings and deduplicated using insertion-ordered dict keys. The frozen
dataclass is initialized with object.__setattr__; callers cannot mutate it afterward.
`from_env` continues loading private JSON with the same default settings.

JobRunner persists attempts/retries when claiming work. Its existing commit hook
merges metrics at successful atomic report completion and uses one measured elapsed
value for execution_ms and last_attempt_ms. Queue wait remains the original wait;
these durations describe the final successful attempt, not cumulative billing time.
Existing deterministic IDs, tenant checks, advisory locks and cancellation guards
are unchanged. No historical row is backfilled with inferred metrics.

The Compose Redis health command trims trailing whitespace before authenticating.
Dockerfile.gpu explicitly copies settings and runner alongside its existing runtime
and probe overlay, ensuring a verified local GPU base can receive current source.
No image TLS validation is disabled.

## E. Imports and Dependencies

No runtime dependency, model checkpoint or package version was added by this audit.
Settings uses existing UUID for identity parsing, dataclasses for immutable config,
json/pathlib/os for private file loading; runner retains its existing persistence
and timing imports. Its local int|float annotation resolves an intermediate mypy
loop-variable inference error. That failed check is retained separately, followed
by a passing final mypy receipt. New tests use pytest parametrization, existing
worker fixtures, dataclasses.replace, and time for a real scheduled retry.
GPU library pins from the earlier correction remain unchanged.

## F. Files Created or Modified

- `services/workers/settings.py`: canonical identity and validated numeric domains.
- `services/workers/runner.py`: retained claim/completion metrics.
- `tests/unit/test_queue_configuration.py`: 12 configuration regression cases.
- `tests/workers/test_queue_revalidation.py`: 3 real PG/S3 runner cases.
- `infrastructure/compose/queue.local.yml`: Windows-safe Redis health authentication.
- `Dockerfile.gpu`: explicit current settings/runner source overlay.
- `docs/development/background-jobs.md`: accepted values, metrics and build limitations.
- This report and `docs/implementation/PROGRESS.md`: current validation and status.
- New evidence directory: commands/results, source snapshots/diffs, failure inventory,
  operational receipt and integrity manifests. Ignored local helpers are operational
  tools rather than shipped application modules; private configuration is excluded.

Git's working tree also contains earlier STEP01–10 changes. `git-status.txt`,
`git-diff-stat.txt` and `git-diff-names.txt` capture that broader state; they do not
attribute it all to this audit. New untracked files do not appear in git diff --stat.
The two audit-specific unified diffs compare saved pre-audit source with final code.

## G. Original Repository Comparison

Upstream baseline remains fed4b610742c1337147281fcec8f2cdcc0a79be5 in the preserved
STEP02 clone; local HEAD remains a37e4634af1d2947fc3c548d54e62bda0b0daf89.
Upstream uses the original synchronous workflow and has no equivalent durable
worker settings/runner. These fixes harden the added queue layer. The original
Gradio interface, shared analysis graph and synchronous compatibility API remain.
No upstream model behavior or historical report data was intentionally changed.

## H. Architecture, Reliability and Performance

PG remains the authoritative job ledger/outbox and atomic result transaction.
Redis carries IDs; S3 stores private bounded audio; CPU/GPU workers share application
logic with separate queues. Canonicalization affects startup only, with linear
allowlist cost; validation rejects malformed operator input before dispatch. Metrics
merge is bounded by the existing small metrics map and adds no service or query.
No throughput improvement is claimed. A restart recreated only project services
with preserved volumes. A stopped audit GPU container was removed after its private
logs were retained; unrelated Ollama remained untouched.

## I. Test Execution and Packaging Results

- Pre-fix focused regression: **15 failed in 1.64s** (`red.json`).
- Corrected same cases: **15 passed in 1.03s** (`green.json`).
- Final regression: **275 passed in 46.68s**, zero skipped/failed (`tests.json/xml`).
- Ruff passes; format checks 124 files; strict mypy passes 63 source files.
- Dependency consistency, compilation and hardcoded-key checks pass.
- Real Redis probe old exit1 / corrected exit0; final health healthy.
- Final CPU/GPU worker source hashes equal host; CUDA startup validation passes.
- Gradio config200; API health200; ready/protected503 as expected without an IdP.
- Primary rows unchanged: call_records4, calls4, segments124, audit_log4,
  transcription_cache1, external_identities0, analysis_jobs0.

A Starlette/AnyIO deprecation warning and pytest asyncio configuration warning
remain nonfailing dependency/tooling warnings. An intermediate mypy annotation error
was corrected and is preserved in its own receipt.

Initial corrected CPU/GPU image builds succeeded (GPU build332.81s). A subsequent
build exceeded its orchestration deadline; final fresh base rebuild then failed
registry certificate validation at ghcr uv metadata. These are recorded packaging
limitations, not concealed green builds. Verified local CPU/GPU dependency images
were tagged and rebuilt with source-only overlays, with no network/package changes;
that path succeeded, services were recreated, and final hashes were checked.
Fresh registry-backed rebuild must be retried when certificate routing is repaired.

## J. Actual Model Evidence, Analytics and Metrics

`gpu-worker-http.json`: isolated test tenant using a compact uppercase allowlist,
ephemeral signed RSA identity, actual cached tiny Whisper/float16 Docker GPU worker
and configured hosted provider. Upload202 took0.555s; states queued/running/finished;
attempt1; attempts1.0/retries0.0; execution_ms and last_attempt_ms both25260.301084;
queue_wait_ms2085.677; report/PDF200; repeated key returned the same job.
Total observed request-to-verified-result time28.494s. No transcript/provider logs
are published. This single run proves execution and contract behavior, not WER,
accuracy, comparative speed, sustained capacity or a model-quality improvement.
Prior faster timings remain historical measurements of different runs.

## K. Security and Data Preservation

Full security/API tests exercise tenant/owner isolation, signature validation,
disabled users, bounded uploads, safe errors, idempotency and object integrity.
Canonicalizing UUID syntax preserves identity rather than granting access. Live
external authentication remains fail-closed because no real IdP is configured;
fixture signatures do not validate a production issuer. Runtime S3 permissions,
loopback-only ports, private files and GPU startup rejection remain in force.
No full new vulnerability scan or production penetration-test claim is made.
Report/primary counts and prior evidence hashes are checked, and private provider
logs remain excluded. No volume deletion, Redis flush, migration or history rewrite
was used. Evidence secret scanning is included in final hook receipts. The initial scan
flagged two source SHA256 checksums as high-entropy secrets. Their origin was
verified against source; checksums are encoded as byte arrays to avoid ambiguous
high-entropy text. No credential detection rule was disabled.

## L. Concepts Explained from First Principles

A UUID is a value; case and separator spelling do not define a different identity.
Canonicalization gives all equivalent spellings one comparison representation.
Python bool subclasses int, so positive-number checks alone cannot express an
integer job budget. NaN is unordered, making simple lower-bound checks insufficient;
a finite bounded interval rejects it before date arithmetic.
A persisted metrics map is part of the job record; replacement discards keys while
merging preserves measurements from earlier transitions. CRLF is two bytes: a
line reader can consume LF and leave CR in a secret. Health checks must use the
same credential interpretation as the service. A cached verified image can receive
reviewed source without reinstalling dependencies, but does not prove a fresh
registry build works.

## M. Technical Questions and Detailed Answers

1. **Why did a valid tenant stall?** Validation parsed UUID syntax but stored the
   caller's spelling. The runner compared its canonical spelling against it, so no
   allowed match existed. Canonical storage now makes those values equal.
2. **Does normalization weaken RLS?** No. It maps representations of the same UUID;
   configured membership and database tenant/owner restrictions still apply.
3. **Why reject bool budgets?** True behaves numerically as1 but is not an intentional
   capacity/attempt count. Explicit integer-domain validation catches operator errors.
4. **Why bound republish delay?** Unbounded values cannot be represented reliably
   in datetime arithmetic. Startup rejection prevents a dispatcher failure after work
   has been accepted. Defaults and ordinary configuration remain valid.
5. **Why preserve metrics at claim and finish?** A persisted running attempt should
   expose its current counters, and successful completion must retain those keys
   alongside the measured final duration. Retried success is tested separately.
6. **Are these exactly-once computations?** No. Recovery may repeat inference before
   commit. Locks and the existing atomic deterministic result transaction enforce one
   committed logical result, without claiming once-only provider billing.
7. **Why was Redis usable but unhealthy?** Clients used the correct password while
   the shell probe added CR from a Windows secret. Before/after commands against
   the same running service distinguish probe failure from broker failure.
8. **Did tests replace real model proof?** No. Controlled runner graphs test state
   transitions; a separate real GPU/hosted-provider sample proves actual inference
   and report access. Neither run establishes transcription accuracy.
9. **Why keep API readiness503?** No real issuer/audience/JWKS configuration exists.
   Returning success would hide an unavailable security prerequisite. Synthetic test
   identities are limited to isolated validation.
10. **Why is the build marked limited despite running containers?** Registry TLS
    blocked the final clean base rebuild. Reviewed local dependency images plus
    source overlays run current code, proven by hashes and CUDA checks, while clean
    network reproducibility remains an explicitly separate outstanding validation.
11. **Were historical metrics repaired?** No. Missing values cannot be reconstructed
    truthfully. Existing top-level attempts stays authoritative for old jobs; only
    future transitions receive newly retained metrics.
12. **Is STEP11 implemented?** No. STEP10's code and regression gates pass, making
    STEP11 eligible for a separate requested execution, with deployment limitations
    carried forward rather than silently declared solved.

## N. Remaining Limitations and Next Dependencies

Real OIDC integration, production ingress/TLS/rate limits, object retention/orphan
cleanup, inherited private content logs, other models/training and sustained load
remain unvalidated or pending as previously documented. Registry certificate
routing must be repaired and a fresh base build rerun. No certificate bypass was
introduced. Historical missing metrics are not backfilled. These do not invalidate
the reproduced correction results, but prevent production-readiness certification.
No frontend changed, so Commercially screenshot comparison is not applicable here.
STEP11 may build on the validated durable queue and preserved API/database contracts;
it must review its own prerequisites and carry forward real identity limitations.

## O. Final Quality Verdict

**STEP_10 — PASS WITH LIMITATIONS.** Four confirmed failure groups corrected and
validated, zero unresolved confirmed code defects. Actual GPU execution, isolated
service tests and preserved primary data are evidenced. Deployment/model/load
limitations above remain explicit. STEP_11 eligible, not started. No commit or push.


## Follow-on STEP_11 contract update — 2026-10-27

The completed STEP11 local-model adapter adds backward-compatible model_runs to
report JSON and authorized API reports; old records default to an empty list.
Its current OpenAPI snapshot, scoped PostgreSQL/HTTP test, 293-test regression and
actual Docker local-Qwen job are documented in
[STEP11](STEP_11_integrate_qwen_through_a_safe_model_provider_adapter_REPORT.md).
The measurements and source snapshots above remain historical evidence. Identity,
queue semantics and preserved primary records retain their prior guarantees.
