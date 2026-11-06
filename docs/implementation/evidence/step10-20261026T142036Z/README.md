# STEP10 execution evidence

Captured2026-10-26. See the matching full implementation report.

- tests.json/tests.xml: fresh full256-case pass;12 worker cases enumerated in test-metrics.json.
- ruff/format/mypy/dependencies/compile/hardcoded-keys/hooks JSON: exact commands, exits, output.
- real-worker-http.json: real loopback HTTP202 -> actual Docker CPU worker, cached tiny
  Whisper and configured hosted provider; ephemeral fixture identity, not a real IdP.
  Duplicate same key returned one job; report/PDF200. Provider logs remain private.
- coordination-benchmark.json:12 synthetic-graph jobs using real S3/Redis/PG; one
  deliberately injected failed attempt. NOT neural/production throughput. Raw timings retained.
- migration-upgrade.json: additive primary/test migration and private backup hash/size.
- fresh-migration.json: fresh0003 schema, empty full downgrade/upgrade, metadata check and RLS.
- service-restart.json: authenticated Redis AOF marker and verified S3 bytes retained.
- operational-checks.json: original primary counts, default IdP fail-closed behavior,
  S3 BadDigest rejection and anonymous object GET403.
- bootstrap-revalidation.json: actual Windows byte-safe storage provisioning; existing
  private credential/config files unchanged. Earlier PowerShell text-pipe CRLF problem is
  documented in the report rather than hidden as a successful command.
- containers.jsonl, versions.json: final live services and actual version receipt.
- git-stat/name-status/status: accumulated tracked/untracked work, not an isolated commit.
- source-manifest.json/source-imports.json: final35 step-specific source/artifact hashes
  and parsed imports. Source hashes describe this capture, not future modifications.
- previous-preflight-report.md: historical blocked STEP10 report preserved.
- preflight.json: early in-turn source snapshot after initial scaffolding, explicitly
  distinguished from a pristine pre-step baseline.

No key/password/token/private SQL URL/transcript/audio bytes are included here.
Backups, private configuration, helper scripts and provider output remain ignored
under .local/. Named data volumes and the original four reports were preserved.
The one-off model verification container was stopped/removed after saving private
logs; normal Gradio, API, CPU worker, PG, Redis and S3 remain local. GPU is opt-in
and unverified; default protected API access remains503 without real IdP config.

seal.json hashes every file in this directory except itself. STEP09 original and
correction evidence are preserved separately, without replacing failed-test history.
