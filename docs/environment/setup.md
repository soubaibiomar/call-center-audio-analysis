# Project 28 local setup

For the now-running Docker app, PostgreSQL service and verified local models, see
[local Docker operation](docker-local.md). PostgreSQL is ready, while the original
Gradio application continues using SQLite until its planned migration.

The working checkout is now in the user-requested Documents folder. Git history,
prior uncommitted work and the private `.env` moved with it. The unchanged clean
STEP_02 upstream clone remains in the original Projects folder; it is not assumed
to be a sibling of this checkout. Earlier reports describe their original paths.

## Interpreter and reproducible installation

Use uv-managed Python 3.12, PowerShell and the existing `.venv`. Direct project/dev
pins come from `pyproject.toml`; the observed Windows transitive snapshot is
`PROJECT28_REQUIREMENTS.lock.txt`. That snapshot is not a hash-verified universal
uv lockfile. No `uv.lock` is claimed. `uv sync --locked` is inappropriate until a
reviewed uv lock exists; do not silently resolve newer transitive packages.

For a deliberately created new environment, select the supported Python version,
then install the snapshot. Never clear an existing environment or overwrite `.env`.

```powershell
uv venv --python 3.12 --relocatable .venv
uv pip install --python .venv/Scripts/python.exe -r PROJECT28_REQUIREMENTS.lock.txt
.venv/Scripts/python.exe scripts/check_project_setup.py
uv pip check --python .venv/Scripts/python.exe
```

Relocation reused the same installed uv-managed Python 3.12.15 with
`uv venv --allow-existing --relocatable --no-python-downloads --python <existing-base-python> .venv`,
then `uv pip install --offline --no-deps --reinstall --python .venv/Scripts/python.exe -r PROJECT28_REQUIREMENTS.lock.txt`.
All 127 package versions matched before/after; editable metadata/console launchers
now resolve the new location. This repair downloaded no packages or model weights.
Do not assume arbitrary venv copies are portable just because their interpreter runs.

## Private configuration and readiness

`check_project_setup.py` preserves existing `.env` bytes. Only if absent does it
exclusively create it from `.env.project28.example`, so a concurrent creator is
not overwritten. The template leaves credentials empty and tracing/analytics off.
Keep real values private; do not put them in reports, tool arguments or chat.
An environment variable overrides the corresponding dotenv value, matching dotenv's
normal no-override behavior. Diagnostics emit statuses, never values. Configured
means non-placeholder presence, not provider authentication or billing validation.

Original supported providers: `openai`/`OPENAI_API_KEY`, `gemini`/`GOOGLE_API_KEY`,
`groq`/`GROQ_API_KEY`. Set a matching `LLM_PROVIDER`. Existing Ollama is preserved;
upstream does not implement an Ollama adapter, so selecting it is not a working
local-provider fallback. Tracing credentials are optional and raw-data tracing
should remain off for sensitive calls. A SQLite key setting alone does not prove
encryption. Existing `.env` is not altered to enable any of these features.

STEP_06 subsequently configured Groq using a user-supplied credential privately.
Provider-specific model settings such as `GROQ_MODEL` override the historical
factory default; an explicit `get_llm(model=...)` argument takes precedence.
The real provider returned `model_not_found` for the historical Groq default;
the authenticated model listing and a successful synthetic request verified
`openai/gpt-oss-20b` for this account. Availability is account/time dependent.

STEP_06 also pins PyAV to 18.1.0 because faster-whisper 1.2.1 calls an argument
removed by PyAV 19. This is a measured compatibility correction, not a general
dependency upgrade. The direct/dev pin count is now 22; historical STEP_04 counts
describe the installation at that earlier capture. No model weights were downloaded.

## Hooks and validation

```powershell
.venv/Scripts/python.exe -m pre_commit install
.venv/Scripts/python.exe -m pre_commit validate-config
.venv/Scripts/python.exe -m pre_commit run --all-files
.venv/Scripts/python.exe -m pytest tests/ -q --tb=short
```

Installation creates the local Git hook, not a commit or push. Remote hook
environments may need small dependency downloads on first execution. The local
source-key guard uses portable Python in place of Bash/grep, preserves the original
`sk-`-followed-by-alphanumeric rule, reports only path/line, and fails closed on
missing/unreadable source. detect-secrets remains a separate configured check.
`--all-files` covers tracked files; untracked new code also receives explicit
local validation and is included once deliberately staged/committed. No security
baseline is automatically generated to hide findings. Full project typing and
host FFmpeg remain known limitations unless separately corrected and validated.

## Model/data boundary

Setup diagnostics do not import `app.py`, load ASR/LLM checkpoints or access customer
audio. STEP_06 real analysis requires a usable configured provider and an explicitly
selected small/cached ASR model; no fake success or Ollama substitution is permitted.
Training and production inference remain separate later operations. The approved
Commercially UI reference is unchanged; no frontend is built by setup work.
