# Step 01 — Verify Windows, Docker and GPU environment

> **Status: DONE — quality review: PASS WITH LIMITATIONS.** This is not a claim
> that every future application prerequisite is installed or all original checks pass.
>
> **Date:** 2026-10-24; reporting timezone Africa/Casablanca.  
> **Initial implementation capture (UTC):** `2026-10-24T15:48:42.7623433+00:00`.  
> **Quality-review capture (UTC):** `2026-10-24T16:02:20.7928747+00:00`.  
> **Owner/lead:** Both (AI/ML and Platform); execution by Codex.  
> **Branch:** `feature/project28-foundation`.  
> **Pinned upstream SHA:** `fed4b610742c1337147281fcec8f2cdcc0a79be5`.  
> **Working HEAD:** `a37e4634af1d2947fc3c548d54e62bda0b0daf89`, plus the uncommitted
> STEP_01 additions inventoried in the evidence. No new commit SHA is claimed.  
> **Environment:** Microsoft Windows 11 Home, build 26300, PowerShell
> 7.6.5, uv 0.12.23, project Python 3.12.15, RTX 4060 Laptop 8 GB.  
> **Prompt:** [STEP_01 prompt](../../prompts/STEP_01_verify_windows_docker_and_gpu_environment_PROMPT.md).  
> **Source template:** [report template](../../report_templates/STEP_01_verify_windows_docker_and_gpu_environment_REPORT.md).

> **Current correction record:** See the appended **Failure Analysis and Correction Report** (A–O).
> Earlier sections retain historical results; strict lint and formatting now pass.
> Full-project mypy remains unresolved.

## 1. Goal and plain-English explanation

The goal was to determine which workstation capabilities actually work before
adding models or infrastructure. A Windows GPU appearing in Device Manager does
not prove that a Linux container can access it, and a Python command on PATH does
not identify the Python used by the project virtual environment.

Implemented a repeatable PowerShell diagnostic collector and twelve failure-oriented
tests. Executed the collector, a cached container GPU probe, resource/port checks,
container continuity checks, the full original regression suite plus the new tests,
and static checks. Wrote a prerequisites/remediation matrix and updated the
45-step tracker. Imported the user's specification package unchanged so its master,
index, prompts, templates and design assets are available in this repository.
The imported future templates are explicitly not execution evidence.

No application, model, database, frontend, CI or dependency-manifest behavior was
changed. No packages, models or datasets were installed/downloaded; no training,
provider calls, public deployment, commit or push occurred. STEP_02 was not started.

## 2. Actual upstream vs your implementation

The comparison uses actual local source at the pinned upstream revision, not README
claims. Before this step, `docs/environment/`, `docs/implementation/` and the new
script/test did not exist. The earlier PROJECT28_BASELINE.md is retained as historical
preparation evidence rather than treated as completion of later steps.

| Feature/code path | Actual upstream implementation | STEP_01 result | Behavioral difference / compatibility |
|---|---|---|---|
| `app.py`, module startup and launch | Config -> SQLite -> eager Whisper -> LangGraph -> Gradio | Kept byte-for-byte relative to upstream | No new startup or download behavior |
| `src/agents/transcription.py::_detect_device` | Optional torch check, then CPU int8 fallback | Kept | Host/container driver visibility does not change selected inference device |
| `Dockerfile` | Python 3.12 slim, ffmpeg, non-root appuser; no GPU runtime provisioning | Kept | Separate ephemeral probe validates driver passthrough; image not rebuilt |
| `pyproject.toml` and `requirements.txt` | Python >=3.11; pinned original stack/dev extras | Kept | No new runtime or test dependencies |
| Environment verification entry point | No checked-in collector | `scripts/Test-Project28Environment.ps1` | New manual-only CLI; never imported by the application |
| Failure handling | No diagnostic contract | `Invoke-ToolCheck`, `Test-ServiceContinuity` | Missing/error/timeout and unavailable snapshots stay explicit |
| Prerequisites/evidence | General README/setup prose | `docs/environment/requirements.md`, evidence JSON | Measured resources, PATH and tool state, with redacted user-profile paths |
| Project specification | Not present upstream | 99 original specification assets and per-file SHA-256 manifest | Documentation only; no future feature claims |
| Progress tracking | No 45-step tracker | `docs/implementation/PROGRESS.md` | Only STEP_01 marked DONE |

`git diff --exit-code upstream/main -- app.py src/ requirements.txt pyproject.toml Dockerfile`
returned **0**. The Git evidence records `git diff --stat`, `git diff --name-status`,
`git diff upstream/main --stat`, and `git diff upstream/main --name-status`, plus
untracked additions. New files are intentionally unstaged, so plain `git diff`
does not list them. The SHA-256 change inventory enumerates their actual paths,
byte sizes and content identities; it does not invent a committed worktree SHA.

## 3. Files explained — created / modified / kept

| Paths | State | Purpose / interface / call sites | Verification |
|---|---|---|---|
| `scripts/Test-Project28Environment.ps1` | Created | Manual CLI: OutputPath, GpuImage, LibraryOnly; JSON diagnostic output | Real run, parser and twelve subprocess tests |
| `tests/unit/test_environment_diagnostics.py` | Created | pytest helpers and negative/continuity tests; no model/Docker invocation by tests | Full suite and focused rerun |
| `docs/environment/requirements.md` | Created | Human prerequisites matrix, resource interpretation and safe remediation | Values cross-checked with JSON |
| `docs/environment/evidence/step01-environment.json` | Created | Schema v1 tool records, resources, GPU and service fingerprints | Successful collector run, decoded/inspected |
| `docs/environment/evidence/step01-validation.json` | Created | Exact command arrays, stdout/stderr and exit codes | Real subprocess execution; failures retained |
| `docs/environment/evidence/prompt-package-provenance.json` | Created | SHA-256 identities for all 99 supplied spec files | Byte-equal copy verification |
| `docs/environment/evidence/step01-git-comparison.json` | Created | Raw Git comparison commands and results | Exit codes recorded; untracked status included |
| `docs/environment/evidence/step01-change-inventory.json` | Created | Complete new-file inventory with sizes/hashes, excluding itself | Generated from git's untracked-file list |
| `docs/environment/evidence/step01-documentation-checks.json` | Created | Section/Q&A/tracker/link/provenance checks | 13 sections, 8 answers, 99 exact specification copies |
| `docs/environment/evidence/step01-secret-scan.json` | Created | Secret-scan findings and explicit metadata review | Hash/identity findings classified; no credential finding |
| `docs/environment/evidence/step01-review-*.json`, `step01-quality-review.json` | Created by quality review | Failed reproductions, focused/final tests, fresh diagnostics and the ten-point decision | Actual code/metric validation |
| This STEP_01 report | Created | Completed matching template; evidence and handoff | 13 required sections and answered Q&A checked |
| `docs/implementation/PROGRESS.md` | Created | 45 rows from supplied manifest; one DONE, 44 NOT STARTED | Status count verified |
| `PROJECT28_MASTER_INSTRUCTIONS.md`, `STEP_INDEX.md`, `design/*`, `prompts/*`, `report_templates/*`, `resources/*` | Created; copied unchanged (99 files total) | Reproducible user-supplied specification; templates remain templates | Provenance manifest provides every exact path/hash |
| Existing application, tests, baseline, LICENSE, Dockerfile and manifests | Kept | Original public and persistence contracts | Source diff unchanged; original 113 tests remain passing |

No files were deleted. Full new paths appear in the change inventory rather than
burying code explanations under 99 static specification filenames.

## 4. Code explanation and algorithm

The new manual architecture is:

```text
PowerShell CLI -> typed tool checks -> bounded child processes -> sanitized records
               -> host/CIM/ports + Docker state + cached GPU probe
               -> before/after comparison -> evidence JSON -> report/requirements
pytest -> isolated PowerShell LibraryOnly functions -> real synthetic child processes
```

**Entry-point parameters and schema.** `OutputPath` selects the generated JSON;
`GpuImage` defaults to an already-cached CUDA base image; `LibraryOnly` exposes
functions for tests without running machine or Docker probes. PowerShell 7.2+ is
required for the .NET process, hashing and hexadecimal APIs. The tested runtime is
7.6.5, not Windows PowerShell 5.1. No new Python production classes or API routes exist. The additive capture/launcher
metadata fields preserve existing JSON consumers; no application module reads this
diagnostic schema.

**`Protect-UserPaths([string] Value) -> string`.** Replaces the known profile/home
root, case-insensitively, in native and slash-normalized forms. It is applied to
executable/argument metadata, PATH entries, captured output, errors and the saved
output-path message. It minimizes paths; it is not a general credential/PII classifier.
No credentials or environment-wide variable dump are collected.

**`Invoke-ToolCheck(Executable, Arguments, TimeoutSeconds) -> PSCustomObject`.**
The result explicitly holds `executable`, `arguments`, `path`, `status`, nullable
`exit_code`, `stdout`, `stderr`, `elapsed_ms` and nullable `output_capture_complete`. Command lookup is restricted to
Application executables; no shell alias/function can silently replace a binary.
The default state is MISSING and no process starts when lookup fails.

```powershell
$start.UseShellExecute = $false
$start.RedirectStandardOutput = $true
$start.RedirectStandardError = $true
foreach ($argument in $Arguments) { $start.ArgumentList.Add($argument) }
```

The first line avoids a command shell. The next two capture independent streams;
argument-list insertion preserves each value as a literal argument. Both streams
are read asynchronously before waiting, avoiding a full-pipe deadlock. A real
nonzero exit becomes FAILED and retains stderr. The same deadline now also covers
output draining: descendants can keep redirected handles open after the direct
child exits. `Task.WaitAll` uses the remaining budget; only completed streams are
read. Incomplete capture becomes TIMEOUT with a null exit code. A direct-child
timeout attempts to kill the owned tree and uses a bounded two-second cleanup wait.
A descendant already detached from an exited parent is not promised to be terminated;
the collector stops waiting and closes its streams instead of claiming success. Exceptions become
ERROR; `finally` stops the stopwatch and disposes the process object. A measured
command duration is diagnostic overhead, not application inference latency.

**`Get-ServiceSnapshot() -> diagnostic record`.** Obtains existing container IDs,
then selects only ID, name, image, state, started-at and restart count through a
Docker format string. It does not inspect container environment, logs, mounts or
model contents. Each record is SHA-256 hashed before being persisted to avoid
publishing unrelated project names. Aggregate container/running/Ollama counts are
retained. Snapshot errors remain errors; an empty successful inventory is valid.

**`Test-ServiceContinuity(Before, After) -> status/reason`.** Failing inputs return
UNVERIFIED. Otherwise sort and compare record fingerprints: equal sets yield PASS;
any identity/state/start/restart difference yields CHANGED. This detects a restart
even if a container is running in both snapshots. It is point-in-time evidence,
not a continuous availability audit or proof of causality for external activity.

**Tool collection and npm.** The collector checks each tool independently so a
missing ffmpeg does not hide a successful Docker/GPU result. `npm.cmd` is located,
then its JavaScript CLI is executed with Node directly; this avoids shell/batch
interpretation. A nonstandard npm installation may fail explicitly instead of being
silently repaired. The conventional layout on this workstation passed. Metadata now keeps `path`
as the executed Node binary and records the discovered npm shim as `launcher_path`
instead of overwriting the executable path.

**GPU probe lifecycle.** Inspect the image locally; if absent, record NOT_EXECUTED
and never pull. Generate a unique `project28-gpu-probe-<GUID>` name, run only
`nvidia-smi` with `--rm --pull=never --network=none --read-only --cap-drop=ALL
--security-opt=no-new-privileges --gpus all`, then clean up only that unique probe
if needed. No volumes are mounted. No existing container is stopped, removed or
reconfigured. A driver query uses no neural weights or training workload.

**Resource collection and serialization.** CIM fields supply Windows/RAM and fixed
disk bytes; KiB RAM values are multiplied by 1024. Listener rows retain ports/PIDs
and coarse address scope, not specific IP addresses. `ConvertTo-Json -Depth 10`
preserves nested records; UTF-8 output has no BOM. Complexity scales with the small
number of checks plus containers/listeners; model/audio size does not enter the path.
Resource-query exceptions are recorded, not converted into fabricated zero values.

**Python test helpers.** `ps_quote` escapes a PowerShell single-quoted literal;
`run_check` sources the script with LibraryOnly, executes a synthetic expression,
requires a bounded successful harness process with explicit UTF-8 decoding, and parses JSON into a typed
`dict[str, Any]`. Tests cover missing executables, exit 7/stderr, literal `&` and
spaces, a killed 30-second sleeper after a one-second timeout, profile redaction,
three successful/unavailable snapshot cases, a changed restart timestamp/count,
an exited-parent/inherited-pipe timeout, zero-container metadata and French/Arabic
Unicode output.
Tests are explicitly Windows-only and skip on unsupported hosts without pwsh;
there were **zero skipped tests on this workstation**.

## 5. Imports and dependency explanation

No runtime dependencies or `Import-Module` statements were introduced. PowerShell
built-ins/modules are supplied by Windows/PowerShell, not downloaded here.

| New import/API | Origin and version | Meaning, use and reason | Alternative / risk |
|---|---|---|---|
| `from __future__ import annotations` | Python 3.12 stdlib compiler feature | Deferred test annotations, consistent with repository style | Eager annotations would also work |
| `import json` | Python 3.12 stdlib | Decode real PowerShell records into assertions | Parsing display text would lose schema information |
| `import shutil` | Python 3.12 stdlib | `which` locates pwsh, allowing an explicit unsupported-host skip | Hard-coded host path would be brittle |
| `import subprocess` | Python 3.12 stdlib | Real child process tests with timeout/check/captured streams | Explicit UTF-8 decoding and no shell interpolation; avoids mock-only proof |
| `import sys` | Python 3.12 stdlib | Uses the current uv interpreter and identifies Windows | Host `python` could be a different version |
| `from pathlib import Path` | Python 3.12 stdlib | Resolve the repository script from the test file | String path concatenation is error-prone |
| `from typing import Any` | Python 3.12 stdlib | Describes heterogeneous decoded JSON values at the harness boundary | Not a claim of runtime schema validation |
| `import pytest` | Existing pytest 8.3.5 | Parametrized failure cases and platform skips | No Pester dependency/install introduced |
| `Get-Command`, filesystem/JSON cmdlets | PowerShell 7.6.5; Management 7.0.0.0 | Command lookup, directories, sorting/comparison and serialization | Windows PowerShell 5.1 is not supported by this script |
| `Get-CimInstance` | Windows CimCmdlets 7.0.0.0 | Query OS, RAM and fixed disks without changing them | Avoid external hardware inventory tools |
| `Get-NetTCPConnection` | Windows NetTCPIP 1.0.0.0 | Read listening endpoints | No bind attempts or process termination |
| .NET `Process`, `ProcessStartInfo`, `Stopwatch`, `Threading.Tasks.Task` | Bundled with PowerShell | No-shell processes, async capture, deadlines and elapsed time | Missing/failed tools stay explicit |
| .NET SHA256, Encoding, Convert, IO.File, Guid | Bundled with PowerShell | Stable private fingerprints, UTF-8 evidence and unique probe ownership | Hashes conceal names, not all machine metadata |

All imports added to executable Python code are in the test module. No training
library was imported or installed for this step. NVIDIA runtime registration is
observed, but its toolkit package version is **Not measured**.

## 6. Core concepts explained for a beginner

**PATH and command lookup.** PATH is an ordered list of executable directories.
`Get-Command ffmpeg -CommandType Application` searches that list. A missing result
means this shell cannot find the executable; it does not prove no copy exists
anywhere on disk. Sanitized PATH and exact resolved paths are retained in JSON.

**uv interpreter vs system interpreter.** A virtualenv is an isolated dependency
location tied to a particular Python. Here, host `python --version` says 3.14.6,
while `.venv/Scripts/python.exe --version` says 3.12.15. Invoking the latter keeps
original pinned dependencies on the already-tested baseline without Conda.

**Linux containers on Windows.** Docker Desktop runs a Linux backend that hosts
Linux process/container namespaces. The Windows CLI sends requests to that backend.
`docker info` reporting `linux` establishes container OS type; the Windows caption
remains Windows 11. A backend/driver restart is not an acceptable automatic repair
because other projects and Ollama could be using it.

**NVIDIA Container Toolkit.** The runtime bridges selected GPU devices/libraries
into a Linux container. A working host driver alone does not establish that bridge.
Our cached, network-disabled container returned the same GPU name, memory and
driver as the host, proving the driver query path while saying nothing about ASR
accuracy, PyTorch kernels, cuDNN or sufficient training VRAM.

**Example trace.** The synthetic test asks a Python child to write `probe failed`
to stderr and exit 7. The wrapper returns FAILED, exit_code 7 and the same stderr.
A missing executable instead returns MISSING with null exit_code because no process
existed. These are different failure mechanisms and require different remediation.

**Units and snapshots.** MiB/GiB use powers of 1024; decimal GB uses 1,000,000,000
bytes. Free memory and listeners are snapshots, not reservations. Checking that a
port is unused does not prevent another process claiming it later.

## 7. Data structures, ML evaluation, security and privacy

The only inputs were executable metadata, command outputs, Windows resource data,
Docker identity/state metadata and synthetic test subprocesses. JSON schema v1
retains status plus nullable exit codes rather than treating missing evidence as
zero. Git and specification SHA-256 identities provide provenance.

No audio/transcript/customer files, API keys, container environment variables,
private datasets or model volumes were read. Profile paths and specific listen IPs
are redacted; unrelated container names/images are fingerprinted before storage.
Hashes and ports/PIDs remain machine metadata, so evidence should still receive
normal repository review before future publication.

No model inference, learning, dataset split, MLflow experiment, promotion, or
training happened. Train/validation leakage, WER/CER and neural improvement are
**Not applicable / Not measured**, not zero. Existing sample audio was not used.
The driver probe requests GPU visibility without writable filesystem or networking;
it does not grant the application a new persistent permission.

## 8. Tests, exact outputs and verification

- [x] Each executable returned a real version or explicit MISSING status.
- [x] Host/container GPU and Docker diagnostics saved with profile paths minimized.
- [x] Existing service snapshots matched; no existing service action was issued.

See [quality-review validation](../environment/evidence/step01-review-validation.json)
for the current full suite and static checks;
[initial validation](../environment/evidence/step01-validation.json) retains the
original 122-test run. The original validation contains exact
command arrays, complete stdout/stderr and exit codes, and
[environment evidence](../environment/evidence/step01-environment.json) for every
version/resource/Docker command. Commands below run from repository root.

| Command / check | Exit | Actual result |
|---|---:|---|
| `pwsh -NoLogo -NoProfile -File scripts/Test-Project28Environment.ps1` | 0 | JSON collected; 8/10 tool entries PASS, 2 MISSING; Linux Docker and container GPU PASS |
| `.venv/Scripts/python.exe -m pytest tests/ -q --tb=short` | 0 | **125 passed in 17.54s**, 0 failed, 0 skipped (113 original + 12 diagnostics) |
| Focused `pytest tests/unit/test_environment_diagnostics.py -q --tb=short` | 0 | 12 passed in 7.26s after the deadline, empty-inventory and UTF-8 fixes; final full run above covers final source |
| `ruff check --extend-ignore UP038 src/ tests/ app.py` via project Python | 0 | All checks passed; same existing CI exception, not a new suppression |
| `ruff format --check tests/unit/test_environment_diagnostics.py` | 0 | 1 file already formatted |
| `mypy tests/unit/test_environment_diagnostics.py --follow-imports=skip --allow-untyped-decorators` | 0 | Success, 1 source file; isolates test harness annotations from third-party stubs |
| `python -m compileall -q app.py src/ tests/unit/test_environment_diagnostics.py` | 0 | Compiled without errors |
| PowerShell AST parser on the new `.ps1` | 0 | 0 parser errors; not a claim of PSScriptAnalyzer lint |
| `uv pip check --python .venv/Scripts/python.exe` | 0 | All 127 installed packages compatible |
| `docker run --rm --pull=never --network=none --read-only project28-foundation:baseline ffmpeg -version` | 0 | Container ffmpeg 7.1.5 available despite absent host executable |
| `ruff format --check src/ tests/ app.py` | **1** | Three existing files need formatting; 54 already formatted |
| `mypy src/` | **2** | Six errors in three files; third-party stubs/torch missing and NumPy Python-version syntax mismatch; check aborted |
| Tracked application/source diff against upstream | 0 | No production-source or manifest change |

The added-text secret scan ran successfully; it flagged 153 high-entropy
hex strings in generated metadata, not a clean zero-finding result. Each is a file
hash, Git revision, Docker identity or service fingerprint; all were reviewed as
non-secret and none silently suppressed. See
[secret-scan review](../environment/evidence/step01-secret-scan.json). The artifact
records the scan scope; later generated inventory hashes are metadata too.

The full formatter failures are unchanged `src/services/history.py`,
`src/services/pipeline.py`, and `tests/unit/test_history_service.py`. The full mypy
run is not marked passed: ReportLab/faster-whisper typing, optional torch and the
configured 3.11 target vs installed NumPy stubs remain unresolved. The focused
mypy command checks our harness only; it does not repair or replace that full gate.
The first focused lint attempt found one overlong added line; it was corrected and
rerun successfully. Initial focused mypy exposed the third-party traversal problem,
which is why the explicitly scoped command is reported alongside the full failure.
pytest also emits its existing unset asyncio fixture-loop-scope deprecation warning.

No fresh Gradio launch or live provider test was attempted: that is a later step.
Earlier UI-only smoke evidence in PROJECT28_BASELINE.md is historical, not claimed
as a fresh STEP_01 runtime measurement. Original model/LLM tests use mocks.

## 9. Analytics and quantitative report

The original measurement table below is historical, from the initial implementation
capture at 2026-10-24T15:48:42Z. The separate review capture is summarized below it.
No original metrics were overwritten or presented as fresh. No benchmark audio
or dataset was used. Prior baseline is used only where comparable evidence exists.

| Metric / definition | Sample / baseline | Actual observation | Interpretation |
|---|---|---|---|
| Tool availability = PASS / 10 selected entries | 10 entries, one invocation; Compose counted separately, code included | 8 PASS, 2 MISSING = 80% | Explicit missing status satisfies diagnostic gate; ffmpeg/code require native readiness follow-up |
| Diagnostic blockers = unmet STEP_01 acceptance gates | 3 specified gates | 0 | DONE is scoped to diagnostics |
| Future readiness gaps | 2 missing PATH tools plus 1 low-RAM policy warning | 3 | Not a complete audit of later model/service requirements |
| Free disk decimal GB = bytes / 1e9 | One fixed disk C:, one snapshot; previous free-space baseline Not measured | 358.31 GB (333.70 GiB) | Storage observed, not guaranteed allocation capacity |
| RAM GiB = bytes / 1024^3 | One Windows CIM snapshot; earlier baseline had no RAM measurement | 15.71 total / 1.58 available | Do not load models now; leave existing services intact |
| GPU total capacity | One GPU; earlier baseline 8,188 MiB | 8,188 MiB = 7.996 GiB | Same capacity; not available-memory guarantee |
| Observed used VRAM | Three observations: host before, container, host after | 165 / 165 / 165 MiB; max 165 MiB | Diagnostic snapshots only; inference/training peak **Not measured** |
| Container continuity | 52 fingerprints before and 52 after; one running | 0 differences; one Ollama container present | No identity/start/restart/state change observed |
| Listening endpoints | One snapshot; IPv4/IPv6 may repeat | 31 rows, 21 distinct ports | Planned project ports had no listener at capture time |
| Regression tests (initial implementation) | Previous baseline 113 tests | 122 passed; +9 initial diagnostic tests | Preserves original behavior, not proof of ML accuracy |
| ASR quality, latency p50/p95, training improvement | No workload/dataset | **Not measured** | Driver queries are not neural benchmarks |

**Fresh quality-review evidence:** capture `2026-10-24T16:02:20.7928747+00:00`; 8/10 tool
entries PASS, ffmpeg/code MISSING; available RAM **1.13 GiB**; free disk
**358.24 decimal GB**; used VRAM **366/366/366 MiB**
(host/container/host), maximum observed **366 MiB**, not inference peak.
All 52 existing service fingerprints matched, with one running container and one
existing Ollama container. These are diagnostic snapshots during verification,
not steady-state capacity or neural-performance benchmarks. Current suite: 125
passed, including the unchanged 113 original cases and 12 diagnostic cases.

RAM/disk/listener values can change immediately after capture. Three VRAM samples
are too few to estimate workload peak. No speedup, accuracy improvement, capacity
benchmark or causal performance claim is made.

## 10. Questions with answers

1. **Why test container GPU separately from host nvidia-smi?** The Windows driver
   can be healthy while Docker uses the wrong backend or lacks GPU passthrough.
   Here both queries succeeded and `nvidia` is registered. That proves the query
   path, not all CUDA libraries needed by a future model.
2. **Why use uv instead of Conda here?** The project already has an isolated uv
   Python 3.12.15 environment with compatible installed packages. It preserves the
   requested tooling and avoids introducing another environment manager or replacing
   the host's Python 3.14 installation. No environment reinstall was necessary.
3. **Why measure RAM, disk and VRAM before downloading weights?** Downloads consume
   disk, decompression/runtime consumes RAM, and GPU tensors consume VRAM. This
   workstation had only 1.58 GiB available RAM despite an 8 GB GPU, so
   loading models would introduce avoidable risk without proving step acceptance.
4. **How can the step be DONE with missing FFmpeg and code?** The specified gate
   requires real version output **or explicit missing status**, not installation of
   every tool. Both gaps are documented with safe follow-up. The existing container
   has working ffmpeg. No claim of full native or ML readiness is made.
5. **What fails and why not fix it now?** Repository-wide formatting and mypy remain
   failing in unchanged source/dependency typing. Environment diagnostics do not
   authorize unrelated formatting, torch installation or broad dependency upgrades.
   Their exact failures are retained for the later baseline-check step.
6. **How do we know Ollama was not disrupted?** The script never issues an action
   against an existing container. Before/after fingerprints include identity, state,
   start time and restart count for all 52 existing containers and match exactly.
   This is bounded evidence, not a promise about activity outside the collection window.
7. **Why use hashes for service records?** Equality/restart checks need stable
   identities but the report does not need unrelated project names. SHA-256 provides
   that comparison while minimizing incidental disclosure. The inputs are selected
   non-secret metadata; no environment variables or model files are hashed/read.
8. **What does a timeout mean compared with a missing tool?** Missing means lookup
   found no executable and no process existed; timeout means a child started but
   failed to finish before its limit. The test verifies the timeout is not success
   and the owned sleeper is terminated. Remediation differs: locate/install vs
   inspect a hung tool/backend, without resetting unrelated services.

## 11. Decisions, changes and risks

| Decision / risk | Evidence and rationale | Mitigation / owner |
|---|---|---|
| PowerShell 7.2+ manual collector | Available runtime 7.6.5; modern no-shell subprocess/hashing APIs | Platform: use pwsh, not Windows PowerShell 5.1 |
| Preserve original application | STEP_01 explicitly excludes redesign/model setup | Both: production diff remains empty |
| Keep full specification as passive assets | 99 supplied files copied byte-identically and hashed | Both: future templates stay NOT EXECUTED; tracker governs actual progress |
| Low available RAM — high operational risk | 1.58 GiB observed free | User/Platform: save work, choose what to close, rerun; no automatic termination |
| Native ffmpeg/code missing — readiness gaps | Explicit MISSING statuses | Platform: use container ffmpeg; locate trusted binaries or deliberate later install |
| GPU query is not inference — scientific risk | No weights/workload executed | ML: validate libraries/model-specific budgets at their proper step |
| Existing static failures — medium maintenance risk | Formatter exit 1, mypy exit 2 | Both: characterize in STEP_05; no silent waiver |
| Diagnostic metadata still operational information | Profile/IP redaction and service hashing minimize it | Both: review evidence before any later authorized push |

No package installation, global PATH edit, Docker reset, model download or service
restart was used as a workaround. No commit timestamps were changed. Existing
Git history and both copyright notices remain intact.

## 12. Actual deliverables, next handoff and evidence checklist

- [x] Changes executed and documented, with reusable checker and prerequisites matrix.
- [x] Original vs new paths/symbols grounded in actual source and Git evidence.
- [x] Functions, API types, imports and their failure behavior explained.
- [x] Real tests, numeric observations and known failed checks retained.
- [x] Eight technical questions answered, including failure/tradeoff explanations.
- [x] No secrets/customer audio/training assets added or read.
- [x] Only STEP_01 marked DONE in [PROGRESS.md](PROGRESS.md); remaining 44 NOT STARTED.

Artifacts: [requirements](../environment/requirements.md),
[diagnostics](../environment/evidence/step01-environment.json),
[validation](../environment/evidence/step01-validation.json),
[Git comparisons](../environment/evidence/step01-git-comparison.json),
[change inventory](../environment/evidence/step01-change-inventory.json),
[spec provenance](../environment/evidence/prompt-package-provenance.json),
[checker](../../scripts/Test-Project28Environment.ps1),
[tests](../../tests/unit/test_environment_diagnostics.py).

Next safe command, if refreshed resource evidence is desired:

```powershell
pwsh -NoLogo -NoProfile -File scripts/Test-Project28Environment.ps1
```

Review this report before authorizing STEP_02. Its dependency is this environment
assessment; existing clone work must be inspected and reused rather than overwritten.
No later prompt was executed. Any later commit/push or adjusted timestamp schedule
requires the corresponding user authorization and dates/timezone as previously agreed.

### STEP_01 quality review — 2026-10-24

**Decision: PASS WITH LIMITATIONS.** Specification gates pass; confirmed collector
and test-harness defects were corrected. Repository-wide static analysis and ML
readiness are not declared fully passing.

| Review item | Validation | Decision |
|---|---|---|
| Acceptance criteria | Ten tool entries have actual outputs or MISSING; Linux/runtime/GPU evidence saved; service fingerprints match | PASS |
| Existing functionality | Original app/manifests unchanged; 125 tests pass, including 4 original integration tests | PASS |
| Architecture/security/performance | Manual-only CLI, no shell, bounded capture, selected/hash-minimized metadata, no model downloads | PASS with detached-process limitation |
| Imports/dependencies | No new packages; UTF-8 uses existing subprocess; Task is bundled .NET | PASS |
| Unit/integration tests | 12 diagnostic tests plus 113 original tests; initial regression cases failed before corrections | PASS |
| Report vs source/Git | Current counts/schema explained; earlier metrics labeled historical; complete untracked inventory regenerated | PASS |
| Metrics | Original and review JSON kept separately; no ASR/training/peak-inference claims | PASS |
| Commercially-style UI | No UI code changed; approved reference/specification hashes unchanged | Not applicable |
| Limitations | Missing PATH tools, low RAM, original static failures and process-supervision boundary documented | PASS with limitations |
| Next dependency | Git, full non-shallow source history, expected remotes and step specifications available for STEP_02 inspection | Ready for non-destructive inspection only |

**Confirmed and corrected findings:**

1. **Medium:** After a direct child exited, inherited output handles could make
   capture exceed TimeoutSeconds and still return PASS. A real three-second child
   with a one-second budget reproduced it. The remaining deadline now bounds
   stream completion and reports TIMEOUT/incomplete capture. Cleanup waiting is
   bounded separately; this is not a general Windows process supervisor.
2. **Low:** Successful zero-container snapshots omitted all count fields. The
   boundary test reproduced a container_count KeyError; zero counts now remain in
   the successful schema without issuing an invalid empty inspect call.
3. **Low:** The Python test harness decoded PowerShell UTF-8 using Windows' default
   encoding. Synthetic French/Arabic output reproduced corruption. Explicit UTF-8
   fixes the capture boundary; this adds no claimed ASR/language functionality.
4. **Low:** npm evidence mixed `executable=node` with `path=npm.cmd`. The actual
   binary path is retained and the shim has its own launcher_path; the fresh live
   snapshot verifies both.

[Reproduction evidence](../environment/evidence/step01-review-reproduction.json)
retains **3 failed, 9 deselected in 4.93s** before the first three fixes.
[Focused post-fix evidence](../environment/evidence/step01-review-focused.json)
records **12 passed in 7.26s**. Final combined checks record **125 passed in
17.54s** and a clean final Ruff run. An intermediate added-test overlong line
was corrected; the failing lint attempt is retained, not erased. See the
[machine-readable ten-point review](../environment/evidence/step01-quality-review.json),
[fresh environment](../environment/evidence/step01-review-environment.json), and
[complete review validation](../environment/evidence/step01-review-validation.json).

**Remaining limitations:** host ffmpeg and code are absent from PATH; available RAM
was 1.13 GiB in the latest capture. The three original formatter differences and
six mypy errors still fail their full gates. Real inference, cuDNN/PyTorch kernels,
model capacity, provider credentials and neural accuracy remain unverified and
belong to later steps. PSScriptAnalyzer was not installed; AST parsing is not a
substitute for claiming that lint tool passed. A detached descendant whose parent
has exited is not forcibly terminated by the stream-deadline fix; only waiting is
bounded, and the collector runs trusted version/metadata commands.

**Next-step dependency:** STEP_02 can inspect and fingerprint the existing clone
without new model/runtime setup. Its current worktree contains intentional,
uncommitted STEP_01 additions: preserve them, distinguish original clean-clone
history from today's modified state, and do not overwrite or pretend it is clean.
No STEP_02 implementation/report was executed. No commit, push or timestamp edit
was performed during this review.

## 13. Approved ERP UI design / visual contract verification

**Status: Not applicable — environment-only implementation.** Read the supplied
UI design system and acceptance checklist; visually inspected the primary approved
[Commercially-style reference](../../design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png).
It overrides earlier green-ERP wording/assets. The secondary image is preserved
unchanged for provenance, not used to override the user's main reference.

| Check | Actual evidence / finding |
|---|---|
| Routes/components/files affected | None; only manual diagnostics, tests and documentation |
| Original Gradio vs upgraded interface | `src/ui/` and `app.py` unchanged; no new interface or routes |
| Neutral canvas, rounded white cards, green accents | Preserved as future acceptance criteria; no CSS/token changes in STEP_01 |
| Blue/pink rule | No theme colors introduced; reference business metrics never used as execution data |
| Typography, charts, loading/error states | No product UI/API data-contract changes; diagnostics expose truthful status/error fields only |
| Responsive 1440/1280/1024/390 layouts | Not applicable; no UI implementation |
| Accessibility: contrast, keyboard, focus, reduced motion | Not applicable; no UI implementation; future reference colors still require actual contrast testing |
| Application desktop/mobile screenshots | Not captured; approved reference is a specification, not an application screenshot |
| Automated UI visual/e2e checks | Not run; not relevant to environment step |
| Review decision/deviations | Correctly retains original Gradio; future ERP shell remains NOT STARTED |

**UI Reference Compliance:** this step is not UI-related. Matching elements and
intentional implementation differences: Not applicable. Color tokens used: none.
Screenshots: reference inspection only. Accessibility notes and remaining UI gaps:
all future frontend acceptance work remains in its numbered steps; no screen is
claimed compliant or implemented here.


# Failure Analysis and Correction Report

Correction review date: 2026-10-24, Africa/Casablanca. Fresh environment capture:
`2026-10-24T16:12:53.0848184+00:00`. This appendix is the current correction record.
Sections 1–13 above retain the original implementation/review chronology; their
statements that application/CI source was unchanged and formatting failed describe
the earlier snapshot and are superseded here. Failed logs have not been replaced.

## A. Executive Summary

**STEP_01: PASS WITH LIMITATIONS.** All three diagnostic acceptance criteria pass:
each tool has a real version or explicit missing status; sanitized GPU/Docker
evidence is saved; pre-existing service fingerprints match. Five failure groups
were reproduced, two corrected and three remain documented. This cycle fixed
formatting and strict lint, and restored both gates in CI. It did not implement
STEP_02 or later functionality. No commit, push or commit timestamp adjustment was
made. Historical baseline tests and prior review results remain separate evidence.

## B. Failure Inventory

The [structured inventory](../environment/failure-inventory.md) records F01–F05,
component, severity, reproduction, root cause and status. F01/F02 are corrected;
F03 full typing, F04 host FFmpeg and F05 editor launcher remain unresolved.
The [raw reproduction](../environment/evidence/step01-correction-reproduction.json)
preserves the original strict lint and formatter failures, the official mypy abort,
and the Python 3.12 diagnostic. The four earlier diagnostic/test fixes in section
12 are preserved as prior work rather than counted as new corrections.

## C. Root-Cause Analysis

F01 is deterministic formatting drift in three original files. F02 consists of
two builtin `isinstance` tuples that Ruff UP038 expects to use union syntax. The
previous workflow disabled formatting and ignored UP038, allowing these failures
to persist. Neither failure demonstrated a runtime defect.

F03 combines environment typing gaps with source typing debt. The configured
Python 3.11 analysis encounters a Python 3.12-only NumPy stub syntax, absent
ReportLab stubs, untyped faster-whisper and absent optional torch. A diagnostic
`--python-version 3.12` run gets past the syntax barrier but reports 79 errors in
18 files, including function annotations, SQLAlchemy types and structured-output
unions. Changing the target alone is therefore not a correction. No suppressions
or heavy optional runtime installs were used to manufacture a passing result.

F04/F05 are reproducible PATH lookup failures, not proof that every disk location
lacks these programs. Earlier safe lookup found no known native installation;
the existing baseline container provides a working FFmpeg alternative. The
diagnostic step requires recording these states, not silently provisioning tools.

## D. Code Corrections

`src/services/history.py` changes `isinstance(score, (int, float))` to
`isinstance(score, int | float)` and applies Ruff's layout. The guard still accepts
the same numeric builtin types and their subclasses. No score conversion or
weighting changes. `src/ui/tabs/history.py` changes only the event-index builtin
guard to `list | tuple`; no rendering, route, color or interaction is redesigned.

`src/services/pipeline.py` joins adjacent formatted string literals according to
Ruff; generated string content is unchanged. `tests/unit/test_history_service.py`
reflows conditional fixture dictionaries without changing test values or asserts.
The workflow removes `--ignore UP038` and enables an explicit `Ruff format` step.
These are complete small corrections to reproduced gates; no extra runtime tests
were added merely to mirror formatting. Existing regressions and the AST comparison
cover preservation. No new function, class, public API or schema was introduced.

## E. Import and Dependency Analysis

No imports, dependency manifests or lockfiles changed during this correction.
Union builtin type objects are supported by the project's Python >=3.11 baseline;
they require no third-party package. Ruff, pytest and mypy were already available
in the uv environment. The temporary equivalence validator used Python standard
library `ast`, `hashlib`, `json`, `subprocess` and `pathlib` to parse syntax, hash
bytes, save evidence and read Git versions. Existing PyYAML 6.0.3 parsed CI YAML;
it was not added to application requirements. No Conda environment was used.
The collector's .NET process APIs and the diagnostic test imports are explained
in the retained original implementation sections.

## F. File-by-File Changes

| Path | Correction and interface impact |
|---|---|
| `src/services/history.py` | Equivalent numeric guard; formatter layout; public functions unchanged |
| `src/services/pipeline.py` | Formatting of adjacent literals only; pipeline inputs/outputs unchanged |
| `src/ui/tabs/history.py` | Equivalent event-index guard; UI visual contract unchanged |
| `tests/unit/test_history_service.py` | Fixture formatting; assertions unchanged |
| `.github/workflows/ci.yml` | Strict lint and formatter enforced; existing job permissions unchanged |
| `docs/environment/failure-inventory.md` | Current structured triage and unresolved actions |
| `docs/environment/requirements.md` | Current follow-up; original measurement tables retained |
| `docs/implementation/PROGRESS.md` | Current result, still one step DONE |
| This report | Preserved history plus appended A–O correction evidence |
| `docs/environment/evidence/step01-correction-*.json` | Reproduction, validation, AST/CI comparison, fresh environment, decision summary |
| Existing derived evidence JSON | Refreshed Git comparison, documentation checks and change inventory |

The [change inventory](../environment/evidence/step01-change-inventory.json)
lists both modified tracked files and untracked additions with sizes and SHA-256.
It includes the pre-existing STEP_01 collector/tests and all 99 supplied package
files; those are not all newly authored by this correction cycle. No files deleted.

## G. Original vs Improved Repository

Comparison pins upstream `fed4b610742c1337147281fcec8f2cdcc0a79be5` and working
HEAD `a37e4634af1d2947fc3c548d54e62bda0b0daf89`. The original four Python files
are compared directly to upstream, not an invented baseline. Formatting leaves
their syntax trees unchanged after normalizing only the two supported builtin
tuple-to-union guards. File hashes and CI parse results are in
[equivalence evidence](../environment/evidence/step01-correction-equivalence.json).
Upstream lacked this environment collector/report package. The preparation commit
already added baseline configuration/documentation; its changes are distinguished
from this uncommitted correction by the
[Git comparison](../environment/evidence/step01-git-comparison.json).
MIT licensing and upstream history remain preserved. No published history changed.

## H. Architecture Impact

The existing Gradio → service → LangGraph/agent boundaries, SQLite persistence,
PII handling and scoring remain intact. The diagnostic collector remains an
external development tool with JSON output; it does not enter application startup.
The CI change moves style consistency into automated review. No FastAPI, React,
PostgreSQL, Redis or training architecture is claimed to exist because this step
does not implement those later designs. Production inference and training remain
separate future concerns. The UI file edit is a guard syntax equivalent; visual
impact is **Not applicable**. No app/browser screenshot was captured in this cycle.
The approved Commercially reference remains a future UI acceptance criterion.

## I. Tests and Validation

Commands below use `.venv/Scripts/python.exe -m` unless otherwise stated. Full
stdout/stderr, command arrays, exit codes and wall times are retained in
[validation evidence](../environment/evidence/step01-correction-validation.json).

| Check | Actual result |
|---|---|
| `pytest tests/ -q --tb=short` | Exit 0; 125 passed in 17.97 s; 0 failed, 0 skipped |
| `ruff check src/ tests/ app.py` | Exit 0; all checks pass with no UP038 exception |
| `ruff format --check src/ tests/ app.py` | Exit 0; 57 files already formatted |
| `mypy tests/unit/test_environment_diagnostics.py --follow-imports=skip --allow-untyped-decorators` | Exit 0; scoped check of 1 file only |
| `mypy src/` | Exit 2; 6 errors in 3 files; aborted further analysis, remains FAIL |
| `compileall -q app.py src/ tests/` | Exit 0 |
| `uv pip check --python .venv/Scripts/python.exe` | Exit 0; 127 installed packages compatible |
| `git diff --check` | Exit 0 |
| Four Python AST comparisons and workflow YAML parse | PASS; strict lint/format commands present |
| Fresh collector | Exit 0; GPU probe and continuity PASS; 8 tools PASS, 2 MISSING |

The 125-test suite includes original unit, integration and security coverage plus
12 environment diagnostics tests. Tests use synthetic/mocked boundaries and are
not a live credential-backed ASR/LLM integration benchmark. The pytest-asyncio
unset fixture-loop-scope deprecation warning persists in stderr; it is not hidden
or counted as a failed test. CI YAML and exact commands were validated locally;
GitHub's Python 3.11/3.12 matrix was not executed remotely. No check was bypassed
to declare full typing success. No new source change followed these validations.

## J. Performance and ML Metrics

One current full regression run: 125 passed / 125 collected = 100% test pass rate,
17.97 s pytest-reported duration (20.07 s process wall time). The original 113-test
baseline, initial 122-test step and prior 125-test review are different snapshots;
their durations do not establish a speed improvement. Formatter scope is 57 files,
not a model-quality sample. Tool availability is 8/10 = 80%; the two missing tools
are recorded rather than excluded from the denominator.

Fresh hardware/resource observations and exact timing are retained in
[environment evidence](../environment/evidence/step01-correction-environment.json).
The RTX 4060 Laptop reports 8,188 MiB total VRAM. This is capacity and diagnostic
observation, not peak model inference/training memory. All 52 pre-existing container
fingerprints matched. No audio dataset, ground-truth labels, training gradients,
model checkpoint or inference request was used. WER, CER, DER, emotion F1, model
latency, throughput and learning improvement: **Not measured**. No benchmark or
reference-image number is presented as a real model result.

## K. Security Analysis

Corrections add no imports, credentials, network endpoints or permissions. Existing
PII/redaction/security tests pass within the regression suite. The fresh GPU probe
uses a cached image, no network or mounts, read-only filesystem, dropped Linux
capabilities, no-new-privileges and a unique disposable name. It does not restart
existing Ollama or other containers. Service continuity is fingerprint evidence,
not a complete service-availability monitor. User-profile paths are redacted in
saved diagnostics; no customer audio or credentials were read for this step.

Prior entropy findings were reviewed as specification hashes and diagnostic/Git
identifiers; the report does not equate a nonzero entropy count with leaked secrets
or claim an exhaustive security audit. No new dependency vulnerability scan was run
in this correction cycle. The existing advisory dependency-audit job remains
advisory; strengthening it needs separate policy decisions and is not claimed here.
Detached descendants after parent exit remain outside full process supervision;
bounded output capture protects the collector's wait, not every spawned process.

## L. Concepts Explained

A formatter chooses source layout; a linter detects selected syntax/style issues;
a type checker analyzes possible values without running the application. These
checks cover different failure classes, so passing Ruff does not make mypy pass.
For example, a numeric `isinstance` guard can be runtime-correct yet violate a lint
style rule. A syntax-tree comparison removes formatting from the comparison while
retaining actual expressions; the two known builtin guard equivalents need a
narrow normalization rather than ignoring arbitrary differences.

PATH is an ordered executable search list: a missing `ffmpeg` lookup describes the
current environment, not the whole machine. Host `nvidia-smi` sees the Windows
driver; a Linux Docker probe exercises GPU passthrough through the container
runtime. Neither runs an ASR model. uv selects an isolated interpreter and package
environment; the project uses Python 3.12 even though host lookup returns 3.14.
A failing dependency stub can stop static analysis before application annotations
are checked, explaining why the two mypy diagnostics have different error totals.

## M. Questions and Answers

### Q1. Why is STEP_01 allowed to pass with missing tools?
Its acceptance gate explicitly requires a real version **or explicit missing
status**, saved GPU/Docker evidence and no disrupted existing services. Those
diagnostic gates pass; missing prerequisites still restrict later native setup.

### Q2. Why is full-project typing still reported as failed?
The official command exits 2 before checking all source. A scoped test check cannot
replace it. Both results are shown so a reviewer can distinguish new test typing
from unresolved original application debt.

### Q3. Why not just change mypy's Python target?
The Python 3.12 diagnostic exposes 79 errors across 18 files. It removes one syntax
barrier but does not fix those annotations or dependency interfaces. A compatible
development typing plan is needed rather than a cosmetic target switch.

### Q4. Why are the union guards equivalent here?
The operands are only supported builtin class objects (`int`, `float`, `list`,
`tuple`) on Python >=3.11. `isinstance` accepts their union as an alternative type
set. This claim is deliberately limited to these two sites, not arbitrary unions.

### Q5. What prevents formatting drift returning?
CI now runs the same strict Ruff lint and format commands that passed locally.
Remote execution is pending a future authorized push; local workflow parsing does
not prove GitHub jobs already ran.

### Q6. Why preserve failed evidence after correction?
It proves reproducibility and distinguishes baseline failure from the validated
outcome. Separate files retain exact outputs, so the successful run cannot erase
the failure chronology or imply that all earlier checks passed.

### Q7. Do 125 passing tests prove real model quality?
No. They validate current code paths and synthetic/mocked boundaries. Real ASR or
diarization quality requires consented labeled audio, fixed model versions and
defined evaluation metrics, none of which were executed in STEP_01.

### Q8. Why avoid installing torch merely for mypy?
An optional runtime install changes environment size and compatibility without
resolving the remaining typing debt. This diagnostic step did not authorize a
model/runtime provisioning operation; the absent import is recorded honestly.

### Q9. What was checked for service disruption?
All 52 pre-existing Docker container fingerprints matched before and after the
probe, including state/start/restart metadata. This supports non-disruption of
those containers; it is not a claim that all application endpoints were healthy.

### Q10. Does the history UI edit require new ERP screenshots?
It only changes equivalent guard syntax and has normalized AST parity with
upstream. No visual layout or interaction was changed, so visual acceptance is
not applicable. Future frontend implementation must use the approved reference.

### Q11. Why retain the pytest warning?
It signals an unresolved fixture-loop-scope default that may change with future
pytest-asyncio versions. The current run passes, and the warning remains visible;
changing async behavior needs deliberate regression analysis beyond this fix.

### Q12. What is safe to do next?
The repository/specifications and diagnostic evidence support reviewing STEP_02
when requested. Native installs and model work still need their own prerequisites.
This task stops at STEP_01; no later step was implemented or marked complete.

## N. Remaining Problems

F03–F05 remain unresolved with exact reproduction and next actions in the inventory.
Low available RAM limits safe model work; no processes were killed to improve it.
The collector bounds pipe waiting but does not guarantee cleanup of a detached
descendant whose direct parent has already exited. The async warning remains.
No real app startup, API credentials, model throughput, live browser interaction,
training or remote CI execution was validated in this correction cycle.

The next step's repository-inspection inputs are available: full Git history,
pinned upstream, master/index/prompts and progress/report evidence. This is not
general readiness for all future steps. No timestamps were adjusted; any future
adjusted commit schedule needs explicit dates/timezone and separate authorization
before rewriting published history.

## O. Final Quality Verdict

**PASS WITH LIMITATIONS — STEP_01 is ready for the next step's review.** Three of
three diagnostic gates pass; five failure groups identified, two corrected, three
unresolved. Full typing remains FAIL and native tool gaps remain explicit. Current
source behavior is supported by regression and narrow AST evidence; reports and
the Git/file inventory describe the actual uncommitted changes. No later step
started, no new infrastructure claimed and no model improvements invented.

Current decision: [correction summary](../environment/evidence/step01-correction-summary.json).
Supporting checks: [documentation verification](../environment/evidence/step01-documentation-checks.json).
