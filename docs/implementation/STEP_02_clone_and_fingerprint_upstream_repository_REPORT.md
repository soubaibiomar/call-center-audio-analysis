# Step 02 — Clone and fingerprint upstream repository

> **Status: DONE — PASS WITH LIMITATIONS.** All three STEP_02 acceptance gates pass.  
> **Date:** 2026-10-24; reporting timezone Africa/Casablanca; **lead:** Platform.  
> **Upstream:** https://github.com/ANI-IN/Call-Center-Intelligence-System.git  
> **Baseline branch/SHA:** `main` / `fed4b610742c1337147281fcec8f2cdcc0a79be5`.  
> **Working branch/SHA:** `feature/project28-foundation` / `a37e4634af1d2947fc3c548d54e62bda0b0daf89` plus uncommitted STEP_01/STEP_02 work.  
> **Environment:** Windows 11, PowerShell 7.6.5, Git 2.55.0.windows.3, uv 0.12.23,
> isolated Python 3.12.15; RTX 4060 Laptop 8 GB not used for inference in this step.  
> **Prompt:** [complete STEP_02 prompt](../../prompts/STEP_02_clone_and_fingerprint_upstream_repository_PROMPT.md).  
> **Template:** [supplied report template](../../report_templates/STEP_02_clone_and_fingerprint_upstream_repository_REPORT.md).  
> **Snapshot capture (UTC):** `2026-10-24T16:20:08.854843+00:00`.

> **Latest quality review:** Section 14 records the root-boundary fix, 10 provenance
> tests and 135 passing total tests. Earlier execution counts remain historical.

> **Latest diagnosis/revalidation:** The appended **Failure Analysis and Correction
> Report** (A–O) records two historical fixes revalidated, 135 passing tests and
> current limitations. Sections 1–14 retain their earlier results.

## 1. Goal and plain-English explanation

Built a reproducible source baseline so future changes can be compared to a known
original. Cloned upstream into a new sibling directory,
`<WORKSPACE_PARENT>/Project28-Upstream-Baseline-Step02`, after verifying that target
did not exist. The existing development checkout was already dirty with STEP_01;
it was neither reset nor presented as clean. The separate baseline clone was clean
before inspection and remains clean afterward. No project commit, push, branch
switch, remote change or history rewrite was performed.

STEP_01's current report/decision permits the next step with limitations. Git and
the uv Python interpreter work; no FFmpeg, IDE launcher, API credential, model or
GPU workload is required for cloning/static provenance. Its full-project typing
debt and resource warnings therefore do not block this step. Reviewed the existing
architecture document and STEP_01 decisions; no separate ADR directory was found.

Executed a new standard-library fingerprint tool against the real clean clone,
archived its tracked tree/file hashes/Python declarations/license/UI source, and
compared README claims with inspected source. Eight tests validate both success
and refusal behavior against real synthetic local Git repositories. The original
113 tests and combined 133 tests were executed separately. This step adds a
development provenance tool; it does not build the future neural platform.

## 2. Actual upstream vs your implementation

| Feature/code path | Verified upstream | STEP_02 outcome | Reason / compatibility |
|---|---|---|---|
| Git provenance | `main`, SHA `fed4b610…`, full history | New clean clone, 16 reachable commits, `fsck --full` exit 0 | Preserve traceable original; development branch untouched |
| File tree | 87 committed paths | `docs/upstream/baseline/tracked-tree.txt` and per-blob SHA-256 manifest | Immutable comparison unit; no application file altered |
| Python source | 56 Python files, 33 under `src/` | AST inventory of declarations/imports with source lines | Inspect without importing app/model startup |
| License | MIT, original Animesh Kumar copyright | Original bytes archived; working license retains original notice plus pre-existing fork attribution | No license removal or replacement |
| README vs source | Existing source/documentation differences | `docs/upstream/SOURCE_REVIEW.md` records evidence and limitations | Findings documented, not silently patched beyond scope |
| Gradio baseline | Soft theme; three tabs; upload/microphone/history/metrics | Exact committed source archived as permitted UI baseline evidence | No frontend modification or screenshot claim |
| Fingerprinting | No equivalent standalone tool | `scripts/fingerprint_repository.py` plus eight tests | Development-only; no runtime/training dependency added |

Actual Git differences are saved in [Git comparison](../upstream/evidence/step02-git-comparison.json).
At the working tree, `git diff --stat` shows five tracked STEP_01 changes (36
insertions/49 deletions). Against upstream it shows ten tracked changes (533
insertions/49 deletions): five preparation files/license differences plus those
five STEP_01 changes. **STEP_02 adds no further tracked source edits.** Its new
files are untracked and intentionally excluded by ordinary `git diff`; the complete
delivery inventory and `git status --untracked-files=all` expose them separately.

## 3. Files explained — created / modified / kept

| Path | State / purpose / interfaces / verification |
|---|---|
| `scripts/fingerprint_repository.py` | Created; repository/destination paths → manifest/tree/source archive; real Git fixture and baseline execution |
| `tests/unit/test_repository_fingerprint.py` | Created; eight local Git tests; no provider network or model startup |
| `docs/upstream/SOURCE_REVIEW.md` | Created; 24-module map, schemas/data flow, README discrepancy/risk matrix and UI baseline |
| `docs/upstream/baseline/provenance.json` | Created; versioned metadata schema, SHA/branch/remote and all 87 path/blob/size/SHA-256 records |
| `docs/upstream/baseline/tracked-tree.txt` | Created; original tracked tree with Git mode/blob ID/path, one row per committed file |
| `docs/upstream/baseline/python-symbols.json` | Created; imports and classes/functions/methods for all 56 Python files with line ranges |
| `docs/upstream/baseline/source-evidence.md` | Created; exact text of committed app, README, license and UI modules; baseline UI source option |
| `docs/upstream/baseline/LICENSE.upstream.txt` | Created; byte-identical original license retained separately |
| `docs/upstream/evidence/step02-*.json` | Created; preflight, clone, clean baseline, first/final validation, reproduction, source facts, diff, delivery verification/inventory |
| This STEP_02 report | Created from supplied section structure; observed results replace unexecuted placeholders |
| `docs/implementation/PROGRESS.md` | Modified; STEP_02 DONE, remaining 43 steps NOT STARTED |
| Existing application, dependencies, CI, STEP_01 reports/evidence | Kept; prior uncommitted work preserved byte-for-byte except deliberate tracker update |
| New sibling clone | Created outside development checkout; original tracked files and full Git objects; no code installation |

The [delivery inventory](../upstream/evidence/step02-delivery-inventory.json) enumerates
each STEP_02 file with byte count/hash rather than treating an evidence-directory
wildcard as a complete file list. No repository files deleted.

## 4. Code explanation and algorithm

`git(repository, *arguments)` passes a list directly to `subprocess.run`, without
shell expansion, captures bytes, enforces a 30-second per-query timeout and raises
on nonzero exits. Its calls only inspect state/objects. `inspect_python` calls
`ast.parse` on bytes, walks syntax nodes and emits declaration names/kinds/source
lines plus normalized import statements. It never imports the archived modules.

`fingerprint` resolves the two paths and rejects destinations inside the baseline
or already present. It rejects dirty tracked/untracked state, shallow history and
an origin differing from the approved public URL. It pins HEAD before enumerating
`git ls-tree -r -z --full-tree`: NUL delimiters avoid splitting filenames at spaces.
Each entry yields Git mode/type/blob ID/path. `git cat-file blob <OID>` reads the
committed bytes; SHA-256 and byte length describe those exact bytes, independent of
Windows checkout CRLF conversion. A Gitlink/submodule raises an explicit failure;
symlink blobs can be fingerprinted but are not parsed or followed as source.

For example, the manifest's app hash identifies the original `app.py` containing
import-time Whisper initialization, while the AST parser only lists its imports
and syntax. No model gets loaded just to count a module. For exported source, paths
are quoted headings inside one Markdown file, not filesystem destinations chosen
by upstream filenames; archive traversal through `../` paths is avoided.

After inspection, HEAD/clean status are checked again before an exclusive new output
directory is created. JSON preserves Unicode, the tree is written as UTF-8, selected
source is archived and raw license bytes are written separately. `main` parses two
CLI paths, prints the SHA/count summary and exits 1 with a failure class on errors.
An existing archive is preserved; a mid-write failure can leave a partial archive
for inspection, never silently overwritten or reported as completed. The tool does
not lock Git against other writers, so run it against the dedicated idle baseline.

Time scales with tracked blobs/source bytes and Git process count; blob reading is
sequential and the parsed declaration list is accumulated in memory. This 87-file
repository needs no database/service infrastructure or GPU. The provenance JSON
schema is a development artifact, not a new production API contract.

## 5. Imports and dependency explanation

All tool imports use Python 3.12.15's standard library; no manifest/lockfile changes.

| Import | Origin, use and reason |
|---|---|
| `from __future__ import annotations` | Stdlib language feature; postpones annotation evaluation in tool/tests |
| `import argparse` | Stdlib; validates repository/destination CLI arguments and exit handling |
| `import ast` | Stdlib; parses declarations/imports without executing source; safer than app import for inspection |
| `import hashlib` | Stdlib; SHA-256 of committed bytes; tests use a fixed independently specified byte payload |
| `import json` | Stdlib; portable structured evidence and quoted archive headings; tests read exported contracts |
| `import subprocess` | Stdlib; bounded Git queries without shell; fixture tests create isolated synthetic commits |
| `from datetime import UTC, datetime` | Stdlib; unambiguous UTC capture timestamp, no invented engineering duration |
| `from pathlib import Path` | Stdlib; path resolution, external-output validation and UTF-8 file IO |
| `from typing import Any` | Stdlib; heterogeneous JSON/AST record annotation, no runtime/model effect |
| `import importlib.util` (tests only) | Stdlib; loads the standalone tool by path without packaging or application startup |
| `import pytest` (tests only) | Existing pytest 8.3.5; temporary-directory fixture, parameterization and negative assertions |

Git is an existing external executable, not a new Python dependency. Alternatives:
GitPython would add a dependency without improving this bounded read-only workflow;
filesystem hashing alone would include line-ending conversions and could accidentally
inspect ignored local data. AST inspection intentionally does not discover runtime
dynamic imports or prove dependency execution.

## 6. Core concepts explained for a beginner

A remote is a named repository address; a branch moves to new commits over time.
A pinned commit SHA identifies one tree/history state. Here `main` resolved to
`fed4b610…`, the same commit STEP_01 used; future comparisons should use the recorded
SHA even if GitHub advances. A full clone retains ancestors (16 reachable commits
here); a shallow clone would omit part of that history.

A tracked file is in Git's tree. An untracked report can exist on disk without
appearing in `git diff`. That distinction explains why a status/inventory is required
in addition to diff statistics. A Git blob identifies committed file content; our
SHA-256 is an additional portable digest, not a claim that the commit was signed.
On Windows a text checkout may contain CRLF even if its blob has LF, so the tool
hashes the blob. AST parsing reads syntax rather than running the application's
import-time initialization. MIT notice preservation retains upstream attribution;
it does not establish rights to reuse every sample audio recording for training.

## 7. Data structures, ML evaluation, security and privacy

The provenance schema stores capture time/remote/branch/SHA, cleanliness/full-history
flags, counts and per-file `path`, Git `mode`, `git_blob`, `bytes`, `sha256`. The
separate symbol index stores path and declaration/import source positions. The
[source review](../upstream/SOURCE_REVIEW.md) explains `AudioInput` → `IntakeResult`
→ `TranscriptionResult` → summary/QA → `CallReport`, UUIDs and score/confidence bounds.
No existing production schema, validation rule, persistence model or public API changed.

Clone/fingerprint operates on public committed source; ignored `.env`, databases,
credentials and user calls are excluded. Ten bundled MP3 blobs were counted/hashed
without decoding/listening/transcription; their consent, scenario labels and training
rights are unverified. No training, dataset split or model download occurred.
No inference/training improvement, WER/CER/DER/F1, throughput or peak inference VRAM
was measured. The eight tests use synthetic source/license bytes, not customer data.

Git clone was the network operation. Existing Docker/Ollama services were not queried
or changed by STEP_02, and no public server was launched. Diagnostics redact the
user-profile prefix. Exact public origin validation prevents exporting an unexpected
credential-bearing URL. Hashes and `git fsck` establish content consistency/object
integrity, not upstream-author authenticity or a full software-supply-chain audit.
The raw transcript cache, audit mutability and encryption uncertainty are documented
existing risks, with no false claim that STEP_02 fixed them.

## 8. Tests, exact outputs and verification

| Acceptance criterion | Executed evidence | Result |
|---|---|---|
| Git remote and SHA recorded | Clone/clean baseline JSON plus provenance; approved URL, `main`, `fed4b610…` | PASS |
| Repository clean before modifications | New target absent at preflight; fresh clone has empty porcelain status before source inspection and after validation | PASS for baseline; development checkout explicitly preserved dirty |
| License/attribution retained | Raw upstream license matches blob hash; working license retains original MIT text and pre-existing fork notice | PASS |

Reproduce the positive export with a **new external destination**:

```powershell
.venv/Scripts/python.exe scripts/fingerprint_repository.py ../Project28-Upstream-Baseline-Step02 ../Project28-Another-New-Archive
.venv/Scripts/python.exe -m pytest tests/unit/test_repository_fingerprint.py -q --tb=short
```

Do not reuse an existing destination or create outputs inside the baseline. The
archive was also reproduced into a temporary directory with the final tool; all
manifest content except capture time, tree, symbols and source archive matched.

| Command / execution context | Exit / actual result |
|---|---|
| `git clone --no-local -- <approved URL> <new sibling>` | 0; 20.22 s process wall time, no existing target overwritten |
| Baseline `git status --porcelain=v1 --untracked-files=all` | 0; empty before/after |
| Baseline `git rev-parse --is-shallow-repository`, `git fsck --full` | 0; false / no integrity errors |
| Final tool export to temporary external output | 0; 87 tracked paths, 33 source modules; 3.07 s |
| Focused provenance tests | 0; 8 passed in 2.63 s; 0 failed/skipped |
| Clean upstream `pytest tests/ -q --tb=short`, using project venv | 0; 113 passed in 10.70 s; 0 failed/skipped |
| Working tree `pytest tests/ -q --tb=short` | 0; 133 passed in 20.21 s; 0 failed/skipped |
| `ruff check src/ tests/ app.py scripts/fingerprint_repository.py` | 0; all checks passed |
| `ruff format --check src/ tests/ app.py scripts/fingerprint_repository.py` | 0; 59 files already formatted |
| `mypy scripts/fingerprint_repository.py` | 0; no issues in 1 source file |
| `mypy tests/unit/test_repository_fingerprint.py --follow-imports=skip --allow-untyped-decorators` | 0; scoped test typing, no issues in 1 file |
| `compileall -q app.py src/ tests/ scripts/fingerprint_repository.py` | 0 in first validation; no executable tool changes afterward |
| `uv pip check --python .venv/Scripts/python.exe` | 0; 127 installed packages compatible |
| Re-run tool against existing `docs/upstream/baseline` | Expected 1, actual 1 (`FileExistsError`), archive preserved |
| `git diff --check` | 0 |

Initial lint reported four line-length/layout issues and Ruff formatting corrected
them before final checks. The first license byte-preservation assertion failed:
the synthetic fixture used text-mode writing, producing CRLF on Windows while its
oracle specified LF. Fixed the fixture with `write_bytes`, preserving the intended
exact-byte assertion rather than normalizing away corruption. Added a missing-license
refusal test. First evidence has 1 failed/6 passed focused and 1 failed/131 passed
combined; the independent upstream run stayed 113/113. Those failures are preserved
in [first validation](../upstream/evidence/step02-validation-first-run.json), not
overwritten by [final validation](../upstream/evidence/step02-validation.json).

Eight current cases cover exact capture/no app import, dirty tracked and untracked
state, existing output preservation, output-inside-baseline refusal, unapproved
origin, shallow history and missing license. They use real temporary Git repositories;
synthetic fixture commits do not alter project history. The existing pytest-asyncio
loop-scope deprecation warning remains visible. Full-project mypy remains an unresolved
STEP_01 failure; it was not rerun or suppressed because no application typing changed.
Remote CI, real provider/model calls and UI runtime were not validated in STEP_02.

## 9. Analytics and quantitative report

| Metric | Baseline → observed / definition / interpretation |
|---|---|
| HEAD SHA | STEP_01 pinned `fed4b610…` → fresh remote clone same full SHA; one snapshot, identity rather than a numeric improvement |
| Tracked files | 87 upstream → 87 in original archive; count of `ls-tree -r` blobs, independent of untracked development additions |
| Source modules | 33 upstream → 33 preserved `.py` paths under `src/`, including nine empty initializers; 24 nonempty modules mapped |
| Python file count | 56 committed `.py` files = 33 source + 22 test/helper + 1 app; source inventory covers all 56 |
| Graph/UI facts | AST extraction: 8 `add_node` registrations, 3 Gradio tabs, 22 injection patterns; QA weights sum to 1.0 |
| History | 16 commits reachable from baseline HEAD; non-shallow, `fsck --full` exits 0 |
| Regression cases | 113 clean upstream → 133 working tree = original 113 + STEP_01 diagnostics 12 + STEP_02 provenance 8; final pass rate 133/133 |
| Execution duration | One final full working run 20.21 s pytest time / 21.96 s process wall time; no speedup claim across different test workloads |

Counts come from Git/AST execution, not README estimates. Clone/export timings are
single workstation observations affected by network/cache/process overhead, not a
statistical benchmark; p50/p95 are not measured. Model quality, cost/provider quotas,
inference latency, multilingual accuracy, diarization quality and training improvement
are **Not measured**. Hardware facts are inherited STEP_01 observations; no fresh GPU
load or capacity benchmark was needed.

## 10. Questions with answers

1. **Why pin a SHA instead of only recording `main`?** A branch moves; the full
   SHA fixes the comparison tree. This fresh clone matched the earlier baseline,
   so provenance can be compared without silently moving to another revision.
2. **Why a separate clone when a development checkout exists?** The checkout
   contains valuable uncommitted STEP_01 changes. A new previously absent sibling
   gives a genuinely clean upstream baseline without reset/stash/destructive work.
3. **Why hash Git blobs rather than checked-out files?** Windows line-ending
   conversion can change disk bytes. Committed blob bytes are reproducible across
   platforms. The fixture failure demonstrated why byte/text distinctions matter.
4. **How is importing the original application avoided?** `ast.parse` inspects
   bytes and Git reads objects. Tests include an app that raises if executed, yet
   export succeeds. This avoids credential checks and Whisper startup/downloads.
5. **What if a destination already exists?** The tool exits nonzero before writing.
   Both a sentinel test and a real CLI refusal prove existing evidence is preserved;
   pick a new destination after inspection rather than automatically removing it.
6. **Do the source hashes prove model correctness or security?** No. They establish
   identity and enable later comparisons; the original source still contains raw
   transcript caching, heuristic diarization and ordinary mutable audit storage.
7. **Why is no UI screenshot included?** STEP_02 explicitly permits source evidence.
   Exact Gradio/app sources are archived. No frontend changed and model-backed
   app startup remains future work; a reference picture is not an execution screenshot.
8. **Why retain the MIT notice but defer sample training use?** The original code
   notice must remain with the source. Sample path presence does not verify caller
   consent, recording ownership or permission for model training; none was assumed.

## 11. Decisions, changes and risks

| Decision / risk | Rationale / handling |
|---|---|
| Dedicated full clone, no overwrite | Fulfills clean-baseline gate while preserving existing work; no stash/reset/cleanup required |
| Stdlib Git/AST tool, no GitPython | Small repeatable seam with negative tests; no inference/runtime dependencies |
| Baseline source evidence instead of app launch | Explicit step option, avoids model/credential setup and falsely styled screenshots |
| README conflicts | Eight-vs-seven nodes, explicit port and post-transcription injection order recorded in source review; no application behavior changed |
| Existing privacy/reliability risks | Raw cache before redaction, mutable audit, encryption not proved, Windows temp handling; retain for later scoped work |
| Existing typing/native tools/RAM limitations | Not prerequisites for provenance; still unresolved, not relabelled as passing |
| Concurrent checkout mutation / partial archive | Dedicated idle baseline and before/after recheck; no transaction/lock guarantee; failed partial outputs need inspection/new destination |
| Python 3.11/remote platform compatibility | Tool uses supported >=3.11 syntax, but executed only on local Python 3.12 Windows; remote CI not claimed |

No cost/quota/availability claims were externally verified because this step only
archives and contrasts upstream source claims. No edits to upstream README, services,
security policies, dependency manifests or the earlier CI corrections were needed.
No adjusted timestamps or new project commits were created. The user's milestone
commit preferences remain in effect; date adjustments require explicit dates/timezone.

## 12. Actual deliverables, next handoff and evidence checklist

- [x] New target inspected and fresh upstream clone completed without overwrite.
- [x] Origin/branch/SHA/full history/clean before-and-after state recorded.
- [x] License bytes and existing attribution retained.
- [x] Tracked tree, all blob fingerprints, all Python declarations/imports archived.
- [x] Entry points/schemas/module boundaries and README differences inspected.
- [x] Original and combined tests executed; initial failure and correction retained.
- [x] No ignored secrets/user call data copied and no existing services changed.
- [x] All prior files preserved except deliberate progress-tracker update.

Evidence: [preflight](../upstream/evidence/step02-preflight.json),
[clone](../upstream/evidence/step02-clone.json),
[clean baseline](../upstream/evidence/step02-clean-baseline.json),
[provenance](../upstream/baseline/provenance.json),
[source facts](../upstream/evidence/step02-source-facts.json),
[reproduction](../upstream/evidence/step02-reproduction.json),
[delivery verification](../upstream/evidence/step02-delivery-verification.json),
[delivery inventory](../upstream/evidence/step02-delivery-inventory.json).

**Next eligible step: STEP_03 — Establish branching and collaboration conventions.**
Inputs are available: pinned original snapshot, preserved fork branch/history,
source inventory, user commit preferences and reports. Next safe read command is
`Get-Content prompts/STEP_03_*_PROMPT.md` from the working repository. STEP_03 was
not started. Progress is now two DONE and 43 NOT STARTED.

## 13. Approved ERP UI design / visual contract verification

Primary approved future reference:
`design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png`, interpreted with the design
system/checklist read for this step. Visual changes: **Not applicable**. Original
`app.py`, `src/ui/app_builder.py` and all three tab modules are preserved and archived
in [source evidence](../upstream/baseline/source-evidence.md). No new routes, rendering
code, API shapes, theme tokens or chart values were introduced. No frontend imports
were added. The existing Gradio Soft theme is retained as a baseline, not declared
compliant with the future Commercially-style ERP layout.

| UI verification item | Actual result |
|---|---|
| Original upload/microphone/history/observability behavior | Source archived and described; current regression suite passes; full UI execution not performed |
| Green/neutral palette, white cards, rounded sidebar/top bar | No new frontend; not implemented or visually audited in this step |
| Loading/error/success behavior | Existing analyze callback code archived; no runtime screenshot claim |
| Desktop/mobile screenshots | Not captured; source evidence explicitly permitted by STEP_02 |
| Contrast/keyboard/focus/reduced motion | Not tested; no accessibility changes |
| Reference mock metrics | Never used as measured analytics |
| Design decision | Preserve Gradio regression baseline; future React work must implement the approved reference and capture actual screenshots |

**Final decision: PASS WITH LIMITATIONS — STEP_02 is complete; STEP_03 is eligible.**


## 14. STEP_02 quality review — 2026-10-24

**Current decision: PASS WITH LIMITATIONS.** Sections 1–13 retain the initial
execution results (eight provenance tests, 133 total tests). This review fixes
one confirmed current-step defect and increases those counts to **10** and **135**.
Original upstream source, archived blobs/license and STEP_01 implementation remain
unchanged. No subsequent implementation step, project commit or push was performed.

### Confirmed finding, reproduction and correction

**R01 — Medium severity, high confidence: repository-subdirectory input bypassed
the archive write boundary.** The tool originally resolved the caller's directory
as the protection boundary. Git accepts `-C <repo>/src` and still queries the whole
repository; `<repo>/archive` is outside `src` but inside the actual checkout. Thus
`fingerprint(repo / "src", repo / "archive")` could create untracked archive files
inside the baseline despite the stated no-modification contract. Default root-path
usage and the original exported baseline were unaffected; the existing eight tests
had not exercised the subdirectory case.

Added `test_subdirectory_cannot_bypass_baseline_write_protection` first. Its exact
reproduction produced **1 failed, 8 deselected** (`DID NOT RAISE ValueError`) against
the original code; see [failed reproduction](../upstream/evidence/step02-review-reproduction.json).
The correction resolves Git's actual root before testing the output boundary:

```python
repository = repository.resolve(strict=True)
repository = Path(
    git(repository, "rev-parse", "--show-toplevel").decode("utf-8").strip()
).resolve(strict=True)
```

The first line verifies/resolves the supplied path. The read-only Git query obtains
the checkout root even when the input names a nested directory. UTF-8 decoding
turns Git's path bytes into a path string; resolving that root lets the existing
equality/ancestor check protect the entire checkout. The query uses the existing
bounded no-shell helper. No imports, dependency versions, application APIs, model
paths or training behavior change. One additional Git query is required per export.

Added `test_capture_from_subdirectory_uses_complete_repository` to prove supported
subdirectory inputs still export all committed files to a safe external destination.
Both tests check the baseline remains clean. Files modified by this review are
`scripts/fingerprint_repository.py`, `tests/unit/test_repository_fingerprint.py`,
this report and `docs/implementation/PROGRESS.md`; fresh review JSON and a preserved
pre-review inventory are added under `docs/upstream/evidence/`. The current
[delivery inventory](../upstream/evidence/step02-delivery-inventory.json) lists every
file with byte/hash evidence. The old inventory is explicitly historical.

### Ten-point review matrix

| Criterion | Review evidence and result |
|---|---|
| 1. Acceptance criteria implemented | Approved remote/SHA and original clean clone evidence checked; fresh baseline still clean/full-history; MIT bytes/attribution verified. All three gates PASS. Existing development checkout remains intentionally dirty. |
| 2. Existing functionality preserved | 135 tests pass; prior application/CI changes preserved byte-for-byte. Actual upstream export reproduces original archive. No application source changed in this review. |
| 3. Architecture/security/performance | Development-only bounded Git/AST tool remains separate from app startup. R01 boundary defect fixed and covered. Dedicated idle clone still required; no locking/atomic-output guarantee added. |
| 4. Imports/dependencies justified | Correction uses existing `Path`/Git helper. No new imports, package installs, requirements or lockfile edits. Original standard-library/test imports remain justified in section 5. |
| 5. Unit/integration tests | Full suite 135 passed; includes original unit/security/integration and 22 diagnostics/provenance tests. Ten focused provenance tests pass. No credential-backed inference was tested. |
| 6. Report/source/Git agreement | Root normalization and two tests documented; updated hashes, Git comparison and tracker checked. Historical 133-test results are retained rather than silently relabelled. |
| 7. Metrics/benchmark evidence | All counts/times below come from retained stdout or Git objects. 87 baseline blobs independently hash-verified; no model metrics or performance improvement claim. |
| 8. Approved UI | No UI/API changes; original Gradio source evidence remains byte-identical. STEP_02 allows source evidence. No new screen/theme or visual-compliance claim. |
| 9. Issues/limitations documented | R01 corrected; full app typing, native tools, low-RAM observations, async warning and existing privacy risks remain explicit. No new unresolved in-scope acceptance failure identified. |
| 10. Next-step dependencies | Full upstream history, clone/provenance, working branch, user commit preferences and reports are available for STEP_03. Tracker remains two DONE, 43 NOT STARTED; STEP_03 not executed. |

### Fresh execution results

All commands use the existing uv Python 3.12.15 interpreter. Exact command arrays,
exit codes, stdout/stderr and wall durations are in
[review validation](../upstream/evidence/step02-review-validation.json).

| Check | Actual result |
|---|---|
| `pytest tests/unit/test_repository_fingerprint.py -q --tb=short` | Exit 0; 10 passed in 3.45 s; no failures/skips |
| `pytest tests/ -q --tb=short` | Exit 0; 135 passed in 20.82 s; no failures/skips (22.86 s process wall time) |
| `ruff check src/ tests/ app.py scripts/fingerprint_repository.py` | Exit 0; all checks passed |
| `ruff format --check src/ tests/ app.py scripts/fingerprint_repository.py` | Exit 0; 59 files already formatted |
| `mypy scripts/fingerprint_repository.py` | Exit 0; no issues in 1 file |
| `mypy tests/unit/test_repository_fingerprint.py --follow-imports=skip --allow-untyped-decorators` | Exit 0; scoped test-file check only |
| `compileall -q scripts/fingerprint_repository.py tests/unit/test_repository_fingerprint.py` | Exit 0 |
| `git diff --check` | Exit 0 |
| Baseline `git status --porcelain=v1 --untracked-files=all` | Exit 0; empty |
| Baseline `git fsck --full` | Exit 0; no integrity errors |
| Final tool: real upstream `src/` → temporary external archive | Exit 0; 87 files/33 source modules; 3.04 s; original manifest matches except capture timestamp; symbols/tree/source/license match |

[Equivalence evidence](../upstream/evidence/step02-review-equivalence.json) binds the
real export to the current tool/test SHA-256 values. The original clean upstream
113-test run in section 8 is historical and was not repeated; the combined suite
freshly re-exercises those original tests. Full application mypy was not rerun or
made green by these scoped checks; its STEP_01 failure remains unresolved. The
pytest-asyncio fixture-loop-scope warning persists in stderr. No dependency audit,
remote CI, browser runtime, audio inference or training benchmark was run here.

### Remaining limitations and handoff

Root normalization fixes the confirmed write-protection defect. This tool still
does not lock the checkout or atomically publish multi-file archives; a concurrent
writer or mid-write failure requires inspection and a new destination. Per-command
timeouts do not impose a total export deadline. Git integrity/hashes do not prove
author identity or safe behavior of all upstream dependencies. Existing raw
transcript cache, mutable audit storage, unverified encryption and Windows temp
cleanup risks remain source-review findings, not fixed platform capabilities.
Earlier RAM/native-tool observations are not a fresh hardware-readiness measurement.

No visual changes require Commercially screenshot comparison in this review. Future
frontend implementation still needs actual screenshots and accessibility checks.
No later step started, no project history altered and no model improvement claimed.

**PASS WITH LIMITATIONS — STEP_02 ready for STEP_03, with the limitations above.**


# Failure Analysis and Correction Report

Date: 2026-10-24; timezone Africa/Casablanca. This appendix is the latest STEP_02
diagnosis/revalidation record. Sections 1–14 and their failed logs remain preserved
as historical execution evidence. STEP_02 entered this cycle with PASS WITH
LIMITATIONS, not an unresolved FAIL; no step was promoted by documentation alone.

### A. Executive Summary

Revalidated two historical STEP_02 failures: R01 archive-boundary handling and T01
the Windows license fixture. Isolated single-correction reversals reproduce both
failures; the unchanged corrected code passes all 135 current tests. No new active
failure was found and no additional source patch was necessary. All three STEP_02
acceptance gates remain satisfied. Full application typing and existing setup/privacy
limitations remain distinct from this development-tool step's acceptance criteria.

### B. Failure Inventory

| ID | Failure | Component | Severity | Reproduction | Root cause | Status |
|---|---|---|---|---|---|---|
| R01 | Archive could be written inside baseline via subdirectory input | `fingerprint` output boundary | P2 | Isolated old root handling: `pytest ... -k subdirectory_cannot_bypass` → 1 failed, 9 deselected | Caller directory was used as the boundary although Git resolves the repository root | Previously corrected with Git-root normalization; current refusal and external export revalidated |
| T01 | Exact license assertion failed on Windows | Synthetic Git test fixture | P3 | Isolated old text-mode fixture: `pytest ... -k capture_hashes_committed_bytes` → 1 failed, 9 deselected | `write_text` created CRLF while the expected committed payload specified LF | Previously corrected with `write_bytes`; current byte-exact test revalidated |

See [structured inventory](../upstream/FAILURE_INVENTORY.md). Counts are **2 historical
failures identified, 2 previously corrected and revalidated, 0 newly discovered,
0 unresolved within STEP_02**. Do not interpret these counts as zero remaining
issues across Project 28. Earlier formatter housekeeping is preserved in section 8,
and current strict lint/format checks pass without exceptions added by this cycle.

### C. Root-Cause Analysis

R01 came from inconsistent interpretation of the input path. `git -C repo/src`
operates on the owning repository, while the original path comparison protected
only `repo/src`. An output such as `repo/archive` passed that comparison despite
modifying the baseline. The actual checkout root is the correct boundary.

T01 was a test-data construction error, not a license corruption in the tool.
Windows text-mode IO translated LF to CRLF before the fixture committed its
synthetic license. The oracle specified LF bytes. Byte-writing makes the fixture
match its independently defined payload without weakening the assertion.

For each issue, a temporary copy reverses exactly that mechanism and selects its
regression test. Both fail for the expected reason. The original raw failures and
these new controlled reversals are different runs and are retained separately.
Reversal is used to verify test sensitivity, not to damage or re-fail the real repo.

### D. Code Corrections

The validated R01 implementation in `scripts/fingerprint_repository.py::fingerprint`
resolves the supplied directory, queries `git rev-parse --show-toplevel`, resolves
that root and applies the existing destination equality/ancestor checks to it.
Existing output, dirty state, shallow history and unapproved-origin refusals remain.
The Git helper continues to use an argument list without a shell and a bounded
per-command timeout. No public application API changed.

The validated T01 fixture uses
`(repo / "LICENSE").write_bytes(b"MIT License\nCopyright Test\n")`.
The exact output assertion remains intact. R01 has negative subdirectory-write
and positive external-export tests; T01 has an exact-byte assertion and a separate
missing-license refusal test. `inspect_python` still parses syntax without importing
app startup; `main` still reports failures nonzero. These corrections were already
implemented in earlier STEP_02 work; this cycle revalidated them rather than
claiming duplicate source changes. No new functions, classes or tests were needed.

### E. Import and Dependency Analysis

No application/tool/test imports, dependency manifests, lockfiles or installed
package versions changed. The corrections use existing `Path`, Git helper and
standard byte IO. Their complete import rationale remains in section 5.
The temporary verification driver uses standard-library `pathlib`, `hashlib`,
`json`, `subprocess`, `tempfile`, `time` and `datetime` to manage owned scratch
directories, invoke commands, record timing and verify artifacts. It is not a new
runtime or training dependency. pytest, Ruff and mypy are the existing uv tools.

### F. File-by-File Changes

| Path | Work in this cycle |
|---|---|
| This STEP_02 report | Appended A–O record and latest-status note; earlier sections/logs retained |
| `docs/upstream/FAILURE_INVENTORY.md` | New structured two-issue inventory with counting/scope definitions |
| `docs/implementation/PROGRESS.md` | Updated latest revalidation evidence; still two DONE, 43 NOT STARTED |
| `docs/upstream/evidence/step02-correction-preflight.json` | New preflight hashes proving starting state and unchanged source |
| `docs/upstream/evidence/step02-correction-validation.json` | New exact commands, two expected negative runs, current results/timings |
| `docs/upstream/evidence/step02-correction-equivalence.json` | New real-upstream reproduction and current source hashes |
| `docs/upstream/evidence/step02-correction-git-comparison.json` | New actual Git status/diff comparison |
| `docs/upstream/evidence/step02-correction-summary.json` | New current verdict, issue counts and quality-gate evidence |
| `docs/upstream/evidence/step02-correction-documentation-checks.json` | New section/question/link/hash verification |
| `docs/upstream/evidence/step02-delivery-inventory-before-correction.json` | Preserved prior inventory as historical evidence |
| `docs/upstream/evidence/step02-delivery-inventory.json` | Refreshed current per-file sizes/hashes; self-excluded |

No source, CI, requirements or prior raw execution JSON modified; no files deleted
or renamed. The [current inventory](../upstream/evidence/step02-delivery-inventory.json)
lists every delivered path individually. The temporary validation scripts are
execution helpers outside the repository, not application deliverables.

### G. Original vs Improved Repository

Original upstream is pinned to `fed4b610742c1337147281fcec8f2cdcc0a79be5`.
Working HEAD remains `a37e4634af1d2947fc3c548d54e62bda0b0daf89`. Upstream has no
standalone provenance tool or these fixture tests; STEP_02 introduced them. R01
was introduced in that new tool, not in the original call-analysis application.
T01 was confined to new synthetic test setup. The fixes preserve original
Gradio/LangGraph/SQLite/scoring/security behavior.

The actual [Git comparison](../upstream/evidence/step02-correction-git-comparison.json)
distinguishes HEAD-relative prior tracked STEP_01 changes from all inherited
upstream differences. New untracked STEP_02 files do not appear in ordinary
`git diff`; their contents are bound by the current inventory. All 87 archived
upstream blob hashes and all 99 supplied specification hashes are checked again.
The MIT text and original attribution remain; no project history was rewritten.

### H. Architecture Impact

No production component interaction changed. The development tool reads Git blobs,
builds JSON/tree/AST evidence and writes a new external archive. Root normalization
adds one read-only query at its existing boundary. The fixture correction changes
only synthetic bytes. No FastAPI/React/Redis/PostgreSQL/training component is
implemented by this work. Inference and training remain future independent
concerns. Baseline UI source evidence is unchanged and no frontend was modified.

### I. Tests and Validation

Actual commands, stdout/stderr, exit codes, selected/deselected counts, elapsed
times and working locations are saved in
[validation JSON](../upstream/evidence/step02-correction-validation.json).
Python commands use `.venv/Scripts/python.exe` from the existing uv environment.

| Check | Actual result |
|---|---|
| Isolated reversal of R01; selected subdirectory guard case | Expected exit 1; 1 failed, 9 deselected in 0.66 s; `DID NOT RAISE ValueError` |
| Isolated reversal of T01; selected exact-license case | Expected exit 1; 1 failed, 9 deselected in 0.74 s; CRLF/LF assertion mismatch |
| `pytest tests/unit/test_repository_fingerprint.py -q --tb=short` | Exit 0; 10 passed in 3.78 s; 0 failed/skipped |
| `pytest tests/ -q --tb=short` | Exit 0; 135 passed in 21.26 s; 0 failed/skipped |
| `ruff check src/ tests/ app.py scripts/fingerprint_repository.py` | Exit 0; all checks passed |
| `ruff format --check src/ tests/ app.py scripts/fingerprint_repository.py` | Exit 0; 59 files already formatted |
| `mypy scripts/fingerprint_repository.py` | Exit 0; no issues in 1 file |
| `mypy tests/unit/test_repository_fingerprint.py --follow-imports=skip --allow-untyped-decorators` | Exit 0; scoped test check of 1 file |
| `compileall -q scripts/fingerprint_repository.py tests/unit/test_repository_fingerprint.py` | Exit 0 |
| `uv pip check --python .venv/Scripts/python.exe` | Exit 0; 127 installed packages compatible |
| `git diff --check` | Exit 0 |
| Baseline porcelain status / `git fsck --full` | Both exit 0; clean / no integrity errors |
| Corrected tool, real upstream `src/` → temporary external archive | Exit 0; 87 files, 33 source modules; manifest matches except capture time, symbols/tree/source/license match |

The 135 passing cases include original unit/security/integration tests, 12 STEP_01
diagnostic tests and 10 STEP_02 provenance tests. Two intentionally failing
reversal runs are not part of that 135/135 current-code result and are not hidden.
The old 113 clean-upstream, 133 initial and 135 review runs remain separate history.
Existing pytest-asyncio loop-scope warnings remain visible. Full app mypy remains
historically FAIL; these scoped passes do not replace it, and it was not rerun
without application changes. Remote CI, browser/UI runtime, new platform services
and real neural-model evaluation: **NOT EXECUTED**, outside this step and requiring
later setup/implementation. No relevant available check was disabled.

### J. Performance and ML Metrics

One fresh current full suite: 135/135 passed = 100%, 21.26 s pytest duration,
23.18 s process wall time. One focused run: 10 passed in 3.78 s. One real export:
87 tracked files, 33 source modules, 3.18 s process wall time. These are workstation
observations, not latency distributions or evidence of an optimization. No fair
before/after speed benchmark was conducted; tests/workstation load differ between
historical runs. Baseline and exported source counts agree; original tree has 56
Python files including helpers/initializers, not 56 executable features.

WER, CER, DER, F1, real ASR/LLM latency, throughput, peak inference VRAM and learning
improvement: **Not measured**. No checkpoint, dataset split, gradients or model
promotion was used. No reference screenshot number is a project metric.

### K. Security Analysis

R01's checkout-write boundary is protected for root and nested inputs; existing
output, dirty-state, origin, shallow-history and missing-license refusals still
pass. Source parsing does not execute upstream startup. No auth/RBAC/tenant/SQL/
upload/inference/deployment boundary was changed, so those capabilities are not
newly claimed. Existing security tests pass within the combined suite. The fixture
uses synthetic source/license and temporary local Git commits, not customer audio.

Saved command evidence redacts the user-profile prefix. No credentials, ignored
`.env`, private recordings or datasets were read for this cycle. Temporary reversals
alter only owned scratch copies; real project and baseline code remain unchanged.
No containers/services were started/stopped/reconfigured. No dependency vulnerability
audit was rerun, and Git hashes/fsck are integrity checks, not full security certification.
Known upstream raw cache, audit mutability and encryption uncertainty remain explicit.

### L. Concepts Explained

The repository root is the directory owning a checkout, while a caller can start
from any subdirectory. A safe write boundary must use the same root that Git uses;
otherwise a path can be outside the caller's folder yet inside protected source.
For example, `repo/archive` is not below `repo/src`, but is still below `repo`.

Text IO can transform newlines; byte IO preserves a specified payload. A test that
expects LF should create LF bytes rather than assume platform defaults. Controlled
reversal means undoing one fix in a disposable copy to check that the regression
test detects it. A passing test plus a failing reversal is stronger evidence than
a test that never detects the bug. Expected negative runs must remain distinguishable
from a failing current implementation. A scoped type check covers its named file,
not every module/dependency in the application.

### M. Questions and Answers

#### Q1. Which step is being corrected, and is it currently failing?
STEP_02 is the target because it is the latest completed step. It entered with
PASS WITH LIMITATIONS after R01 had already been corrected. This cycle verifies
that correction and the earlier T01 fixture fix; it does not invent an active
failed gate or count the same fix as new engineering work.

#### Q2. Why did R01 happen?
The initial check compared the destination with the supplied folder. Git queries
still operated on the full checkout when that folder was `src/`. Normalizing to
Git's actual root makes the write guard and inspected source refer to the same
protected tree, closing the inconsistency without changing the tool's CLI.

#### Q3. How was the root cause verified rather than guessed?
The original failing regression is retained, and a fresh isolated copy removes
only the root-normalization block. Its refusal test fails with the expected
`DID NOT RAISE` message. The current tool passes that case and exports from an
actual upstream subdirectory to a safe external destination.

#### Q4. Why was normalization chosen over rejecting all subdirectories?
Subdirectory invocation is normal Git behavior and can remain useful. Root
normalization preserves it while enforcing the full boundary. Rejecting all
subdirectories would avoid the narrow issue but unnecessarily restrict legitimate
external exports; a positive regression case covers that compatibility decision.

#### Q5. Was T01 fixed by weakening the assertion?
No. The oracle still requires the exact synthetic license bytes. The fixture
changed from text writing to byte writing so its committed payload matches that
oracle on Windows. A reversal restores the text writer and reproduces the CRLF
mismatch, while the archive's byte-copy implementation remains unchanged.

#### Q6. Were new imports or packages required?
No. Root resolution uses the existing Git helper and `Path`; fixture byte writing
is already built into pathlib. Existing pytest/Ruff/mypy tools provide validation.
The temporary driver's standard-library imports are execution utilities, not new
application dependencies or training requirements.

#### Q7. What changed relative to upstream?
Upstream's original call-analysis code is preserved. STEP_02 adds the separate
provenance script, fixtures, source inventory and documentation. Its own earlier
write-boundary defect was fixed without modifying Gradio, graph agents, QA weights,
database schema or original security controls. No upstream functionality was replaced.

#### Q8. How are historical and fresh failures distinguished?
Original logs remain under their initial/review filenames. New temporary reversal
rows have explicit scenario names and expected exit 1. Current-code test rows use
the real workspace and exit 0. Reporting both avoids either hiding failure evidence
or wrongly describing expected negative tests as a current regression.

#### Q9. What does the end-to-end check prove?
The current CLI read the real pinned upstream `src/` input and produced a new
external archive. Its manifest, symbols, tree, source evidence and license match
the retained baseline except capture time. This validates the provenance workflow,
not credential-backed audio analysis, neural quality or production deployment.

#### Q10. Was performance improved?
No controlled optimization benchmark was run. The tool adds one bounded read-only
Git query for safety; the current real export took 3.18 s on this workstation.
Differences from earlier one-off timings do not establish a speedup or regression,
and no percentile, model-latency or GPU-memory metric is inferred from them.

#### Q11. Why does full-project typing remain unresolved?
The original app has dependency/stub and source annotation issues documented in
STEP_01. STEP_02 changes no application typing, and a pass for the development
tool/test file cannot make `mypy src/` green. Its later remediation needs a scoped
dependency/source plan; no ignores or heavyweight installs were added here.

#### Q12. How can this failure class be prevented in later steps?
Identify canonical resource boundaries before validating user paths, and test both
root and nested invocation. Define exact byte fixtures when serialization matters.
Keep refusal and successful-use tests together, verify them against real local
collaborators, preserve failed evidence and avoid equating a narrow pass with
whole-platform readiness. These principles carry into STEP_03 review inputs.

### N. Remaining Problems

No active STEP_02 code/test failure or unmet diagnostic/provenance gate remains.
Existing project-wide full mypy failure, absent host FFmpeg/editor launchers and
earlier low-RAM observations remain unresolved/unrefreshed; no readiness claim for
models follows from provenance passing. Existing async fixture-loop warnings remain.
Raw transcript caching, ordinary audit mutability, unverified SQLCipher encryption
and Windows temp lifecycle are upstream findings for later scoped work.

The archive has no transactional publish or checkout lock; interrupted writes can
leave a partial external directory. A dedicated idle baseline and inspection/new
destination remain necessary. Per-command timeouts are not a total workflow deadline.
Remote CI, UI screenshots/accessibility and real model/runtime performance were
not executed. No frontend changed; STEP_02's permitted source-evidence option
remains valid, while future frontend work must use the approved Commercially
reference and actual screenshots. No three-approach correction limit was exceeded.

### O. Final Quality Verdict

**PASS WITH LIMITATIONS.** Two historical code/test failures reproduced in isolated
controlled reversals and their existing corrections revalidated; zero new active
failures and zero unresolved in-scope failures. All 135 current tests pass and real
upstream provenance reproduces. No additional source edits were justified.
The appended documentation is supported by execution, not used to conceal a fail.

Current decision: [correction summary](../upstream/evidence/step02-correction-summary.json).
Documentation checks: [validation record](../upstream/evidence/step02-correction-documentation-checks.json).
Next eligible step remains STEP_03; it was not started. No commit, push, merge,
deployment or timestamp adjustment occurred.
