# STEP_08 — SQLite to PostgreSQL with Alembic

> **DONE — PASS WITH LIMITATIONS.** Executed2026-10-25, Africa/Casablanca.
> Owner: Platform. Windows11/PowerShell, uv Python3.12.15, Docker Linux,
> PostgreSQL17.11; CPU-only validation, no training/GPU experiment.
> Branch: feature/project28-foundation; HEAD a37e4634af1d2947fc3c548d54e62bda0b0daf89
> plus preserved, uncommitted work. Upstream: fed4b610742c1337147281fcec8f2cdcc0a79be5.
> [Complete prompt](../../prompts/STEP_08_migrate_sqlite_persistence_to_postgresql_with_alembic_PROMPT.md),
> [template](../../report_templates/STEP_08_migrate_sqlite_persistence_to_postgresql_with_alembic_REPORT.md).

## 1. Objectives, prerequisites and completed work

Read master/index, complete prompt/template, prior STEP_07 correction evidence,
current architecture and actual models/connections/configuration/report services.
STEP_07 has passed with limitations: full strict typing and Docker errors are fixed.
PostgreSQL was available and its public schema empty. The earlier blocked STEP_08
report is preserved in [previous-blocked-report.md](evidence/step08-20261025T075147Z/previous-blocked-report.md).

Implemented12 PostgreSQL data tables, a reviewable Alembic revision, restricted
runtime role, tenant RLS, transactional legacy import/normalization, retention
operations, typed history/KPI contracts and private URL configuration. Tested empty
upgrade/down/upgrade and populated backup restore before switching the local app.
Imported all3 existing sample reports,3 audit entries and1 cache entry with exact
legacy field/ID parity. The app now uses PostgreSQL through project28_app; its
original SQLite volume and private snapshots remain available.

All three acceptance gates pass. Final suite **193 passed in23.11s**, including18
new cases; independent pinned upstream **113 passed**. Real Gradio analysis added
a fourth persisted PostgreSQL report plus31 normalized segments and valid downloads.
No API/auth server, broker, training execution, object-store transfer or new UI was
claimed. Job/review/model/training tables are real storage, not those future systems.

## 2. Actual upstream versus upgraded implementation

| Surface/symbol | Actual pinned upstream | Current change and compatibility |
|---|---|---|
| src/database/models.py | CallRecord/AuditLogEntry/TranscriptionCache and original fields | Kept unchanged during STEP_08; original SQLite schema remains three tables |
| get_engine/init_db | SQLite path and create_all | Also accepts PostgreSQL URL, sets transaction tenant, verifies Alembic revision; PostgreSQL never auto-creates schema |
| persist_report | One legacy CallRecord commit | PostgreSQL also inserts canonical Call/Segments in that same transaction; SQLite path retains original behavior |
| History/audit/cache | Original ORM queries and serialization | Same callers work under PostgreSQL RLS; original report/summary/QA JSON text retained |
| Schema lifecycle | No Alembic | Frozen0001_platform creates12 tables/indexes/FKs/policies; populated down explicitly refused |
| Ownership | No tenant/user schema | Tenant/user ownership, composite same-tenant FKs, forced RLS and separate runtime privileges |
| New platform entities | No jobs/reviews/model versions/training records | Typed ORM models and constraints exist; no execution or quality improvement implied |
| Recovery/import | No PostgreSQL import/recovery tool | Exclusive online SQLite backup, atomic field-checked import/ledger and tested pg_dump/pg_restore |
| Config/app.py | DB_PATH only | Optional private DATABASE_URL(_FILE); Compose uses runtime secret; explicit SQLite override preserved |

Git stat/name-status were executed and saved in evidence. They describe the entire
mixed working tree, including earlier steps; they are not misrepresented as a
STEP_08-only commit. New/untracked files were inspected directly. The delivered
inventory identifies this step's actual files. No Git history rewrite or commit.

## 3. Files created, modified and preserved

| Path | Action / important interface / purpose |
|---|---|
| services/api/db/__init__.py | New package boundary; no connection on import |
| services/api/db/settings.py | database_url, legacy tenant/user IDs, SCHEMA_REVISION; private configuration without provider bootstrap |
| services/api/db/models.py | PostgreSQL Base and nine platform models plus three tenant-scoped legacy table copies |
| services/api/db/repository.py | store_report, scoped_calls, tenant_metrics, expire_calls, expire_cache; transaction-bound operations |
| services/api/db/contracts.py | CallListItem/TenantMetrics; real fields for future history/KPI/filter/model display |
| services/api/db/admin.py | Explicit provision_runtime and CLI; separate non-owner inference privileges and disabled legacy service identity |
| services/api/db/legacy_import.py | readonly_sqlite, backup_sqlite, import_backup and CLI; backup/import/replay/parity behavior |
| alembic.ini, migrations/env.py, migrations/script.py.mako | Migration configuration, shared-connection transaction support, revision template |
| migrations/versions/0001_platform_tenant_owned_platform_and_legacy_.py | Explicit static upgrade/down/RLS; no dependency on future model definitions |
| src/database/connection.py | PostgreSQL routing, transaction-local scope, migration-version guard; SQLite retained |
| src/utils/config.py, app.py | Optional private URL selection; secret field excluded from dataclass repr |
| src/agents/report.py | Same-transaction PostgreSQL legacy/canonical writes |
| requirements.txt, pyproject.toml, PROJECT28_REQUIREMENTS.lock.txt | Two direct dependencies and actual refreshed environment freeze |
| scripts/check_project_setup.py | Resolve extras such as psycopg[binary] to distribution name for truthful pin checks |
| Dockerfile, compose.local.yml, compose.sqlite.yml | Ship migrations/driver, mount restricted runtime secret, explicit compatibility rollback |
| .env.project28.example, .github/workflows/ci.yml | Safe opt-in URL instructions; migration lint/format scope |
| tests/unit/test_database_configuration.py | Five cases: online backup/overwrite/read-only, two SQLite paths, private URL selection, unsupported backend |
| tests/integration/test_postgresql_persistence.py | Thirteen real PostgreSQL cases: import/replay/parity, abort/collision, RLS/pool/FKs/permissions, retention/holds, metadata and down refusal |
| docs/database/schema.md | Entity/ownership contract, operational commands and recovery/retention limitations |
| This report, progress, architecture/STEP_07 handoff, STEP_09 eligibility note, evidence | Executed results and ordered handoff; previous attempts retained |

Original SQLite models, report schemas, summary/QA weighting, ASR configuration,
security algorithms and visible Gradio controls were preserved. Private generated
URLs/passwords, backups, downloaded reports and local execution drivers are ignored
under .local. Database contents were never added to published evidence.

## 4. Important code, functions, classes and algorithms

The PostgreSQL Base is separate from the SQLite Base. Its platform entities are
Tenant, User, ModelVersion, Call, Segment, Job, Review, TrainingRun and LegacyImport.
The legacy tables are copied into PostgreSQL metadata with tenant_id and policies,
so old ORM callers still see their original columns. Canonical owner/reviewer/call/
model references include tenant_id in composite FKs. Database constraints enforce
positive retention/review versions, ordered segment times, confidence0..1 and QA0..5.
Models expose nullable model/artifact/audio/language metadata rather than invented
values. The exact columns/indexes/relationships are in [schema.md](../database/schema.md).

get_engine accepts legacy paths/SQLite URLs or normalizes postgresql URLs to the
psycopg dialect. Its begin event uses parameterized set_config(..., true), making
scope local to a transaction; session_scope can override a trusted tenant and
still commits/rolls back/closes as before. No scope survives pooled transaction
reuse. init_db checks0001_platform on PostgreSQL and keeps create_all only on SQLite.

The report path's important sequence is:

```python
session.add(record)
if engine.dialect.name == "postgresql":
    session.flush()
    store_report(session, report)
session.commit()
```

Flush establishes the parent legacy row/tenant default before canonical FKs.
store_report checks the provisioned tenant, projects report metadata and expiry,
flushes the Call, then adds ordered Segments. Commit covers both representations;
failure rolls both back. Existing best-effort error handling in process_call is
retained, so the live smoke independently checks actual stored rows rather than
equating export success with persistence. Audit remains a separate transaction.

backup_sqlite exclusively creates its destination, opens the source query-only,
uses SQLite's online backup API and validates integrity. import_backup opens that
snapshot read-only, takes a transaction advisory lock per tenant, checks the exact
checksum ledger and refuses implicit merges. It inserts every legacy field/ID,
reads it back for equality, validates report identity, creates canonical projections,
adjusts sequences and records counts/checksum. Failure aborts the target transaction.
Exact-file replay is a no-op; conflicting global numeric IDs are refused, not remapped.
Rows without full report JSON still retain a basic call projection; invalid embedded
reports are rejected. Original JSON text and naive timestamps remain intact; only
normalized naive timestamps are interpreted UTC for expiry, an explicit limitation.

provision_runtime quotes identifiers/password literals using psycopg.sql and applies
grants atomically. It rejects unsafe preexisting role flags and never silently
rotates passwords. Inference reads tenant/user/import-ledger/model/training metadata;
it cannot promote models or create training metadata. Audit permits SELECT/INSERT;
call/segment/cache/job/review operations receive their scoped grants. The owner
seeds a disabled legacy service identity, not a usable authentication account.

scoped_calls adds tenant/optional owner/status filters and bounded deterministic
history ordering. tenant_metrics computes SQL counts/average, preserving zero QA
scores and NULL for unavailable averages. expire_calls/cache default to dry-run
and require timezone-aware cutoffs. Applying call retention removes eligible
non-held call data and cascades its dependent rows; ephemeral raw cache is purged
separately. No live retention deletion was run and no scheduler is implied.

## 5. Imports, dependencies and technology versions

PostgreSQL17.11 is measured from the running container. SQLAlchemy2.0.41 remains;
**Alembic1.20.1** and **psycopg[binary]3.3.6** are added to both direct manifests.
Their Mako1.4.3 and psycopg-binary3.3.6 packages bring the native environment to135
distributions. All25 direct/dev pins match; no model/provider/audio dependency was
changed. The base Docker image still receives the earlier pinned av18.1 correction.

Actual new imports and their roles:

- models.py: datetime UTC/datetime provide aware creation times; uuid4 supplies IDs;
  Any describes JSON metrics/corrections. SQLAlchemy Boolean/Integer/Float/String/
  Text/DateTime define columns; Column copies legacy ownership; ForeignKey and
  ForeignKeyConstraint enforce references; CheckConstraint/UniqueConstraint/Index
  encode validity and lookup rules; text defines trusted static defaults. JSONB
  stores structured metadata. DeclarativeBase/Mapped/mapped_column build typed ORM
  classes; LegacyBase supplies the unchanged legacy table definitions.
- repository.py: datetime UTC/timedelta compute expiry; select/func/case aggregate
  and filter real rows; delete applies explicit retention. Session is caller-owned.
  Local models/contracts/settings and CallRecord/CallReport connect canonical,
  legacy and typed report boundaries. These operations do not initialize a model.
- legacy_import.py: argparse defines CLI; hashlib fingerprints snapshots; json
  emits value-safe counts; sqlite3 performs read-only backup/query; pathlib and
  datetime handle files/legacy timestamps; Any represents heterogeneous raw rows.
  SQLAlchemy Engine/Session/create_engine/select/func/text handle transactional
  inserts, parity, counts and advisory/sequence SQL. Local models/store_report/
  settings and CallReport provide ownership and strict report validation.
- admin.py: os/Path read private configuration; psycopg and sql.SQL/Identifier/
  Literal perform explicit owner-only role/grant operations. Engine/Session and
  local Base/Tenant/User/settings establish schema permissions and legacy identity.
- contracts.py: datetime and Literal express data/provenance; Pydantic BaseModel,
  Field and ConfigDict validate typed nullable display fields and ORM conversion.
- settings/config/connection: os/Path read one private URL input; dataclass field
  hides its repr. Connection/make_url/text and constants provide driver selection,
  bound tenant scope and revision verification. Existing SQLite imports remain.
- migrations: Alembic context/op configure transactional execution and reviewed DDL;
  sqlalchemy/its PostgreSQL dialect describe static types. env.py imports metadata,
  create_engine and the URL reader, without LLM config or application bootstrap.
- tests: existing pytest, uuid/datetime/Path/sqlite3, SQLAlchemy query/session/
  inspection/error types and Alembic command/Config exercise real databases and
  failure paths with synthetic fixtures. No additional test library is required.

The setup diagnostic only strips an extras suffix before looking up a distribution;
it does not relax version equality. Migration use follows [Alembic's shared-connection
pattern](https://alembic.sqlalchemy.org/en/latest/cookbook.html); the PostgreSQL driver
uses [SQLAlchemy's psycopg dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg).

## 6. Concepts explained from first principles

A migration is an ordered, reviewable change to a schema; create_all only creates
missing objects and cannot represent evolution. A transaction commits a complete
unit or discards it: a failed segment FK must not leave half a persisted report.
A primary key identifies a row; an FK requires a referenced row; a composite FK
adds tenant to that requirement, preventing an existing foreign tenant's user from
becoming an owner. An index speeds matching/order operations at a write/storage cost.

JSONB is structured metadata that PostgreSQL can query; retaining legacy JSON text
separately preserves exact serialization. RLS adds a database row predicate to
ordinary queries; table privileges separately govern allowed operations. Neither
authenticates a browser user. A connection pool reuses connections, which is why
tenant settings must end with the transaction. A checksum ledger makes the same
snapshot's import repeatable without duplicate rows. A backup restore is stronger
evidence than merely observing a backup file exists.

## 7. Data, security, performance and reliability

All12 data tables have forced tenant RLS. The app role owns zero tables and has
no superuser/createdb/createrole/inherit/bypassrls flags. Negative tests establish
cross-tenant write/owner failures, missing-context denial, tenant override reset,
denied DDL, denied audit mutation and denied model promotion. This respects the
inference/training separation: schema metadata is not a training loop. PostgreSQL
documents the [scope and privileged-role limits of RLS](https://www.postgresql.org/docs/17/ddl-rowsecurity.html).

The trusted server must supply scope; unrestricted SQL using the app account can
change its own tenant setting. STEP_09 must authenticate, authorize ownership and
sanitize constraints/errors. This step exposes no public HTTP route. Local URLs
and passwords are ignored/mounted privately; only the runtime URL enters the app.
Backups/downloads contain sample report text and remain ignored, not published.
Database storage/network encryption and production backup access were not certified.

Legacy raw-cache/PII masking and best-effort audit/export behavior remain known
limitations. Retention is explicit/manual; audit archival, backup expiry and future
object-store lifecycle are separate policies. Concurrent cutover and large archives
were not load-tested: quiesce submissions and reconcile final source state first.
The original source row counts still match its snapshot after cutover. No recording
was used for training, no checkpoint downloaded and no neural accuracy claimed.

## 8. Actual tests, execution and acceptance gates

Primary evidence directory: [step08-20261025T075147Z](evidence/step08-20261025T075147Z/).
Each command JSON preserves arguments, cwd, exit status, wall time and stdout/stderr.
PostgreSQL test URL files were explicitly supplied, so no integration case skipped.

| Check | Actual final result |
|---|---|
| python -m pytest tests/ -q --tb=short | **193 passed in23.11s**, zero failed/skipped; wall25.340s |
| Independent clean upstream pytest | **113 passed**, exit0; final exact timing in upstream-regression.json |
| python -m mypy src/ services/ app.py | Exit0; **46 source files** |
| Ruff lint / format-check including migrations/stubs | Exit0;90 files formatted |
| uv pip check / project setup | Exit0;135 compatible distributions and25 matching direct/dev pins |
| compileall / four pre-commit hooks / explicit new-file detect-secrets | All exit0 |
| Isolated Alembic upgrade/down/upgrade |2 upgrades and1 empty downgrade pass |
| Primary empty-schema upgrade and Alembic drift check | Upgrade passes; no new operations detected |
| Backup and import/query/parity/replay |3 reports +3 audit +1 cache preserved; exact replay verified |
| Populated PostgreSQL backup restore |12 tables restored with every field equal in a new DB |
| Populated downgrade negative test | Refused before any drop; revision remains usable |
| Runtime app/PostgreSQL health | Both healthy; runtime role and storage directly queried |
| SQLite rollback config and new-image bootstrap | Merge valid; original SQLite app imports/builds |
| Actual new Gradio request | Legacy and normalized PostgreSQL rows queried; JSON/PDF validate |
| Source/runtime parity |49 source/migration/config file hashes match the running container |

The five unit cases and13 PostgreSQL cases cover the new behavior. Expected
failures remain assertions, not hidden successes. Remote CI and Python3.11 runtime
execution were not run; strict checking targets3.11 locally on3.12.15. Current CI
retains its unit/security selection, while real PostgreSQL integration is explicit
opt-in as documented. The inherited pytest-asyncio loop-scope warning is advisory.

Acceptance: **fresh schema migrates; legacy fixture imports/queries; empty down and
populated backup restore are actually tested. All three gates pass.**

## 9. Analytics, measurements and interpretation

| Metric / definition / sample | Observed value | Interpretation |
|---|---|---|
| Upgrade success count |3/3: isolated fresh/re-upgrade plus primary | Small local success evidence, not production reliability probability |
| Empty downgrade / populated restore |1/1 each | Real distinct recovery exercises; populated down intentionally denied |
| Legacy row parity = equal preserved rows / source rows |7/7 =100%; reports3, audit3, cache1 | Every inserted field/ID compared, not just aggregate counts |
| Derived normalized rows before live smoke |3 calls,93 segments | Projections from real retained reports; not extra source rows |
| History p50/p95, SQLite snapshot |0.4485 /0.5605ms |100 serial queries after5 warmups;3 rows, limit200 |
| Same history p50/p95, PostgreSQL app role |2.9176 /4.9390ms |Same3 rows, warm pool; includes TCP/transaction scope and ORM formatting |
| Fresh Gradio call |4.1157s,1 request,31 segments, QA2.35 |Sample/cache-path smoke, stochastic provider output, not a quality benchmark |
| Fresh report files |JSON13,676bytes; PDF3,261bytes |Actual schema/UTF-8/PDF signature validation |
| Post-smoke persistence |4 legacy report rows; new call1 +segments31 |Source SQLite still3 reports; fresh work persisted only in PostgreSQL |

Query p95 uses sorted sample index ceil(.95*N)-1. These Windows/Docker CPU-first
measurements are tiny warm-data tests; PostgreSQL is slower here and no speedup is
claimed. No scaled p95, concurrent load, WER/DER/F1, peak VRAM or training metrics
measured. Sample SHA992feada7a67a56ee2881e0e2dc6ae8980d3190238be26c58d5b29b323b47989
matches the prior bundled recording; generated QA differs across calls without
proving improvement or regression. Weighted score was independently recomputed.

## 10. Technical questions and detailed answers

1. **Why keep SQLite models?** Existing installations and tests rely on those fields/schema. PostgreSQL uses separate metadata plus compatibility tables so migration does not silently break old files.
2. **Why migrations rather than startup create_all?** The owner can review and execute a fixed change. Restricted application startup checks its revision and cannot mutate schema.
3. **Why preserve both integer IDs and call UUIDs?** Existing history/audit references remain traceable. Import refuses collisions instead of silently rewriting historical identity.
4. **What makes importing atomic?** Legacy inserts, readback equality, canonical projections and the ledger share one target transaction. A validation/FK/collision error rolls them back.
5. **Why is replay based on the exact snapshot hash?** It identifies a known imported artifact. A newly modified file is not assumed equivalent and cannot implicitly merge into populated data.
6. **Does RLS mean authentication is complete?** No. The server must derive tenant identity and permissions. The privileged migration role bypasses RLS, and the shared runtime SQL account is not a browser identity.
7. **Why composite FKs?** A foreign user's ID may exist but belong to another tenant. Including tenant_id enforces that its owner/reference belongs to the same tenant even under privileged inserts.
8. **Why not let inference write model/training records?** That would mix deployment/training authority with ordinary analysis. Inference reads that provenance while trusted owner tooling prepares metadata; no training execution exists yet.
9. **Why keep unknown provenance NULL?** Original reports do not record reliable model versions/language or every caller field. Inventing those values would mislead model lab/history views.
10. **Why not store audio blobs in these tables?** Managed object storage can enforce scoped access and lifecycle without inflating structured transactional storage. This step models its key but does not fake that integration.
11. **What does retention actually do?** Explicit dry-run/apply operations remove expired non-held call data and ephemeral cache with tenant scope. Scheduling, audit archives and object storage cleanup are not claimed implemented.
12. **Can rollback lose newer calls?** Pointing back to the untouched SQLite file hides PostgreSQL-only writes. Stop new submissions, take a current dump/export and reconcile data before switching; the override is not reverse migration.

## 11. Problems, decisions, corrections and limitations

Selected a modular monolith with synchronous SQLAlchemy/psycopg, not new services
or a queue. PostgreSQL-only metadata preserves original SQLite and lets the SQL
layer enforce scope without rewriting every legacy history/cache query. Explicit
migration owner versus inference privileges avoids running the app as superuser.
Initial broad metadata grants were tightened atomically to read-only user/model/
training/import provenance; negative promotion permission is tested.

Initial focused execution had13 passes and1 failure: unrelated synthetic archives
both used numeric ID1 in a shared test DB. The importer now detects collisions
explicitly and refuses remapping; successful independent fixtures use noncolliding
source IDs, and a dedicated collision test verifies other-tenant rows are untouched.
The malformed-report test separately reaches validation and proves rollback.

Docker cp reported a missing snapshot inside /tmp although exec/ls could see it:
that path is tmpfs. Transfer used a checked binary subprocess into an exclusively
created local file; no PowerShell text conversion. The first partial backup folder
was retained. Initial layout/import lint findings were formatted. Extras-aware
readiness lookup was corrected for psycopg[binary]; no check was disabled.

Limitations: seven-row legacy import and small local benchmarks; no concurrent
writer cutover guarantee; global integer/UUID compatibility keys may refuse other
archives; UTC interpretation for naive legacy timestamps; explicit retention only;
limited original PII masking/cache/audit lifecycle; no public identity layer or
object-store lifecycle. Production TLS, external backup handling, peer review and
remote CI remain unverified. These do not fail the scoped STEP_08 acceptance gates.

## 12. Deliverables, evidence and next-step handoff

- [Schema/recovery/operator guide](../database/schema.md).
- [Isolated migrations](evidence/step08-20261025T075147Z/isolated-migrations.json), [actual legacy import](evidence/step08-20261025T075147Z/actual-legacy-import.json), [populated restore](evidence/step08-20261025T075147Z/backup-restore.json).
- [Final tests](evidence/step08-20261025T075147Z/pytest-final.json), [strict typing](evidence/step08-20261025T075147Z/mypy-final.json), [independent upstream](evidence/step08-20261025T075147Z/upstream-regression.json).
- [Query benchmark](evidence/step08-20261025T075147Z/query-benchmark.json), [live PostgreSQL analysis](evidence/step08-20261025T075147Z/live-postgresql-analysis.json).
- [RLS/role/schema delivery](evidence/step08-20261025T075147Z/database-delivery.json), [running-source parity](evidence/step08-20261025T075147Z/container-source-parity.json), [preserved SQLite counts](evidence/step08-20261025T075147Z/sqlite-original-still-preserved.json).
- Final delivery inventory, summary and artifact seal accompany these files.

Private backups are under .local/backups/step08-20261025T075816Z; no database/text
dump is included in public evidence. Empty migration validation and restore used
separate named test DBs, retained for review. No database or important data deleted.
No commit, push, deployment or altered commit timestamp performed.

Checklist: real implementation; all models inspected; three acceptance gates pass;
legacy data preserved; inference role restricted; transactional and tenant failure
tests run; actual metrics retained; limitations disclosed; progress/report updated.
**STEP_09 — typed FastAPI endpoints and authentication boundaries — is next eligible.**
It must establish trusted identity/ownership and safe upload/error contracts using
these database scopes. Model/training metadata mutation must not be handed to the
inference role. Next safe action is that step's prompt; no advancement in this task.

## 13. Approved ERP UI design / visual contract verification

**Not applicable to visual implementation:** no new frontend route, CSS, component,
color token, layout or chart was introduced. The approved primary reference remains
design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png with the existing UI system and
acceptance checklist. Original Gradio is retained as the regression interface;
its dark/purple presentation still differs from the approved neutral/white/green
ERP design and is not certified as the final product UI.

The step-specific backend contract is implemented: CallListItem contains ownership,
status, score, optional model/version/language/department and expiry/hold values;
TenantMetrics derives scoped counts/average. Unknown provenance remains NULL,
review/training metadata defaults are truthful, and no live/learning progress is
fabricated. Shared future AppShell/component requirements remain in the transition
document. The real six-output Gradio analysis and history query worked after storage
cutover. No fresh screenshot or responsive/contrast result is claimed for a new UI;
prior STEP_07 images remain historical baseline evidence only.

**PASS WITH LIMITATIONS — STEP_08 complete; STEP_09 eligible.**
