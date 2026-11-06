# Step 04 — Install dependencies and configure secrets safely

> **Status: DONE — PASS WITH LIMITATIONS.** Date: 2026-10-24, Africa/Casablanca. Lead: Platform.  
> Working branch `feature/project28-foundation`, HEAD `a37e4634af1d2947fc3c548d54e62bda0b0daf89`.  
> Original upstream/local main `fed4b610742c1337147281fcec8f2cdcc0a79be5`.  
> Environment: Windows 11, PowerShell, uv 0.12.23, managed Python 3.12.15.  
> [Prompt](../../prompts/STEP_04_install_dependencies_and_configure_secrets_safely_PROMPT.md), [template](../../report_templates/STEP_04_install_dependencies_and_configure_secrets_safely_REPORT.md).

## 1. Goal and plain-English explanation

Established the pinned development environment in the user-requested Documents
checkout. First completed relocation: all 38 top-level entries, hidden Git data,
ignored environment and private `.env` were moved without overwriting the empty
destination. Git status/refs and private environment were verified unchanged at
move time. The original clean upstream clone remains in Projects. Historical report
paths describe their own captures; they were not rewritten to invent a different history.

Inspected master instructions, current prompt, prior reports, architecture, pins,
templates and hooks. Repaired the venv's absolute editable/launcher paths using the
same managed base interpreter and an offline reinstall of the existing snapshot.
Installed the local pre-commit hook, ran compatibility diagnostics and added safe
non-overwriting configuration/readiness tools. Existing `.env` was preserved, not
replaced; the user is supplying any credential privately. No inference/model download.

## 2. Actual upstream vs your implementation

| Surface | Original / starting behavior | Actual change / compatibility |
|---|---|---|
| Python setup | Pinned direct dependencies, earlier 127-package Windows freeze | Same Python 3.12.15 and all 127 versions retained; UV relocatable metadata and editable path repaired |
| `.env` creation | Generic template includes placeholders and tracing defaults | Existing private file preserved; exclusive creation from safer project template only if absent |
| Readiness diagnostics | Config load requires key; app startup also initializes model | New script reports pin/credential states without app import or printing values |
| Local source-key guard | Bash/grep dependency and noisy matched output | Portable stdlib Python preserves original key-pattern rule, emits locations only, fails closed on scan error |
| Integration fixture | Mocked Config contained literal dummy keys | Empty unused credentials; model/provider calls remain mocked; tests still pass |
| Git exclusions | `.env` ignored, variant coverage narrow | `.env.*` and venv ignored; two intentional public templates remain included |

No production agents, workflow, persistence, provider selection or QA rules changed.
Actual [Git comparison](../environment/evidence/step04/git-comparison.json) separates
inherited edits from new setup files, which remain untracked until an authorized commit.

## 3. Files explained — created / modified / kept

- Created `scripts/check_project_setup.py`: pin/readiness diagnostics and exclusive template creation.
- Created `scripts/check_hardcoded_keys.py`: portable location-only source guard.
- Created `tests/unit/test_project_setup.py`: eight cases for preservation, creation,
  missing/placeholder values, non-disclosure, detection and fail-closed behavior.
- Modified `.gitignore`, `.pre-commit-config.yaml`, and the unused mocked credentials
  in `tests/integration/test_pipeline_end_to_end.py`.
- Created `docs/environment/setup.md`, this report, step04 evidence JSON and
  `workspace-relocation.json`; updated progress. Ignored venv metadata/entry points
  and `.git/hooks/pre-commit` changed locally; no private `.env` write by setup.
- Preserved production source, dependency pins, original MIT attribution and prior raw logs.

The [file inventory](../environment/evidence/step04/file-inventory.json) records paths,
sizes/hashes and Git comparison. No application data deleted or remote refs changed.

## 4. Code explanation and algorithm

`ensure_environment(root)` returns without writing if `.env` exists. Otherwise it
reads the approved safe template and opens `.env` with `xb`: an existing/concurrently
created file cannot be overwritten. `credential_status` returns MISSING, PLACEHOLDER
or CONFIGURED_UNVERIFIED, never the value. `inspect_setup` merges dotenv values with
environment overrides, restricts serialized provider names to recognized labels,
queries installed distribution versions and compares every direct/dev exact pin.
`main` reports JSON and fails nonzero on pin mismatch. Presence is not validation
of authentication/billing. Ollama is reported unsupported upstream, not substituted.

`check_source` iterates Python files under the supplied source root, refuses missing
roots/symlinks, reads UTF-8, and returns only relative path/line for the original
`sk-` plus alphanumeric pattern. `main` returns 0 clean, 1 findings, 2 scan failure.
No exception becomes a false clean scan. The system hook uses Python rather than
requiring the Windows Bash alias to provide a working Unix toolchain. Other Ruff
and detect-secrets hooks remain enabled at their original versions.

Tests load standalone tools by filename, use temporary synthetic inputs and assert
public output/file effects. The fake payload remains absent from JSON/findings.
No model, database schema or public application API added by this step.

## 5. Imports and dependency explanation

No new installed project dependency or version. `dotenv_values` is from the existing
python-dotenv 1.1.0 pin; it reads configuration without importing app startup.
`importlib.metadata` queries installed versions; `tomllib` parses Python 3.11+
project metadata; `json` serializes value-free diagnostics; `os` reads environment
overrides; `Path` implements local/exclusive IO; `Any` annotates heterogeneous JSON.
The key guard uses stdlib `re`/`Path`. Tests add stdlib `importlib.util`, `json`,
`Path`, `ModuleType`, and existing pytest fixtures/parameterization. No Conda,
GitHub SDK, PyTorch, pyannote or provider adapter installed. Isolated pre-commit
hook environments are separate from the unchanged 127-package application environment.

## 6. Core concepts explained for a beginner

A version pin fixes a dependency version; a Windows freeze records the observed
transitive set. It is not a universal hash-verified uv lock. No `uv.lock` exists,
so blindly invoking locked sync would be misleading. Here uv pip reinstalled the
existing exact snapshot offline with `--no-deps`; `uv pip check` then checked compatibility.
A moved venv can still run Python while its console wrappers/editable installation
point to the old folder. Recreating metadata and reinstalling cached identical
versions repairs those paths. A dotenv file is private input, not a report artifact.
Credential presence and provider authentication are different checks. A Git hook
is local automation, not a project commit, push or server-side branch rule.

## 7. Data, model and security

Diagnostics store booleans, statuses, public versions and pin comparisons only.
Existing `.env` and process values are never echoed; ignore rules prevent staging
private variants, while tracked names show only public templates. No customer audio,
private transcripts or model checkpoints used. The key guard retains original
detection semantics and reduces log disclosure. Removing unused fixture credentials
does not bypass scanning or actual authentication. Current production code still
supports hosted OpenAI/Gemini/Groq; Ollama integration is later work. Existing cache,
audit, encryption and typing limitations remain. No training or promotion occurred.

## 8. Tests and exact verification

**145 passed in 20.44s**. Eight focused setup tests pass. Ruff lint/format over
src/tests/app/scripts pass (63 Python files formatted); mypy of both new scripts
passes, compile checks and 127-package compatibility pass. Pre-commit configuration
validates, the installed hook runs all four tracked-file checks successfully, and
an explicit detect-secrets invocation covers the new untracked source/test files.
Full command arrays, runtimes, stdout/stderr and failures are in
[validation](../environment/evidence/step04/validation.json). Raw failed first hook
execution is retained in `validation-before-correction.json`; the following capture
before final fixture naming cleanup is retained separately. No failed record erased.

Gates: dependency setup attempted/outcome recorded PASS; secrets excluded from Git
PASS; no silent large model download PASS. First formatting issues were fixed with
the configured formatter. Full application mypy remains a historical known failure;
new-script type checks do not substitute for it. Existing pytest-asyncio warning
remains in stderr. No remote CI or real provider inference was executed by setup.

## 9. Analytics and quantitative report

127 distributions before → 127 after, identical name/version mapping; all 21
direct/dev pins match. uv reported resolve 0.225 s, preparation 4.48 s, uninstall
3.83 s and install 3.90 s. These phase observations are retained in
[installation](../environment/evidence/step04/installation.json); end-to-end install
wall time was not measured and is not inferred from command polling. Required
selected credential missing: 1 at capture; two unused alternative-provider keys
and optional tracing key also missing (four absence statuses, not four required keys).
Model WER/DER/F1, latency, peak inference VRAM and learning improvement: Not measured.

## 10. Questions and answers

1. **Why preserve all pins?** Setup should not introduce unreviewed transitive changes;
   before/after distribution mappings prove identical versions rather than assume it.
2. **Why no uv.lock?** The existing project provides a flat observed freeze, not a
   reviewed universal lock. Its Windows/platform and hash limitations are explicit.
3. **Why preserve `.env`?** It belongs to the user and may contain private values.
   Exclusive template creation permits first setup without overwriting existing work.
4. **Why not call a provider during diagnostics?** Presence checks can be safe and
   reproducible; credential validity and billable model execution require their own run.
5. **Why repair wrappers after moving?** Paths embedded in editable metadata and
   launcher scripts can remain absolute even when the base interpreter still runs.
6. **Why empty fixture keys?** The integration fixture mocks every provider/model
   boundary and does not use real keys. Empty values remove a misleading dummy secret.
7. **Why not allowlist the whole tests folder?** That would hide future leaks.
   The actual scanner remains enabled and synthetic fixtures retain their assertions.
8. **What blocks real analysis?** A usable privately configured provider key and a
   selected available model are needed. Setup success does not prove inference readiness.

## 11. Decisions and remaining risks

Honor original pins; use offline repair rather than package upgrades. Preserve
private configuration and actual supported providers. Replace host-sensitive Bash
scan with portable fail-closed Python. No scanner disabled or fabricated credential.
The freeze has no artifact hashes or cross-platform lock guarantee. Full app typing,
host FFmpeg/IDE PATH and earlier RAM warnings remain separate limitations. User
credential setup is pending; a future real run must not be reported as tested yet.

## 12. Handoff and evidence checklist

All three setup gates have execution evidence; project moved; 127 versions retained;
hooks installed/validated; credentials excluded; current relevant tests pass;
prior failed history preserved. The requested quality review confirms acceptance,
compatibility, justified imports, real metrics and unchanged UI; scope limitations
are recorded. STEP_05 baseline diagnostics are eligible. No STEP_06 success is
assumed, no commit/push/merge, no model download. Continue in order as the user requested.

## 13. Approved ERP UI design / visual contract verification

Not applicable: no frontend, routes, styles or user-facing API contract changed.
Original Gradio is preserved. `design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png`
remains the future UI reference; no fake screenshot/accessibility/visual acceptance
or reference-image metrics claimed.

# Failure Analysis and Correction Report

## A. Executive Summary
Relocation/setup and its quality checks executed. Current verdict PASS WITH LIMITATIONS.
Corrected stale local paths and two synthetic-fixture scanner problems; credential
absence is retained as an environment prerequisite. No production source refactor.

## B. Failure Inventory
| ID | Failure / limitation | Root cause | Correction / status |
|---|---|---|---|
| S01 | Relocated editable metadata still named old source | Absolute installation paths are not automatically moved with a venv | Recreated venv metadata without clearing packages and reinstalled exactly the same 127 versions offline; launchers and editable path validated |
| S02 | Tracked-file secret hook failed on upstream mocked config | Literal `test-key` dummy values in an entirely mocked integration fixture triggered Secret Keyword | Removed unused dummy credentials (empty strings); no scanner allowlist or exemption added; hook and integration regressions pass |
| S03 | Explicit new-test scan flagged two synthetic literals | Generic keyword detector treated the synthetic variable name as a secret assignment | Named the test payload by its actual purpose; payloads and non-disclosure assertions retained; explicit scan passes |
| E01 | No selected hosted-provider credential | Preserved private .env has no configured provider key at capture | Unresolved environment prerequisite for real STEP_06 execution; user will configure privately; not a STEP_04 dependency-install failure |


## C. Root-Cause Analysis
Absolute venv paths do not follow moves. Secret Keyword detection intentionally
looks at assignment context and cannot infer a mocked fixture's purpose. Empty
unused original keys and accurately named synthetic payloads solve the concrete
false positives without exempting files or altering scanner thresholds. Missing
credentials cannot be fixed by inventing values or silently switching providers.

## D. Code Corrections
Same-version offline reinstall repaired metadata/launchers. Original integration
fixture uses empty unused keys; new payload tests keep exact non-disclosure checks.
Portable guard preserves the pattern and fails closed. No new approach exceeded
three attempts; failed hook evidence and corrected executions are retained.

## E. Import and Dependency Analysis
All introduced imports and existing dependency rationale are in section 5. No
project package version changed; hook caches are isolated from application runtime.

## F. File-by-File Changes
Section 3 and the hashed inventory enumerate actual local deliverables. `.env`
was preserved; `.git/hooks/pre-commit` and ignored venv internals are local setup
effects, not source commits. No data deleted, code history rewritten or remote push.

## G. Original vs Improved Repository
Pinned upstream provides the original provider/configuration/hook implementation.
Current scripts add safe development checks, not neural capabilities. Git comparison
records inherited vs current edits; original production behavior remains unchanged.

## H. Architecture Impact
Only the development environment and pre-commit validation boundary change. No
inference/training service is introduced or coupled to setup diagnostics.

## I. Tests and Validation
See section 8 and raw validation JSON. Current tests/static/compatibility/hook checks
pass. Failed first captures remain evidence, not relabelled successes. Full app
typing and real inference are not claimed passed by a scoped check.

## J. Performance and ML Metrics
Observed install phases/package counts are in section 9. No speed improvement or
ML benchmark; model latency, quality and training metrics were not measured.

## K. Security Analysis
Secret values never serialized. Private dotenv variants ignored, templates allowed,
mock credentials removed, detector kept active. Existing security regression tests
pass in the suite. No customer data, model promotion, external deployment or RBAC
change occurred. Configured presence remains distinct from authenticated access.

## L. Concepts Explained
Exclusive creation refuses overwrites; pin comparison verifies environment identity;
metadata repair fixes absolute references. Secret scanning is defense-in-depth,
not a proof that all private files are safe to publish. Tracked-hook coverage and
explicit new-file scans are reported separately rather than conflated.

## M. Questions and Answers

1. **What actually failed?** Stale moved paths and synthetic secret detections. The
   first is an installation metadata problem; the others are verified test data,
   not real leaked credentials. Their different causes received different fixes.
2. **How was pin preservation proved?** Sorted distribution mappings before/after
   compare equal for 127 packages, then uv pip check confirms compatibility.
3. **Why use offline reinstall?** Cached identical artifacts repair installation
   paths without uncontrolled resolution or package/model downloads.
4. **Can the dotenv checker overwrite a key?** No: existing files return unchanged;
   a missing file uses exclusive binary creation, which also refuses a creation race.
5. **Why are placeholders not ready?** A nonempty template string is not a usable
   secret. The checker labels it PLACEHOLDER rather than asserting authentication.
6. **Why no Ollama fallback?** Upstream lacks that adapter. Selecting a local service
   name would not implement the missing integration and could hide a failed baseline.
7. **Was detection weakened?** No broad allowlist, threshold change or disabled
   hook. Original fake keys were unnecessary; current scanning and regressions pass.
8. **How does the Python guard fail?** It reports only location for a match, returns
   1, and returns 2 on scan errors instead of a false clean result.
9. **Why distinguish hook coverage?** All-files means tracked files in pre-commit;
   explicit new-source scans cover untracked code before any authorized staging.
10. **What remains?** Private credential configuration, original typing debt and
    later real-model/UI evaluation. These are documented rather than invented.

## N. Remaining Problems
Provider credential absence is an unresolved execution dependency for STEP_06.
Existing upstream privacy/type/platform limitations remain. No real-call success
or trained-model improvement is implied by environment setup.

## O. Final Quality Verdict
**PASS WITH LIMITATIONS** for STEP_04. STEP_05 diagnostics may proceed; no unmet
setup acceptance gate is hidden and no future step is automatically marked done.

## 14. Requested STEP_04 re-execution — 2026-10-24

Re-read the complete STEP_04 prompt, preceding STEP_03 report, existing setup
implementation, dependency manifests, safe template, hooks and tests. The master,
step index, UI specifications and current Git changes were reviewed in this session.
STEP_03's local acceptance gates are satisfied; remote collaboration limitations
do not block local setup. Existing implementation meets the requested setup scope,
so no duplicate implementation or dependency reinstall was necessary.

### Fresh execution and acceptance evidence

- `uv pip check --python .venv/Scripts/python.exe`: exit 0; **127 installed packages**.
- `scripts/check_project_setup.py`: exit 0; **21/21 direct/dev pins match**;
  existing `.env` preserved, not recreated; selected credential readiness false.
- `pre_commit validate-config`, `pre_commit install`: exit 0. Local Git hook
  installation refreshed successfully using the relocated environment.
- `pre_commit run --all-files`: all **four hooks pass**. Explicit detect-secrets
  execution for the two new setup scripts and setup test also passes, covering
  files not included by the tracked-file selection.
- `pytest tests/unit/test_project_setup.py tests/integration/ -q --tb=short`:
  **12 passed in 0.98 s**, zero failed/skipped (eight setup, four integration).
- Ruff lint and format including `scripts/`: exit 0; **63 files formatted**.
- `mypy scripts/check_project_setup.py scripts/check_hardcoded_keys.py`:
  exit 0, no issues in two files. This does not certify full application typing.
- `git check-ignore` confirms `.env`, `.env.production` and venv metadata ignored;
  tracked environment names contain only the two intentional public templates.
- `git diff --check`: exit 0. Application/source/test/configuration hashes unchanged
  across this revalidation; private configuration unchanged (boolean recorded,
  private contents and digest not written to evidence).

Exact commands, exits, durations and outputs:
[command capture](../environment/evidence/step04-revalidation-20261024T194456Z/commands.json).
[Summary](../environment/evidence/step04-revalidation-20261024T194456Z/summary.json)
records environment preservation and pin checks. No failed historical logs overwritten.
The immediately preceding STEP_05 review separately executed the full suite:
145 current tests passed in 21.03 s and 113 upstream tests in 10.40 s; see that
report's section 14. Those results are not labelled as new STEP_04 test executions.

### Change scope, compatibility and handoff

This repeat request refreshed the local Git hook and added this report section,
new evidence and a progress note. It corrected section 13's heading to the exact
required name. No production/test implementation, dependency version, lockfile,
private configuration, provider or model changed. Existing components and imports
are explained in sections 2–7; no new project imports were introduced. Installation
was already complete, so no new install-duration measurement or resolution count
is claimed. The historical install-phase observations remain in section 9.

All three STEP_04 gates pass: installation attempted and outcome recorded; private
secrets excluded; no silent model download. The flat Windows snapshot's lack of
artifact hashes/cross-platform locking, inherited full-app mypy failure and missing
provider credential remain explicit limitations. No UI surface changed; screenshot,
responsive and accessibility checks are not applicable to this setup revalidation.

**Status: DONE — PASS WITH LIMITATIONS.** The next sequential step is STEP_05,
already completed and independently revalidated. The next unfinished step is
STEP_06, still BLOCKED / FAIL until private provider configuration is ready.
No advancement, commit or push performed by this re-execution.

## 15. STEP_04 quality review — 2026-10-24

Audited the just-revalidated STEP_04 rather than treating blocked STEP_06 as done.
The following table addresses all ten review requirements.

| Requirement | Validation and decision |
|---|---|
| Acceptance criteria implemented | All three explicit gates satisfied: installation outcome recorded, secrets excluded from Git, no silent model download. Section 14 and historical installation logs establish execution. |
| Existing functionality preserved | No production change during re-execution/review. Fresh setup plus integration suite: **12 passed in 0.97 s**, zero failures/skips. The separate recent full-regression evidence remains linked through STEP_05; mocked integrations do not validate real models. |
| Architecture/security/performance | Configuration inspection avoids app/model startup. Exclusive template creation preserves existing configuration. Source guard reports locations without values and fails on file-read errors. No added service/infrastructure; no inference performance claim. |
| Imports and dependencies | All 21 direct/dev pins still match. No newly installed dependency; script imports and alternatives explained in sections 5–6. Full typing is not inferred from script typing. |
| Relevant automated checks | Fresh two-script mypy, source-key guard and whitespace check pass. Twelve setup/integration tests pass. Reviewed prior capture confirms all four hooks, Ruff lint/format and package compatibility passed in the immediately preceding revalidation; no needless repeat of unchanged checks. |
| Report/source/Git agreement | All 13 required report sections and eight existing local artifact links verified. Reviewed current tracked changes and untracked delivery files. Historical before/after changes remain distinguished from this documentation-only review. |
| Execution evidence | Reviewed raw command log, recorded its SHA-256 in the new review summary. Fresh tests/checks have separate raw output and durations; no historical evidence overwritten or model metrics invented. |
| Approved UI design | Not applicable: no new frontend, route or visual contract. Original Gradio preserved; no screenshot/accessibility pass claimed. |
| Issues and limitations | No confirmed new in-scope implementation defect. Flat snapshot is not a hash-verified cross-platform lock; inherited full-app typing remains failed. Credential presence diagnostics do not prove authentication. Regex source guard is a narrow inherited heuristic, not universal secret detection; separate detect-secrets remains enabled. |
| Next-step prerequisites | STEP_05 prerequisites satisfied and that step is already complete. Next unfinished STEP_06 remains BLOCKED / FAIL: selected credential readiness false. No advancement beyond this blocker. |

New artifacts: [quality command log](../environment/evidence/step04-quality-review-20261024T194544Z/commands.json)
and [quality summary](../environment/evidence/step04-quality-review-20261024T194544Z/summary.json).
Review modified this report and the progress note and created those two evidence
files. No source/test fixes, package installation, private configuration changes,
commit, push, UI change, provider request or model download was needed.

**PASS WITH LIMITATIONS** — STEP_04 acceptance criteria and relevant local checks
pass. The documented full-app typing limitation and STEP_06 credential blocker
remain unresolved; no further implementation step was executed.
