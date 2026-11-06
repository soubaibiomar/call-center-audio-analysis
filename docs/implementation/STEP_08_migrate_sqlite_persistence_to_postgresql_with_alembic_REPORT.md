# STEP_08 — SQLite to PostgreSQL with Alembic

> **DONE — PASS WITH LIMITATIONS.** Executed2026-10-25, Africa/Casablanca.
> Correction review2026-10-25:3 confirmed failure groups corrected;198 tests pass.
> Earlier implementation measurements below remain historical; see the A–O appendix.
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

# Failure Analysis and Correction Report

### A. Executive Summary

STEP_08 is the latest implemented step. Its prior verdict was PASS WITH LIMITATIONS,
not an active migration failure. The attached diagnosis request prompted fresh
edge-case tests rather than treating future steps as broken functionality.
Five tests reproduced **three confirmed failure groups**, all now corrected:
SQLite connection ownership, WAL-inconsistent snapshot checksums, and accepting
runtime-role memberships despite NOINHERIT. No migration or model checkpoint changed.

Fresh full suite: **198 passed in24.33s**, zero failed/skipped. Strict mypy checks46
application files; Ruff/format/hooks/secret checks pass. Fresh isolated upgrade/down/
upgrade, valid import/query/replay and normal role provisioning pass. Replaying the
original snapshot against the primary database leaves its four reports unchanged.
The rebuilt app and PostgreSQL are healthy. No STEP_09 advancement or commit/push.

New evidence is [step08-correction-20261025T082228Z](evidence/step08-correction-20261025T082228Z/).
The earlier37 sealed artifacts were verified before work; original report/source
copies, red tests and the intermediate WAL-export failure remain preserved there.
No customer/transcript content or credentials are published in this evidence.

### B. Failure Inventory

| ID | Failure | Component | Severity | Reproduction | Root cause | Status |
|---|---|---|---|---|---|---|
| COR08-01 | Backup/import source handles remain open after completion/error | Recovery resource ownership | P2 | Two backup closure assertions and one source-closure expectation fail | sqlite3.Connection's context manager controls transactions, not handle lifetime | Fixed; all three closure regressions pass |
| COR08-02 | Import accepts committed WAL rows absent from the main-file digest | Snapshot identity/replay | P1 | Commit an audit row in WAL; main file SHA unchanged, yet import accepts it | Hashing only the main file did not identify the logical WAL database state | Fixed; reject WAL input, normalize online backup artifact, pin source transaction and recheck streaming digest |
| COR08-03 | Safe-looking runtime role with group membership passes provisioning | Database least privilege | P1 | Membership-bearing role has safe own flags but provisioning does not reject it | NOINHERIT was treated as sufficient without checking explicit SET ROLE memberships | Fixed; reject memberships before any grant changes; actual production runtime membership count0 |

Three groups identified, three corrected, zero unresolved in this inventory.
Five initial failed cases cover those groups, not five independent root causes.
No existing tenant leak or corruption of the primary database was observed.

### C. Root-Cause Analysis

The old backup and import used `with connection` without closing the connection.
Tracked real SQLite connection subclasses show handles still usable/open after
return, including an error path. Python documents that [connection context management
does not close the handle](https://docs.python.org/3.12/library/sqlite3.html#how-to-use-the-connection-context-manager).
Deterministic cleanup matters on Windows where open database handles can interfere
with archive handling; garbage collection is not the ownership contract.

A SQLite WAL database can have committed rows in its sidecar while the main-file
bytes/hash remain unchanged. The regression demonstrates exactly that with synthetic
data. A ledger based only on those bytes could misidentify a changed logical source
as an exact replay. The old importer also did not establish one source read
transaction across all table scans. Exporting a proper standalone snapshot is the
smallest reliable contract; trying to hash two live, changing files is not a snapshot.

PostgreSQL membership with SET permission allows an explicit SET ROLE independently
of automatic inheritance. The test creates isolated synthetic non-login roles,
uses session authorization to demonstrate SET ROLE reaching a CREATEDB group, then
expects provisioning to reject that candidate. It creates no database under the
elevated role and never alters the real runtime role's membership. [PostgreSQL's
membership rules](https://www.postgresql.org/docs/17/role-membership.html) explain the
distinction. Test-only roles/grants are removed after verifying they own no relations.

### D. Code Corrections

`backup_sqlite` now wraps both internally owned connections in contextlib.closing.
After the online backup completes, it commits and changes only the destination
artifact to DELETE journal mode. It checks integrity/counts, exits with both
handles closed, then streams the checksum. The original WAL source is not converted.

`file_checksum` uses existing hashlib.file_digest with an explicitly closed binary
file. It no longer loads the full archive through read_bytes for hashing.
`verified_snapshot` is a typed context manager that opens/owns the read-only source,
begins a read transaction and reads schema to pin it. WAL mode or a WAL sidecar
requires the caller to export a standalone backup first. It yields source/digest
to import_backup, keeps the source transaction open through target work and closes
the source even on replay return or failure. The importer checks the digest again
before sequence adjustment/ledger commit. Existing IDs, field parity, advisory
locking, canonical projection and target rollback semantics remain intact.

`provision_runtime` queries pg_auth_members using the candidate role as a bound
parameter inside its existing transaction. Any membership causes ValueError before
grant changes; it does not silently revoke legitimate administrator configuration.
The actual project28_app remains membership-free and retains its restricted rights.

### E. Import and Dependency Analysis

No package/version/lockfile change. New stdlib imports are collections.abc.Iterator
for the yielded source/digest type and contextlib.closing/contextmanager for
deterministic resource ownership. hashlib was already imported; file_digest is
available within the project's Python3.11+ contract. No global import exception or
typing suppression was added.

Regression tests add stdlib hashlib/secrets/sqlite3 and use existing psycopg/sql,
SQLAlchemy, pytest and local fixtures. Random synthetic role identifiers and the
provisioning argument do not become public credentials. Tests use only the explicitly
named isolated PostgreSQL database; the actual runtime membership is read separately.

### F. File-by-File Changes

| Path | Change |
|---|---|
| services/api/db/legacy_import.py | Closed backup/import ownership, standalone snapshot export/validation and streaming digest |
| services/api/db/admin.py | Reject unexpected role memberships atomically before grants |
| tests/unit/test_database_recovery_edges.py | New two-case success/error resource closure regression |
| tests/integration/test_postgresql_persistence.py | Three new cases for WAL export/import, source closure and membership rejection/SET ROLE proof |
| docs/database/schema.md | Explain handle ownership, standalone artifacts and explicit-role membership limits |
| docs/implementation/PROGRESS.md | Record198-test correction state and preserve ordered handoff |
| This report and new evidence directory | Append A–O record, retain before copies, failures, checks and integrity seal |

Local diagnostic drivers remain ignored under .local. No source file or migration
deleted/renamed, no database reset and no live retention deletion. Only two
production helper modules changed; application/graph/ML/report schema code remains.

### G. Original vs Improved Repository

Pinned upstream has SQLite persistence but no PostgreSQL importer, snapshot ledger
or role-provisioning helper. These defects were introduced in STEP_08's new recovery
surface, not attributed to upstream. Corrections preserve upstream SQLite/report
behavior and the existing PostgreSQL table/JSON contracts. Migration0001_platform
is unchanged. The earlier schema/source provenance and independent113-test upstream
result remain historical evidence, not relabeled as a newly executed baseline.

### H. Architecture Impact

No new service, public endpoint, auth boundary or distributed transaction. Backup
ownership and source-snapshot consistency are enforced inside existing recovery
helpers; target import remains one SQLAlchemy transaction. The owner/inference
privilege split is unchanged but candidate-role validation is stronger. The normal
shared analysis service/call persistence pipeline is untouched.

### I. Tests and Validation

| Fresh check | Result / evidence |
|---|---|
| New edge cases before corrections | **5 failed,13 deselected in1.46s**; red-focused.json |
| Expanded WAL positive-path attempt |1 failed,4 passed: backup API preserved WAL header; wal-backup-correction-attempt.json |
| Same edge cases after final correction | **5 passed,13 deselected in1.00s**; green-focused.json |
| Full pytest with real PostgreSQL URLs | **198 passed in24.33s**, zero failed/skipped; pytest.json, wall26.435s |
| Strict mypy src/services/app | Exit0,46 files; mypy.json |
| Ruff lint and format including migrations/stubs/tests | Exit0; ruff.json / format.json |
| Compile / dependency check / four hooks / explicit secret scan | All exit0; individual command JSONs |
| Fresh isolated upgrade/down/upgrade, provision/import/query/replay | Pass; recovery-and-primary-safety.json |
| Primary snapshot replay and row preservation | Pass; four reports before/after; real runtime memberships0 |
| Rebuilt application/PostgreSQL health and corrected-source hashes | Pass; container-health.json / container-corrected-source-hashes.json |
| Prior implementation evidence seal | All37 artifacts match before review; prior-seal-integrity.json |

The positive WAL export test revealed that SQLite's backup API can copy a WAL-mode
header. Rejecting all WAL-mode inputs initially also rejected that new output;
normalizing only the exported destination fixed the actual workflow. This failed
attempt is retained, not overwritten as a clean first try. Initial long-line/import
layout findings were formatted. No valid test, security check or exception was
disabled. The existing pytest-asyncio loop-scope warning remains advisory.

Commands, arguments, exit codes, timings and stdout/stderr are retained separately.
No fresh hosted-model analysis, frontend build/screenshots, training benchmark or
remote CI ran: those components were unaffected. The earlier real Gradio smoke
and populated restore remain sealed historical evidence. All three STEP_08 gates
still pass; the fresh empty down/import/query validates the corrected recovery path.

### J. Performance and ML Metrics

New measurements are verification durations and source/target parity:198 tests,
fresh three-report snapshot import, exact replay and unchanged four primary reports.
No new inference latency, WER/DER/F1, p95 database benchmark, peak memory/VRAM or
training metric collected. Earlier p95/live-call figures remain historical.
Streaming checksums avoid a whole-file read allocation; two checksum passes add
linear I/O. Its memory/latency benefit was not independently benchmarked.

### K. Security Analysis

Candidate memberships are checked before granting permissions; unsafe candidates
are rejected rather than automatically altered. Synthetic SET ROLE testing leaves
the actual runtime account untouched. Existing RLS, cross-tenant FKs, default-deny,
pool reset, denied DDL/audit mutation/model-promotion tests continue to pass.
The primary account has zero memberships and four reports remain intact.

WAL acceptance can no longer create a ledger based on an incomplete artifact hash.
Source read transactions and deterministic close reduce consistency/resource risks.
Existing private secrets/backups remain ignored; no SQL URL/password/report content
is published. This is not a complete security audit or replacement for STEP_09
authentication. The documented trusted tenant-setting boundary still applies.

### L. Concepts Explained

A transaction manager decides commit/rollback; a resource owner decides when a
handle closes. These are different jobs. A WAL stores committed database changes
outside its main file, so one file's fingerprint may not identify all visible data.
A standalone backup converts that logical state into one reviewable artifact.
NOINHERIT prevents automatic privilege use, whereas SET ROLE is an explicit
membership-based identity switch. Both paths need consideration in least privilege.

### M. Questions and Answers

1. **Was STEP_08 already failing?** Its recorded acceptance gates passed. This review added independent edge tests and reproduced new recovery/provisioning defects instead of changing the prior verdict without evidence.
2. **Why did SQLite handles stay open?** `with connection` commits or rolls back but does not close. Explicit closing now runs on successful return, early replay and exception paths.
3. **Why is the WAL checksum issue real?** The test commits a row while the main-file SHA stays identical. Reading that database includes a row absent from the checksum's identified file state.
4. **Why reject WAL input rather than hash its sidecar?** Two changing files are not a stable artifact. SQLite's backup API already provides a coherent export that can be normalized and fingerprinted.
5. **Did normalization alter the original database?** No. DELETE journal mode is applied only to the newly created backup destination. The live source remains untouched.
6. **Why pin a read transaction?** It keeps table scans on one source snapshot and blocks ordinary rollback-journal writers from committing changes during import. The second digest check guards unexpected artifact replacement/modification before target commit.
7. **Why isn't NOINHERIT sufficient?** A membership may still allow explicit SET ROLE. The test demonstrates the switch to a synthetic CREATEDB group, and the helper now refuses such a candidate.
8. **Why not automatically revoke memberships?** They may reflect deliberate external administration. Refusing before grant changes preserves configuration and makes that authority decision explicit.
9. **Did the fixes require a new migration or dependency?** No. Existing stdlib helpers and a PostgreSQL catalog query suffice. The deployed migration/table contracts remain unchanged.
10. **What establishes no regression?** The full198-case suite, real recovery/import/replay, primary report-count checks, healthy rebuilt containers and original evidence integrity all pass. This does not certify unmeasured scale, UI or ML quality.

### N. Remaining Problems

No unresolved failure remains in this three-group inventory. Existing limitations
remain: manual retention and backup expiry, small-archive/concurrent-cutover scope,
legacy PII/cache policy, trusted tenant context until authenticated endpoints,
production TLS/operational scale, and advisory pytest configuration warning. Partial
failed backup files are retained for review and cannot be overwritten implicitly.
No UI changes occurred; section13's visual N/A and preserved baseline still apply.

### O. Final Quality Verdict

**PASS WITH LIMITATIONS — three confirmed failure groups corrected, zero unresolved.**
All five new regression cases and198 full-suite cases pass. Real snapshot recovery
and the unchanged primary data are verified. STEP_09 remains eligible but NOT STARTED;
no advancement, commit, push or deployment performed during this correction review.
