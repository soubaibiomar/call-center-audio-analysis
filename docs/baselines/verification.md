# STEP_05 verification baseline

Date: 2026-10-24; Windows 11, uv Python 3.12.15. Baseline source is the clean
original `fed4b610742c1337147281fcec8f2cdcc0a79be5`; working HEAD is
`a37e4634af1d2947fc3c548d54e62bda0b0daf89` plus documented uncommitted work.
This records executed checks, not a claim that every tool passes.

| Check | Working project | Original clean clone | Classification |
|---|---|---|---|
| Collection | 145 collected in 0.93 s | Original 113 executed below | Four added development-test modules supply 32 extra cases |
| Unit/security | 141 passed in 20.41 s | Included in 113 total original cases | PASS, no failed/skipped cases |
| Integration | 4 passed in 0.95 s | Included in 113 total original cases | PASS, mocked model/provider boundaries |
| Complete original suite | Current partitions above total 145 | 113 passed in 10.26 s | Source-preservation regression comparison; no live-model claim |
| Ruff lint | Exit 0, no violations | Exit 1, two UP038 findings | Original style issue already corrected in STEP_01; no new regression |
| Ruff format | Exit 0, 63 formatted files | Exit 1, three files need formatting / 53 formatted | Original formatting debt already corrected in STEP_01 |
| Full `mypy src/` | Exit 2, six errors in three files, abort | Exit 2, same initial six errors / abort | Inherited typing/dependency/environment limitation; NOT PASS |
| `git diff --check` | Exit 0 | Clean clone status empty | PASS; no source fix or file mutation in this step |

## Immutable evidence

[Command log](evidence/step05-20261024/commands.json) records exact argument arrays,
working-tree identities, exit codes, process durations and sanitized stdout/stderr.
[Seal](evidence/step05-20261024/seal.json) records its SHA-256. These files are not
overwritten by later checks: a later run gets a new capture. No test name, failure
trace or skipped result is silently dropped. The two current test partitions
execute disjoint directories, so 141 + 4 = 145 executed cases, zero failed/skipped.

## Failure categories

- **M01 — P2, inherited static-analysis blocker:** missing ReportLab stubs,
  faster-whisper lacking typed-package markers, absent optional torch typing,
  and NumPy stubs using Python 3.12 syntax while mypy targets 3.11. The first six
  errors stop analysis; this is not the total debt. A previous diagnostic using
  a 3.12 target exposed more issues; it is not repeated or represented as a fix.
- **L01 — P3, original-only lint:** two builtin tuple `isinstance` guards violate
  configured UP038. Current equivalents were corrected/validated in STEP_01.
- **F01 — P3, original-only layout:** three original files differ from configured
  formatting. Current counterparts already pass after STEP_01; clone left intact.
- **W01 — warning:** unset pytest-asyncio loop scope emits a deprecation warning.
  Kept visible. No skip/ignore was added to manufacture a clean baseline.

No new current-step code failure confirmed. No provider credentials, model weights,
private customer audio, containers or public servers were accessed. Real inference
is not covered by mocked integration tests. Full typing is unresolved and must be
handled in a separately scoped dependency/source plan without blanket ignores.


## Requested STEP_05 re-execution

Original baseline table/log/seal above are unchanged. The separate run at
2026-10-24T19:46Z passed 145 current tests (20.91 s) and 113 upstream tests
(10.27 s). Current Ruff passes; both full mypy checks still fail with six initial
errors before abort. See [report section 15](../implementation/STEP_05_run_original_tests_and_static_checks_REPORT.md)
and [fresh commands](evidence/step05-review-20261024T194612Z/commands.json).
STEP_06 remains blocked by private credential readiness.
