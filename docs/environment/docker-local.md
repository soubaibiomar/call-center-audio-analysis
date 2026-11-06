# Local Docker operation

The operational setup starts the existing Gradio application and a separate
PostgreSQL service. **Gradio still persists to SQLite.** PostgreSQL migration
(STEP_08) and a production Ollama adapter (STEP_11) are not implemented here.
The application continues using the configured Groq provider.

## Running services

| Service | Local address | Storage |
|---|---|---|
| Docker Gradio | http://127.0.0.1:7861 | `project28_app_data`, SQLite `/app/data/calls.db` |
| PostgreSQL | `127.0.0.1:5433`, database/user `project28` | `project28_postgres_data` |
| Existing Ollama | http://127.0.0.1:11434 | Existing container and model volume preserved |

The earlier native Python app may separately remain on port7860; it does not use
the new Docker app's database volume. Host ports bind to loopback only.
The PostgreSQL bootstrap user owns this local database; production least-privilege
application roles and resource ownership belong to the planned migration/security work.

## Start or restart

From the project folder in PowerShell:

```powershell
.venv/Scripts/python.exe scripts/prepare_local_docker.py
docker compose --env-file .env.docker -f compose.local.yml up -d --build
docker compose --env-file .env.docker -f compose.local.yml ps
docker start ollama
docker exec ollama ollama list
```

The preparation helper creates `.local/postgres_password` and `.env.docker` only
if absent. It refuses a missing host Hugging Face cache and downloads no models.
Existing secrets/settings are not replaced. `.env` supplies runtime provider
configuration; `.env.docker` supplies Compose ports, cache location and optional
base-image override. Both and `.local/` are ignored by Git/build context.
Database password is loaded via a Compose secret file and is never printed.

The current `.env.docker` reuses the existing `project28-foundation:baseline`
image. A new checkout defaults to `python:3.12-slim`. Dockerfile installs pinned
requirements using uv0.12.23 and retains av18.1.0 compatibility. This is a local
development image, not a hash-locked production release. See
[uv Docker instructions](https://docs.astral.sh/uv/guides/integration/docker/) and
[official PostgreSQL image secret-file support](https://hub.docker.com/_/postgres).

Whisper uses the read-only host cache, mounted at
`/home/appuser/.cache/huggingface/hub`. Model-hub downloads, tracing and Gradio
analytics are disabled. App runs as a non-root user with read-only root filesystem,
writable temporary storage and a dedicated data volume. No GPU is assigned to
the Gradio container; its cached tiny ASR runs on CPU/int8.

## Check PostgreSQL and local models

```powershell
docker exec project28-postgres-1 pg_isready -U project28 -d project28
docker exec -it project28-postgres-1 psql -U project28 -d project28
docker exec ollama ollama list
docker exec ollama ollama ps
```

The app container can resolve/reach `postgres:5432` and reach Ollama at
`http://host.docker.internal:11434`. Reachability does not mean the application
has migrated to PostgreSQL or implemented an Ollama provider adapter.

## Stop only this project

```powershell
docker compose --env-file .env.docker -f compose.local.yml stop
```

This preserves data volumes. Do not remove volumes to restart the app. The Compose
project does not own Ollama or unrelated containers. No existing service was stopped
or reconfigured by this setup; the previously stopped Ollama container was started.

## Verified execution — 2026-10-24

Both project services healthy; Docker UI HTTP200. PostgreSQL17.11 authenticated
TCP transaction created a temporary table, inserted/queried a row and rolled back.
Container package compatibility passes (111 Linux distributions). Focused setup,
decoder, provider, export and integration checks: **19 passed in1.25s**. Ruff lint
and formatting pass (68 Python files); new preparation script mypy passes.
Inherited full-application mypy failure remains documented in STEP_06.

| Installed Ollama model | Size on disk | Real synthetic generation | Observed request time |
|---|---:|---|---:|
| qwen3.5:9b-q4_K_M | 6,550,825,550 bytes | `OK` | 41.891s |
| qwen2.5-coder:7b | 4,683,087,561 bytes | `OK` | 26.640s |
| llama3.1:8b | 4,920,753,328 bytes | `OK.` | 9.567s |

One short request per existing model, context1024, max32 output tokens,
temperature0, no thinking requested, unload after each request. Times include
loading and are not quality/throughput benchmarks. Largest sampled **whole-GPU**
usage6493MiB (~6.34GiB), sampled about once per second; not an isolated model-only
or guaranteed peak measurement. No model downloaded. Existing Ollama0.32.4;
no model remains loaded after checks. Synthetic prompts contain no user audio.

## Changes and evidence

- `compose.local.yml`: project-scoped services, health checks, volumes, secrets,
  loopback ports and explicit resource limits.
- `Dockerfile`: pinned uv installer, optional existing base image, repeatable
  non-root image construction from pinned requirements.
- `app.py`: honors GRADIO_SERVER_NAME/PORT while preserving prior defaults.
  This fixes the previous Docker loopback binding that prevented port publishing.
- `.gitignore`, `.dockerignore`: exclude local database secret/settings.
- `scripts/prepare_local_docker.py`, `tests/unit/test_docker_preparation.py`:
  exclusive creation, preservation and missing-cache checks; stdlib only.
- This document and operational progress note; no implementation step marked done.

Initial validation exposed a missing Callable annotation and an invalid
`uv pip check --system` diagnostic flag. Both corrected; the container check now
uses `uv --no-cache pip check --python /usr/local/bin/python`. Earlier failure logs
are retained rather than overwritten.

Evidence: [final summary](evidence/docker-local-20261024T200505Z/final-summary.json),
[corrected validation](evidence/docker-local-20261024T200505Z/correction-validation.json),
[initial validation](evidence/docker-local-20261024T200505Z/validation.json),
[model inventory](evidence/docker-local-20261024T200505Z/ollama-inventory.json),
[real model results](evidence/docker-local-20261024T200505Z/ollama-generation.json),
[container snapshot](evidence/docker-local-20261024T200505Z/containers.json),
[artifact hashes](evidence/docker-local-20261024T200505Z/seal.json).
Existing n8n container ID/state preserved; other stopped projects untouched.
No commit, push, migration, model pull, training or UI redesign occurred.
