# Durable background analysis

STEP_10 adds a separate, authenticated job submission path. Gradio and the original
`POST /api/v1/calls/analyze` remain synchronous compatibility interfaces. New
clients should upload to `POST /api/v1/jobs` and poll the returned job ID.

## Local setup

Use the uv environment and existing private provider configuration. No Conda,
training service, new model or public deployment is required.

```powershell
.venv/Scripts/python.exe scripts/prepare_queue_local.py
docker compose --env-file .env.docker -f compose.local.yml -f infrastructure/compose/queue.local.yml up -d redis object-store
.venv/Scripts/python.exe scripts/prepare_queue_local.py --bootstrap-storage
```

Apply `alembic upgrade head` using a **private migration-owner** URL/file. Never
run migrations as the restricted application account or downgrade populated data.
The new revision is `0003_jobs`; back up existing databases before applying it.
Then build/start the application services:

```powershell
docker compose --env-file .env.docker -f compose.local.yml -f infrastructure/compose/queue.local.yml build app
docker compose --env-file .env.docker -f compose.local.yml -f infrastructure/compose/queue.local.yml up -d app api worker-cpu
```

The preparation script creates missing private files exclusively and preserves
existing values. Bootstrap creates a private bucket and a separate runtime user
with only GetObject/PutObject under its `tenants/` prefix. Root storage credentials
are not mounted into API or worker containers. No anonymous object policy exists.
Redis requires its private password, uses AOF and refuses eviction on memory pressure.

Edit `.local/queue_config.json` privately to list authorized worker tenant UUIDs.
The default legacy tenant does not create or enable a user. New tenants require an
operator to update this allowlist and restart workers; there is no global RLS
bypass or hidden all-tenant discovery. `.local/queue_host.json` is the equivalent
configuration for native tests/API; it uses loopback host ports.

Local listeners: Gradio7861, API8000, PostgreSQL5433, Redis16379, S3API19100. All
published ports bind127.0.0.1. API `/health` is available; `/ready` and protected
routes remain503 until a real identity provider is configured as described in
`docs/api/README.md`. The user currently has no IdP. No production test-token switch
or local login is added. The S3 browser is disabled; this step builds no frontend.

The GPU service is opt-in with `--profile gpu`. It reserves one NVIDIA device and
uses its own `analysis_gpu` queue. It refuses startup when CUDA is unavailable;
the CPU worker cannot consume GPU jobs. The separate `Dockerfile.gpu` image now supplies pinned CUDA12/cuDNN9 libraries;
cached tiny Whisper/float16 and the complete GPU job path have passed on the RTX4060.
Build the base app first, then `--profile gpu build worker-gpu`. Reproduce the actual
kernel check with `--profile gpu run --rm -T --no-deps worker-gpu python -m
scripts.check_gpu_runtime`. See `docs/environment/GPU_VERIFICATION.md`. Other
models, training and sustained GPU load remain unverified. CPU inference is
explicitly selected for the default worker and its image stays unchanged.

## HTTP contract

`POST /api/v1/jobs` requires the existing external bearer identity plus:

- `Idempotency-Key`: 1–128 ASCII letters, digits, underscore, period, colon or hyphen.
- Multipart `audio`; optional `caller_id` and `department` (255 characters each).
- Multipart `queue`: `cpu` (default) or `gpu`.

202 returns a typed job with `id`, nullable `call_id`, status, attempts, timestamps,
sanitized error_code and numeric metrics. The full body has a configured size cap;
audio uses existing validation and a maximum50MiB. Client filenames are not paths.
`GET /api/v1/jobs/{id}` reads its persisted state. `POST .../{id}/cancel` returns202
with either terminal state or `cancelling` for an executing attempt. Agents can
read/cancel owned jobs; supervisors/admins remain tenant-scoped. Other resources
return404. No public audio URL or storage credential is returned.

States: queued → running → finished; failures may produce retrying → running;
exhaustion produces failed. Cancellation produces cancelled, or first cancelling
while inference unwinds. Cancellation does not immediately terminate ASR/hosted
requests, but the commit guard prevents committing their result after cancellation.
Terminal states are immutable. `progress` is null because no percentage is measured.

Identical key, owner, audio hash, queue and metadata return the same logical job,
including at capacity or after completion. A changed input with the same key gets409.
The admission cap counts all nonterminal jobs per tenant (default32); saturation
gets429 and Retry-After. Storage failures before acceptance get503; malformed
forms/UUIDs get422; unsupported audio gets415 and oversize uploads413. Existing
transport error envelopes and sanitized messages remain in force. New logical
work after a terminal failure needs a new key; it does not reset the old ledger.

## Delivery, retries and failure recovery

PostgreSQL is authoritative. Its row is also a transactional outbox: queued,
retrying, running and cancelling rows due for delivery are published periodically.
Redis outages or ambiguous publication acknowledgements leave recoverable DB rows.
Redis messages carry only tenant/job UUIDs, not audio, tokens or transcript content.

CPU/GPU Dramatiq actors are separate. Each worker uses one inference thread and
the same AnalysisService/LangGraph implementation as the original workflow.
Application attempts/backoff are persisted in PostgreSQL, not multiplied by a
second Dramatiq inference-retry budget. Default maximum3 attempts, maximum5 by
configuration; exponential delay `min(300, base * 2**(attempt-1))` seconds. Default
base5s, running-job redelivery interval15s. Multiple configured workers may publish
duplicates; PostgreSQL advisory locks prevent overlapping execution of one job.

Every job has a deterministic call UUID. Original intake uses it only inside
worker execution context. Report, canonical call/segments and job completion share
one transaction through an optional commit hook. A replay after commit is a no-op.
A crash before commit can repeat computation/hosted requests; this is **at-least-once
execution with one committed logical result**, not exactly-once inference or billing.
Original post-report audit remains outside that transaction and can need reconciliation.

Worker process death releases its execution lock. Redis redelivery/PG outbox can
resume the running job, consuming another persisted attempt. The worker rechecks
that the owner is enabled before starting and establishes tenant/user context
itself; API ContextVars do not travel through Redis. Each attempt owns a temporary
workspace. Docker tmpfs disappears on restart; a native process killed abruptly
may leave its private OS temp workspace for operator cleanup. Do not sweep other
workers' directories.

## Storage and operations

Object keys are server-generated `tenants/<UUID>/jobs/<UUID>/audio`. Upload uses
Content-MD5 plus stored SHA256/length metadata; the worker reads bounded bytes and
recomputes SHA256 against the trusted job row before analysis. MD5 is a transport
compatibility check; SHA256 is the persisted integrity check. Runtime credentials
cannot list/administer buckets. Local HTTP is confined to the development host/
project network; real remote deployment requires configured TLS, ingress policy,
rate limits, patched images and real provider validation.

Objects persist for replay and audit. Automatic object retention/garbage collection,
orphan cleanup after a failed DB commit and training consent workflows are not
implemented. Operators must apply a reviewed retention policy before production
customer uploads. Never infer training permission from analysis permission.
Existing private graph/provider logs may contain call content and remain a known
privacy limitation. Do not publish `.env`, `.local`, SQL URLs, root/runtime keys or
provider logs. No `docker compose down -v`, Redis flush, credential rotation or
history rewrite is part of setup/recovery.

## Validation

```powershell
$env:PROJECT28_TEST_ADMIN_URL_FILE = Join-Path (Get-Location) '.local/step08_test_admin_url'
$env:PROJECT28_TEST_APP_URL_FILE = Join-Path (Get-Location) '.local/step08_test_app_url'
.venv/Scripts/python.exe -m pytest tests/workers -q
```

Use a migrated **isolated test database**, private local S3/Redis config and
synthetic test identities. Tests skip when private collaborators are absent; those
skips are not a pass. The worker tests include real Redis/PG/S3, kill/restart,
overlapping delivery, lost publish acknowledgement, retry exhaustion, saturation,
cancellation, tampering and post-commit failure. Their synthetic graph is explicitly
not a neural benchmark. A separate bundled-sample Docker worker run validates the
real configured model/provider path. Hosted CI has not executed these local services.


## Queue configuration and metrics revalidation (2026-10-26)

Worker allowlist UUIDs are canonicalized and deduplicated before comparison.
Uppercase and compact spellings identify the same tenant; this grants no new tenant
access. Invalid UUIDs reject configuration at startup. Capacity must be an integer
1–10000 and maximum attempts an integer 1–5; booleans and fractions are rejected.
Retry base must be finite in (0, 300] seconds and republish interval finite in
(0, 86400] seconds. NaN, infinity and out-of-range values fail before dispatch.
Defaults remain 32 / 3 / 5s / 15s respectively.

Claiming an attempt persists attempts and retries in the numeric metrics map.
Completion preserves these counters and prior queue wait; last_attempt_ms and
execution_ms describe the successful final attempt and use the same elapsed
measurement. They are not cumulative retry time. Historical completed rows are not
backfilled; their top-level attempts field remains authoritative.

Redis health authentication strips trailing whitespace from the mounted password
configuration line, including Windows CRLF. It preserves the configured credential
and Redis AOF volume. A failed health probe is distinct from failed client access;
both must be checked. Final deployed source hashes and real probe results are in
the STEP10 correction evidence directory. A registry certificate error blocked a
fresh final base rebuild; locally verified dependency images were reused with
source-only overlays. TLS verification was kept enabled. A clean network build
remains to be rerun after registry connectivity is repaired.
