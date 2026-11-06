# STEP_09 execution evidence

Captured 2026-10-25. Read the matching implementation report for scope and limits.

- `tests.json` / `tests.xml`: full local 235-case result; private test connection *file paths* only.
- `api-final.json`: final 37 API cases after annotating a synthetic scanner fixture.
- `test-metrics.json`: exact JUnit case-name selection, 15 denial-focused cases.
- `ruff.json`, `format.json`, `mypy.json`, `dependencies.json`, `compile.json`,
  `hardcoded-keys.json`, `hooks.json`: successful commands and actual output.
- `hooks-initial-fixture-false-positive.json`: initial test-URL scanner rejection;
  inline test-only allowlist resolved it without disabling scanners.
- `upstream-tests.json`: independently executed pinned original suite (113 passes).
- `live-http.json`: actual loopback Uvicorn HTTP checks, raw p95 samples and real
  bundled sample inference. Ephemeral signed fixture identity, **not a real IdP**.
  Keys/tokens, transcript/provider logs and SQL credentials are excluded.
- `migration.json`: separate fresh database upgrade, empty down/up and populated
  refusal. Disposable databases were retained; primary was not downgraded.
- `docker-regression.json`: final build/up, Gradio config, primary counts and RLS.
- `prior-integrity.json`: 37 original and 25 correction STEP_08 evidence files intact.
- `git-stat.txt`, `git-name-status.txt`, `git-status.txt`: accumulated working-tree
  snapshot, not a STEP_09-only commit. Earlier uncommitted work is preserved.
- `source-manifest.json`, `source-imports.json`, `versions.json`: final relevant
  source hashes, exact parsed imports and installed dependency versions.
- `previous-preflight-report.md`: historical blocked report before this execution.

`seal.json` hashes every file in this evidence directory except itself. Source
manifest entries are repository-relative and describe this capture, not future
steps. Live test server stopped afterward; primary Gradio/PostgreSQL remain local.
Private pre-migration archive and test helper scripts remain ignored in `.local/`.

Initial full-regression observation was 219 passed / 1 failed in 29.05s: the new
identity migration correctly refused downgrade but used exception wording that
broke the older safety-test regex. The final fresh suite passed after correction.
Initial live evidence capture failed on a trailing newline in the evidence-path
pointer; published metrics come only from the complete successful repeat.
