# STEP_01 failure inventory — correction cycle, 2026-10-24

Current decision: **PASS WITH LIMITATIONS** for the three diagnostic acceptance gates.
Five failure groups reproduced: two corrected, three unresolved. This is not a claim
that every original application quality gate passes. Prior diagnostic corrections
remain recorded in the step report and earlier evidence; they are not counted again.

| ID | Failure | Component | Severity | Reproduction | Root cause | Status |
|---|---|---|---|---|---|---|
| F01 | Three files fail formatting | history service, pipeline, history fixtures | P3 | `python -m ruff format --check src/ tests/ app.py` | Existing layout differs from configured formatter; CI formatter had been disabled | CORRECTED: formatted three files and restored CI format gate; 57 files pass |
| F02 | Two UP038 lint findings | history service and history UI | P3 | `python -m ruff check src/ tests/ app.py` | Tuple type guards conflict with configured union style; CI ignored UP038 | CORRECTED: equivalent builtin union guards; removed CI exception; strict lint passes |
| F03 | Full-project mypy aborts | original agents and dependency typing | P2 | `python -m mypy src/` | Missing ReportLab/Whisper typing, optional torch absent, NumPy stub syntax vs configured Python 3.11 target; deeper project typing debt | UNRESOLVED: official run has 6 errors in 3 files before further analysis; Python 3.12 diagnostic exposes 79 errors in 18 files |
| F04 | Native FFmpeg not on PATH | host audio prerequisites | P2 | collector `ffmpeg -version` lookup | No executable resolves on current host PATH | UNRESOLVED: baseline container FFmpeg 7.1.5 works; native installation/configuration deferred |
| F05 | VS Code launcher not on PATH | optional editor tooling | P3 | collector `code --version` lookup | No launcher resolves on current host PATH | UNRESOLVED: optional IDE setup deferred; absence on PATH does not prove absence on disk |

Use `.venv/Scripts/python.exe` for the Python commands. Exact command arrays,
stdout/stderr, exit codes and durations are retained in
[reproduction](evidence/step01-correction-reproduction.json) and
[validation](evidence/step01-correction-validation.json). Environment evidence is
[separate](evidence/step01-correction-environment.json). Severity is engineering
triage, not a CVSS score; no P0/P1 failure was confirmed in this scoped review.

F01/F02 were corrected in one implementation attempt followed by regression checks.
F03 had two diagnostic runs (configured target and Python 3.12); neither was
relabelled as passing. No broad typing refactor, dependency installation or check
suppression was attempted. For F04/F05, lookup and safe workaround discovery did not
change global PATH or install software. No three-attempt limit was exceeded.

Next actions: address project typing with a compatible development dependency plan
and source annotations during the relevant setup/static-check work; choose native
tool installation deliberately when needed. These are not unmet STEP_01 diagnostic
gates, which explicitly accept missing-tool evidence. Low RAM, inherited-pipe child
supervision limits and the pytest-asyncio configuration warning remain limitations.
