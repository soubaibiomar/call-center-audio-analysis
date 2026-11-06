# STEP11 execution evidence — 2026-10-27

Read the STEP11 report for acceptance mapping, implementation and limitations.
Final tests.json/XML:293 passed, no failures/skips. focused-final:17 cases.
Initial missing-module gap and stale-OpenAPI failure receipts are retained.
local-benchmark-final/results.json: actual cached7B/9B inference,6/6 valid each;
first benchmark partials retain the9B120s timeout. Output bodies are hashes only.
Benchmark model digests and static prompt revision hashes are encoded as byte
arrays in public evidence; see evidence-normalization.json. A known synthetic
userinfo URI is normalized only in historical JUnit testcase labels. No actual
credential was detected; no secret detection rule was disabled.
local-worker-http.json proves CPU ASR → local Ollama → PG/Redis/S3 → HTTP/PDF
with synthetic test identity and a bundled consented sample. Provider logs remain
private. This is not a production IdP, quality/accuracy or concurrency benchmark.
operations-final records reviewed source equality, health and preserved primary
counts. build receipts use verified local dependency bases plus current source,
not a fresh registry-backed dependency rebuild. Prior seals remain intact.
source-manifest/seal use SHA256 byte arrays; source snapshots/diffs, imports,
Git summaries and raw check receipts support review. No commit/push or STEP12 work.
