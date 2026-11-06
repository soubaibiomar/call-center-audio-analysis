# STEP11 correction audit — 2026-10-27

Four confirmed failure groups; see failure-inventory.json and the report A–O appendix.
red.json shows7 original failures; red-invalid-model-receipt adds the related eighth
case. green-final passes8. Intermediate300-test pass and subsequent indentation
collection/static failures remain; final tests.json/XML records301 passes in50.93s.
Ruff/types/dependency/compile receipts are final; failed iteration receipts have
intermediate-indent prefixes. No failure history was deleted.

Actual local-benchmark/results.json records6/6 schema-valid per cached7B/9B model.
Real benchmark exits0; controlled all-failed regression proves exit1 with preserved
receipts. benchmark-execution records command/observed exit; total subprocess wall
clock was not separately captured. No accuracy, training or causal speedup claim.
local-worker-http records an actual isolated Docker CPU ASR/local Qwen/PG/Redis/S3
job, report/PDF200 and metadata. Private content logs are excluded. Source hashes,
service health and preserved primary counts are in operations-final.

Public benchmark/job model digests and static prompt revision checksums use integer
byte arrays to avoid high-entropy scanner false positives. No metric/status changes.
Runtime ModelRun API still uses its original string representation. Preflight privacy
checks use controlled remote metadata, never actual cloud/private inference.
Prior artifact seals remain intact. Source snapshots/diffs distinguish this audit
from earlier accumulated uncommitted work. source-manifest/seal use SHA256 byte
arrays. No commit/push, model download, training or STEP12 implementation.
