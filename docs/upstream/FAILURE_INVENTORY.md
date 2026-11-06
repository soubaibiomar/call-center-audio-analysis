# STEP_02 failure inventory — diagnosis and revalidation

Date: 2026-10-24, Africa/Casablanca. **PASS WITH LIMITATIONS** for STEP_02.
Two historical code/test failure groups are counted: both were already corrected
before this cycle and are now independently revalidated. **Zero newly discovered
active failures; zero unresolved in-scope failures.** No fresh source patch is
claimed. Existing project-wide typing/tool/privacy limitations are not included
in this STEP_02 failure count and remain unresolved as documented.

| ID | Failure | Component | Severity | Reproduction | Root cause | Status |
|---|---|---|---|---|---|---|
| R01 | Archive could be written inside baseline via subdirectory input | `fingerprint` output boundary | P2 | Isolated old root handling: `pytest ... -k subdirectory_cannot_bypass` → 1 failed, 9 deselected | Caller directory was used as the boundary although Git resolves the repository root | Previously corrected with Git-root normalization; current refusal and external export revalidated |
| T01 | Exact license assertion failed on Windows | Synthetic Git test fixture | P3 | Isolated old text-mode fixture: `pytest ... -k capture_hashes_committed_bytes` → 1 failed, 9 deselected | `write_text` created CRLF while the expected committed payload specified LF | Previously corrected with `write_bytes`; current byte-exact test revalidated |

The failing scenarios were reconstructed in disposable temporary copies of the
current tool/tests by reversing only the corresponding correction. They reproduce
the old behavior; they are not represented as complete historical checkouts. Real
development and baseline files were never reverted. Each reversal selected one
case (nine others deselected), while the final current suite executes all cases.
Raw outputs, exit statuses and runtimes are retained in
[correction validation](evidence/step02-correction-validation.json).
Original failed runs remain in [first execution](evidence/step02-validation-first-run.json)
and [quality-review reproduction](evidence/step02-review-reproduction.json).

The initial formatting/line-length housekeeping is recorded in the original report;
fresh strict Ruff checks pass. It is not counted as an additional active code/test
failure. One correction approach was needed for each counted defect in earlier
work; this cycle added no implementation attempt. The three-approach ceiling was
not exceeded. No P0/P1 issue was identified in this scoped work.
