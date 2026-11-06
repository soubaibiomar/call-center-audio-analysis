# Version 1 API

This API wraps the same analysis service as Gradio. STEP10 adds durable queued
jobs alongside synchronous routes; see `docs/development/background-jobs.md`.
It adds no training, login page or identity provider. The existing local Gradio interface remains on
port 7861. This API must stay on loopback during development; Gradio is a trusted
local regression interface and does not acquire these API access controls.

## Run locally

Use the uv-managed environment. Apply `alembic upgrade head` with the private
migration-owner connection before starting either application. The API uses the
restricted PostgreSQL runtime account, never the migration owner.

```powershell
$env:DATABASE_URL_FILE = Join-Path (Get-Location) '.local/step08_app_host_url'
.venv/Scripts/python.exe -m uvicorn services.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

The factory reads environment variables explicitly. It does not automatically
load `.env` or instantiate Whisper/LangGraph. The analysis service loads existing
provider configuration only on the first authenticated analysis request.

With no OIDC configuration, `/health` returns 200, `/ready` and protected routes
return 503. This is the intended default for the current project: the user has no
identity provider. A public schema does not grant access to any call data.

## Configure externally verifiable identity

An operator must first supply a real provider's HTTPS `OIDC_ISSUER`, API-specific
`OIDC_AUDIENCE` and pinned HTTPS `OIDC_JWKS_URL`. Alternatively supply
`OIDC_PUBLIC_KEY_FILE` for an administrator-managed RSA public PEM; do not set both
key sources. There is no default issuer, test-token switch, shared API key, or
locally issued production credential. Obtain an API access token through that
provider's own sign-in flow; this application does not accept passwords.

Only RS256 with RSA keys of at least 2048 bits is accepted. Tokens require `iss`,
`aud`, `sub`, `iat`, `exp` and a signed UUID `tenant_id` claim (claim name can be
changed with `OIDC_TENANT_CLAIM`). Expiration, future issue time and `nbf` are
validated; token lifetime must be positive and at most 3600 seconds. Maximum token
size is 16 KiB. Do not use an ID token intended for another audience. The provider
must assign tenant claims from trusted membership, not user-editable profile data.
JWKS uses the configured URL, a three-second network timeout and 300-second cache;
token-supplied URLs are ignored. Pinned PEM rotation requires operator replacement
and process restart. Provider key/claim configuration must be validated before
opening access beyond loopback.

The operator provisions Tenant and User records using the database owner's normal
administration process, chooses `agent`, `supervisor` or `admin`, and explicitly
sets `enabled=true`. Link an existing user with the owner connection:

```powershell
.venv/Scripts/python.exe -m services.api.provision_identity --tenant-id <tenant-uuid> --user-id <user-uuid> --issuer <provider-issuer> --subject <provider-subject>
```

The command validates UUIDs, verifies tenant/user membership, links idempotently,
refuses silent reassignment and preserves enablement/role. Runtime has SELECT-only
access to identity mappings and users. No public provisioning endpoint exists.
The legacy service user stays disabled. Every request resolves the enabled user
and database role again; token role claims do not grant privileges.

## Routes and contracts

| Method | Route | Meaning |
|---|---|---|
| GET | `/health` | Process liveness, no models or database required |
| GET | `/ready` | Auth configured, database reachable and migration revision current |
| GET | `/openapi.json` | Generated public schema (not counted in OpenAPI paths) |
| GET | `/api/v1/me` | Enabled current tenant/user and database role |
| GET | `/api/v1/calls?limit=20&offset=0` | Stable paged calls, `items`, `total`, `limit`, `offset` |
| GET | `/api/v1/calls/{call_id}` | Call metadata |
| GET | `/api/v1/calls/{call_id}/transcript` | Original typed transcription contract |
| GET | `/api/v1/calls/{call_id}/qa` | Original typed five-dimension QA contract |
| GET | `/api/v1/calls/{call_id}/report` | Typed report without internal audio paths/trace ID |
| GET | `/api/v1/calls/{call_id}/report.pdf` | Authorized on-demand original PDF; markup escaped |
| GET | `/api/v1/dashboard` | Actual counts/average over the caller's authorized scope |
| GET | `/api/v1/jobs/{job_id}` | Owned durable job with legacy fallback; unmeasured progress null |
| POST | `/api/v1/jobs` | Durable upload with Idempotency-Key,202 job ID |
| POST | `/api/v1/jobs/{job_id}/cancel` | Cooperative owned-job cancellation |
| POST | `/api/v1/calls/analyze` | Multipart `audio`, optional `caller_id`/`department`, synchronous 201 |

All `/api/v1` requests require `Authorization: Bearer <access-token>`. Agents see
only their owned calls; supervisors/admins see their tenant. Other tenants, other
owners and missing records produce the same 404. Jobs authorize through their
associated call. Lists/dashboard use the same scope. PostgreSQL row policies
provide a second tenant boundary; request-local context carries tenant/owner
through graph caches, audit inserts and both normalized/legacy persistence.

Empty lists return `items: []`, `total: 0`; empty dashboard averages are null.
Clients should display a loading state during synchronous analysis and handle 429
with a retry action. Synchronous `/calls/analyze` returns201 on completion; durable
`/jobs` returns202 with a real ID and persisted states. Progress percentage is not
fabricated. Synchronous concurrency is one analysis per API process; the separate
CPU worker uses one inference thread. See the background-jobs operational guide.

Uploads are checked before multipart parsing for authentication and total body
size (50 MiB plus 64 KiB multipart allowance). A receive wrapper also limits
chunked uploads; actual audio is limited separately to 50 MiB. Metadata is bounded
to 255 characters. Temporary upload names are generated UUIDs; client filenames
are never used as server paths. Original audio validation/intake duration limits
remain in force. API execution skips legacy downloadable temp exports; successful
intake copies use that request-owned directory, which is cleaned after successful
or failed graph execution. A context-aware workspace is reset after invocation.
Legacy Gradio keeps its existing default temp location/retention behavior.
No durable audio object store is implemented here.

## Errors

All application errors have the following stable shape; request IDs are newly
generated, not trusted from incoming headers. Responses carry `Cache-Control:
no-store`. Do not render strings as HTML.

```json
{"error":{"code":"unauthenticated","message":"A valid bearer token is required","request_id":"00000000-0000-0000-0000-000000000000","retryable":false}}
```

| HTTP | Code | Client action |
|---|---|---|
| 400 | invalid_request | Correct malformed request framing/body |
| 401 | unauthenticated | Obtain valid provider token; Bearer challenge included |
| 403 | forbidden | Operator must enable/map an allowed user |
| 404 | not_found | Resource absent or outside authorized scope |
| 405 | method_not_allowed | Use documented HTTP method |
| 413 | upload_too_large | Reduce upload size |
| 415 | unsupported_audio | Upload supported WAV/MP3/FLAC/M4A content |
| 422 | invalid_input | Correct UUID, pagination, metadata or missing form field |
| 429 | analysis_busy | Retry; Retry-After: 1 |
| 500 | internal_error | Use request ID for investigation |
| 502 | analysis_failed | Analysis/provider failed; explicit retry may repeat work |
| 503 | unavailable | Configure/recover identity/database; Retry-After: 1 |

Validation errors never echo bodies/tokens/paths; provider/database exceptions
are not returned. Existing graph/provider logs can contain call content and must
remain private. Hosted inference, inherited tracing/PII behavior, lack of public
rate limiting and the trusted Gradio baseline mean this is not a production
security certification. Auth verifies application identity; it does not replace
consent, provider data agreements or deployment hardening. No wildcard CORS.

## Reproduce validation

```powershell
.venv/Scripts/python.exe scripts/export_api_schema.py
$env:PROJECT28_TEST_ADMIN_URL_FILE = Join-Path (Get-Location) '.local/step08_test_admin_url'
$env:PROJECT28_TEST_APP_URL_FILE = Join-Path (Get-Location) '.local/step08_test_app_url'
.venv/Scripts/python.exe -m pytest tests/api tests/integration/test_postgresql_persistence.py -q
```

Use an isolated, migrated PostgreSQL test database, never production data. Tests
generate ephemeral RSA keys in memory and synthetic users/tenants. Their issuer
is explicitly a fixture, not a configured real provider. Tests requiring private
database files skip when absent. CI provisions a disposable loopback PostgreSQL
service and runs the same tests; hosted CI has not been executed in this step.

Regenerate `docs/api/openapi.json` after route/schema changes. The snapshot test
compares generated JSON with the factory. Swagger/ReDoc pages are disabled; no
new frontend is implemented. The approved green/neutral ERP frontend can consume
the call/dashboard/QA contracts and truthful empty/error/progress states.


## STEP11 model receipts

Authorized report responses now include additive `model_runs` receipts for summary
and QA attempts: provider, model ID/configured version tag, prompt revision, schema,
attempt/retries, measured latency, validity, safe error code and fallback=none.
Existing reports return an empty list. No audio path, endpoint, secret, prompt or
raw provider error is added. See `../development/local-models.md`. The OpenAPI
snapshot is regenerated; existing authentication/tenant/owner rules still apply.
Model Lab can consume this contract in its later UI step. No Model Lab screen
or real OIDC provider is implemented in STEP11.
