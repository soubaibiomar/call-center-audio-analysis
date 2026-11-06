# STEP_01 workstation prerequisites

Observed on 2026-10-24; UTC capture `2026-10-24T15:48:42.7623433+00:00`. Reporting timezone:
Africa/Casablanca. This is a diagnostic snapshot, not a guarantee that models or
future services can run. Machine evidence is in [step01-environment.json](evidence/step01-environment.json).

## Reproduce without installing or stopping anything

From the repository root in PowerShell 7.2 or newer:

```powershell
pwsh -NoLogo -NoProfile -File scripts/Test-Project28Environment.ps1
.venv/Scripts/python.exe -m pytest tests/unit/test_environment_diagnostics.py -q
```

The checker uses the current PATH, queries Windows resources and Docker state,
and writes a sanitized JSON report. A missing tool is recorded as `MISSING`;
a nonzero command as `FAILED`; a timeout as `TIMEOUT`; a launch exception as
`ERROR`. Exit 0 from the script means evidence was collected, not that every
prerequisite is satisfied. It does not install packages, pull images, load models,
read credentials or change service configuration. Its only container mutation is
creating and removing a uniquely named, short-lived, network-disabled GPU probe.

## Measured prerequisites matrix

| Tool/check | Resolved path (profile redacted) | Actual output | Status |
|---|---|---|---|
| git | `C:\Program Files\Git\cmd\git.exe` | git version 2.55.0.windows.3 | PASS |
| python | `<USERPROFILE>\AppData\Local\Microsoft\WindowsApps\python.exe` | Python 3.14.6 | PASS |
| uv | `<USERPROFILE>\AppData\Local\Microsoft\WinGet\Links\uv.exe` | uv 0.12.23 (46b84fd0b 2026-10-03 x86_64-pc-windows-msvc) | PASS |
| docker | `<USERPROFILE>\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe` | Docker version 29.9.2, build a82e528 | PASS |
| node | `C:\Program Files\nodejs\node.exe` | v24.18.0 | PASS |
| ffmpeg | `Not found on PATH` | MISSING | MISSING |
| code | `Not found on PATH` | MISSING | MISSING |
| docker_compose | `<USERPROFILE>\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe` | Docker Compose version v5.6.1 | PASS |
| npm | `C:\Program Files\nodejs\npm.cmd` | 11.16.0 | PASS |
| nvidia_smi | `C:\Windows\system32\nvidia-smi.exe` | NVIDIA GeForce RTX 4060 Laptop GPU, 8188, 165, 610.88 | PASS |

PowerShell: 7.6.5. Host Python is 3.14.6; the existing
uv virtualenv is **Python 3.12.15** and remains the supported baseline. Upstream CI
uses 3.11/3.12; do not install the pinned stack into host Python 3.14 by accident.
No Python or Node dependency changes were made in this step.

## Container and GPU boundaries

- Backend: `linux|x86_64|29.9.2|io.containerd.runc.v2,nvidia,runc,|runc`. Fields are OS type, architecture,
  Engine version, registered runtime names, default runtime.
- Context: `desktop-linux`; Linux containers run inside Docker
  Desktop's Linux environment, not directly as Windows processes.
- `nvidia` is registered as `nvidia-container-runtime`; NVIDIA Container Toolkit
  functionality is demonstrated by the GPU probe. Its package version was not
  queried; do not infer one from the driver version.
- GPU: `NVIDIA GeForce RTX 4060 Laptop GPU, 8188, 165, 610.88`. Fields: name, total MiB, used MiB, driver.
- Cached probe image: `nvidia/cuda:12.9.0-base-ubuntu22.04`; image identity is in
  the JSON. `--pull=never` prevents downloads. GPU probe exit 0, same GPU/driver
  visible inside the container, with no volume mounts or network access.
- NVIDIA driver compatibility is proved for `nvidia-smi`, not PyTorch kernels,
  cuDNN, CTranslate2 GPU inference, ASR quality or fine-tuning. The unchanged
  `src/agents/transcription.py::_detect_device` still falls back to CPU when
  optional torch is absent. Do not install torch in this environment-check step.
- All 52 pre-existing container fingerprints
  matched before/after, including identity, state, start time and restart count.
  1 container was running; one existing Ollama
  container was identified. No existing service, model or volume was modified.

## Resources and safe limits

| Resource | Observed value | Interpretation |
|---|---|---|
| Windows | Microsoft Windows 11 Home, build 26300 | Kernel version is 10.0.26300; Windows 11 uses a 10.0 kernel version |
| Physical RAM | 15.71 GiB total; 1.58 GiB available | Low headroom; defer model loading, training and concurrent heavy inference |
| Fixed disk C: | 358.31 GB free (333.70 GiB) | One observed fixed disk; no E: drive assumption |
| GPU | 8,188 MiB total, 165 MiB observed used | 7.996 GiB total; observations are not inference peak memory |
| Listeners | 31 endpoint rows / 21 distinct ports | Includes IPv4/IPv6 duplicates; no processes killed |

At this snapshot, ports 5000, 5173, 5432, 6379, 7860, 8000, 8080, 9000,
9001 and 11434 had no listeners. This is observation, not port reservation;
recheck before binding. All listener ports/PIDs are in the JSON; specific bind
addresses are redacted. No process command lines or customer content were read.

Operational policy for subsequent steps: one GPU-heavy operation at a time;
separate training from production inference; do not load models while available
RAM remains this low. A suggested 4 GiB minimum free-RAM guard before *considering*
model setup is a conservative project policy, not a measured model requirement.
Determine checkpoint sizes, cache paths, precision and per-model VRAM requirements
before any download. Current measurements establish no training capacity claim.

## Non-destructive remediation

1. **FFmpeg absent on host PATH:** use the existing baseline Docker image; a fresh
   `docker run --rm --pull=never --network=none --read-only project28-foundation:baseline ffmpeg -version`
   returned ffmpeg 7.1.5, exit 0. For native audio tools, locate an existing trusted
   FFmpeg install and add only its `bin` directory to the current session PATH.
   If none exists, inspect `winget search --name FFmpeg`, review the selected
   package/publisher, then deliberately install later. Nothing was installed here.
2. **VS Code launcher absent:** locate a known Code.exe and use its `bin` directory
   in the current session, or inspect `winget search --name 'Visual Studio Code'`
   before choosing a package. An absent launcher does not prove no editor exists
   elsewhere on the machine. No IDE or global PATH modification was made.
3. **Low available RAM:** the user can save work and close selected applications,
   then rerun diagnostics. Do not automatically kill processes or stop Ollama.
4. **Docker backend unavailable on another run:** record the failed command; the
   user can start Docker Desktop and select Linux containers. Do not reset Docker,
   delete volumes or edit NVIDIA/Ollama configuration as a diagnostic workaround.
5. **Cached GPU image absent elsewhere:** record `NOT_EXECUTED`; do not auto-pull.
   Plan a small compatible image explicitly before an intentional download.

Step 01 is DONE because its three evidence gates are satisfied, including explicit
missing-tool statuses. There are **0 unmet diagnostic acceptance gates**, **2 missing
PATH tools**, and **1 additional resource warning**. This is not full application
readiness: model/credential setup, original startup and future platform services
belong to later steps. The earlier baseline's missing API key remains a documented
limitation; no credential or model launch was attempted for this step.

## Quality review follow-up — 2026-10-24

Decision: **PASS WITH LIMITATIONS** for STEP_01. The tables above retain the initial
measurement timestamp; the current review is a separate snapshot.

Latest capture: `2026-10-24T16:02:20.7928747+00:00`; available RAM **1.13 GiB**, free disk
**358.24 GB**, used VRAM **366/366/366 MiB** across the three
diagnostic observations. Tools remain 8 PASS / 2 MISSING; existing services match.
See [review environment](evidence/step01-review-environment.json) and
[review decision](evidence/step01-quality-review.json).

The checker now bounds output capture as well as direct-child waiting, returns
explicit zero counts for an empty Docker inventory, and separates npm's actual
Node executable path from its launcher_path. Its tests decode PowerShell JSON as
UTF-8 and include a synthetic French/Arabic round trip. These changes do not install
anything or alter the application. Detached background children are not claimed to
be supervised after their parent exits; the collector bounds its own capture wait.

STEP_02 repository inspection dependencies are available. Low RAM, missing native
tools and existing full formatting/type-check failures remain relevant to later
setup/model steps. Do not start those operations merely because STEP_01 diagnostics
passed, and preserve the existing uncommitted STEP_01 work.


## Failure-correction follow-up — 2026-10-24

The preceding snapshots remain historical. Fresh environment evidence is in
[correction environment](evidence/step01-correction-environment.json), captured
`2026-10-24T16:12:53.0848184+00:00`. Tools remain 8 PASS / 2 MISSING; GPU probe
and all 52 pre-existing container continuity checks pass. Strict Ruff lint and
formatting now pass after two builtin guard updates, formatting and restored CI
gates. Full mypy remains FAIL (6 errors before abort); the Python 3.12 diagnostic
shows deeper typing debt (79 errors in 18 files). No runtime dependency installed.

See the [five-group failure inventory](failure-inventory.md) and the report's
appended A–O correction record. Two groups corrected, three unresolved; missing
FFmpeg/Code remain explicit environment findings. Original typing remediation
belongs with dependency/static-check work, not a suppressed checker. The complete
test suite passes 125 tests in 17.97 seconds. STEP_02 has not started.
