# STEP_24 — Build timestamped human transcript and QA review

**DONE — PASS WITH LIMITATIONS.** Owner: Platform / Codex. Executed 2026-10-31,
Africa/Casablanca. Windows 11, PowerShell, uv-managed Python 3.12.15, Node 24.18.0,
Chrome and local Docker PostgreSQL. Branch `feature/project28-foundation`;
working HEAD `a37e4634af1d2947fc3c548d54e62bda0b0daf89`; pinned original upstream
`fed4b610742c1337147281fcec8f2cdcc0a79be5`. Changes remain in the working tree.
No commit, push, production migration, model download, inference, training or
promotion occurred. GPU memory/performance was not measured; this step used no
GPU model. This report completes the supplied STEP_24 template's thirteen sections.

## 1. Goal, prerequisites and completed work

Reviewers can correct timestamped words, change Agent/Customer speaker assignments,
flag uncertainty and override the overall QA score with a rationale and supporting
audio interval. Corrections now have a separate draft → submitted → approved or
rejected lifecycle. The original prediction and source record remain unchanged.
Independent approval, authenticated reviewer identity, version checks and audit
snapshots make these corrections inspectable before any training use.

Read the master instructions, STEP_INDEX, complete STEP_24 prompt and matching
report template, STEP_23 report, existing limitations, design system/checklist and
both approved UI images. Inspected the existing report/player, authentication,
PostgreSQL/RLS, emotion review, dataset partition locks, migrations and tests.
STEP_23 supplies the integrated shell and timestamped predictions; STEP_21 supplies
review authorization and shared cohort isolation. Their research/prototype limits
remain explicit. These prerequisites support this annotation step; they do not
establish production readiness or operational ground truth.

Implemented eight HTTP operations over seven additional paths, bringing OpenAPI
from 26 to 33 paths. Added the integrated React review route and isolated local
preview. Executed backend tests, strict checks, component/client tests, fresh
migration checks and real Chrome tests against the production-built interface.
The review does not automatically overwrite reports, recalculate upstream QA
weights, train a model or certify employee performance.

## 2. Actual upstream versus upgraded implementation

| Capability | Original pinned upstream | Before STEP_24 | STEP_24 behavior / exact symbols | Compatibility |
|---|---|---|---|---|
| Analysis UI | `src/ui/tabs/analyze.py::build_analyze_tab`, Gradio displays pipeline results | STEP_23 call detail, playback and immutable transcript | `CallReviewPage`, `/workspace/#/reviews/:callId`, linked from `CallDetailPage` | Original Gradio and standalone emotion UI retained |
| Transcription | `src/agents/transcription.py`, machine `TranscriptionResult` | Read-only timed predictions | `SegmentCorrection`, `call_service.edit`: corrected text, speaker, uncertainty | Original agent and prediction schemas unchanged |
| QA | `src/agents/qa_scoring.py`, machine quality scoring | Read-only report score/evidence | `QAOverride`: separate overall score, rationale, audio range | No change to weighted model score or report exports |
| Corrections | No dedicated normalized human annotation lifecycle in upstream | Emotion labels had separate review, not transcript/QA correction | `CallAnnotation`, `CallAnnotationEvent`, `enroll/edit/decide` | New tables and additive endpoints |
| Persistence | `src/database/models.py::CallRecord` stores report JSON | Tenant-scoped normalized calls and retained source report | Frozen original snapshot plus correction JSONB; immutable-source trigger | No source report UPDATE is performed |
| Audit | Original `src/security/audit.py` logs pipeline events | Existing tenant audit and emotion review history | Per-revision snapshot, actor, role, rationale and playback attestation | Existing audit remains; annotation erasure leaves minimal event |
| Concurrency | No transcript correction revision contract | Existing emotion revision pattern | Row lock plus `expected_revision`; stale writer gets 409 | No silent last-writer-wins behavior |
| Dataset export | No current independently approved transcript manifest | Emotion-only reviewed candidates | `AnnotationDataset`, current permission/expiry/uncertainty gates | No automatic training or audio release |

The original tree and the preceding implementation are distinct baselines.
`git diff --stat` and `git diff --name-status` are saved in
[evidence](evidence/step24-20261031/git-stat-after.txt). They include accumulated
earlier tracked work and omit untracked new source directories. They are **not**
a STEP_24-only diff. [step-files.json](evidence/step24-20261031/step-files.json)
compares pre-step and final SHA-256 fingerprints for the inspected source roots,
identifying 28 changed/new source/config/test files. The explicit inventory below
also includes OpenAPI, CI and documentation outside those roots. No accumulated
earlier change is claimed as work performed in this step.

## 3. Created and modified files

Paths below are repository-relative. No existing source file was deleted.

| File(s) | Change, interface and purpose |
|---|---|
| `services/reviews/call_contracts.py` | New strict input/output DTOs: enrollment, segment correction, QA evidence, decision, source snapshot, view, history and export |
| `services/reviews/call_service.py` | New transaction logic: source registration, cohort reservation, optimistic concurrency, edits, independent decisions, eligibility, current export and erasure |
| `services/api/routes/call_reviews.py` | New authenticated UUID-addressed HTTP adapters and consent/history endpoints; opens tenant-scoped sessions |
| `services/api/db/models.py` | Adds `CallAnnotation` and `CallAnnotationEvent`, tenant/user/source relationships and state constraints |
| `migrations/versions/0005_call_review.py` | New frozen DDL, forced tenant RLS, least-privilege grants, immutable-source/audit triggers and guarded downgrade |
| `services/api/db/settings.py` | Expected schema revision changes to `0005_call_review`; readiness remains fail-closed |
| `services/api/db/admin.py` | Provisioning preserves SELECT/INSERT-only rights for annotation events and shared partition reservations |
| `services/api/app.py` | Registers additive review router inside the existing authenticated API |
| `apps/web/src/features/reviews/CallReviewPage.tsx` | New source registration, local checksum verification, timestamped editor, QA form, decisions, audit/permission/export/erasure UI |
| `apps/web/src/features/reviews/reviews.css` | New responsive green/neutral review layout and form/segment styles |
| `apps/web/src/features/reviews/reviews.test.ts` | Five new client/contract tests for bounded writes, credentials, erasure, conflicts and Unicode/forged-field validation |
| `apps/web/src/app/App.tsx` | Lazy review route, title and safe reconnect destination |
| `apps/web/src/features/calls/CallDetailPage.tsx` | Link from stored report to correction workflow |
| `apps/web/src/features/calls/AudioPlayer.tsx` | Optional selected-file callback and attested-source wording; existing callers retain their prior behavior |
| `apps/web/src/lib/api/client.ts` | Same-origin review read/write allowlists, safe error text, JSON writes and 204 handling |
| `apps/web/src/lib/api/queries.ts` | Optional stable editing query disables focus refresh and avoids unsolicited replacement of drafts |
| `apps/web/scripts/generate-api.mjs` | Adds review contracts and offline validators, explicit Unicode ESM runtime import, shared-reference generation and rejection of unresolved `require()` |
| `apps/web/src/lib/api/generated.ts`, `schema.generated.json`, `validators.generated.mjs`, `validators.generated.d.mts` | Four regenerated artifacts derived from canonical OpenAPI; no handwritten drift |
| `apps/web/package.json`, `tsconfig.workspace.json` | Include new feature in lint and strict type checks; no package dependency changes |
| `docs/api/openapi.json` | Regenerated 33-path contract, including independent correction DTOs |
| `scripts/preview_workspace.py` | Configurable, allowlisted STEP_23/24 ports and private context/source names; isolated loopback test DB guard retained |
| `tests/reviews/conftest.py`, `test_call_reviews.py` | Reuse real RSA identity/PostgreSQL fixtures; 26 new backend cases |
| `tests/api/test_api.py` | Expected public OpenAPI path count updated from 26 to 33; canonical contract regression remains |
| `tests/frontend/call-reviews.mjs` | New real Chrome workflow, source/player checks, exports, conflict/reject/erasure checks, screenshots and axe scans |
| `.github/workflows/ci.yml` | Includes `tests/reviews` in existing disposable PostgreSQL CI test run |
| `docs/development/call-annotation-review.md` | New operator/developer runbook, retention/export and isolated preview instructions |
| This report, `PROGRESS.md`, `CURRENT_LIMITATIONS.md` | Implementation evidence, completion tracker and persistent limitations |
| `docs/implementation/evidence/step24-20261031/` | Test/check logs, fingerprints, migration/bundle/version evidence, synthetic export receipt and screenshots |

Private `.local` URL/context files and disposable harness helpers are execution
materials, not distributable project configuration. They contain no committed
credentials. Existing emotion UI files, original frontend entry/build config and
package lock are unchanged, as verified against the pre-step fingerprints.

## 4. Architecture and entry points

```text
Existing stored call/report (unchanged)
  → administrator source/permission enrollment
  → immutable snapshot + draft correction + revisioned audit event
  → supervisor correction + expected revision
  → submit by editor → decision by different enabled reviewer
  → current approved annotation manifest, if permission/expiry/certainty allow
```

| Method/path, under `/api/v1` | Input → result |
|---|---|
| POST `/calls/{call_id}/reviews` | Admin `CallEnrollment` → 201 `CallReviewView` |
| GET `/calls/{call_id}/review` | Reviewer identity → scoped current view; 404 if absent/expired/hidden evaluation |
| PATCH `/call-reviews/{id}` | `CorrectionInput` plus expected revision → new draft revision |
| POST `/call-reviews/{id}/decisions` | `DecisionInput` → submitted, approved or rejected revision |
| PATCH `/call-reviews/{id}/consent` | Admin `ConsentInput` → audited permission revision |
| GET `/call-reviews/{id}/history` | Reviewer, limit 1–100 → event metadata, newest first |
| GET `/call-review-dataset` | Admin → current eligible manifest, fingerprint and truncation marker |
| DELETE `/call-reviews/{id}?expected_revision=N` | Admin → 204, annotation and copied audit payloads erased |

The source call and tenant form a composite foreign key. Editor, submitter and
approver must belong to that tenant. Events have a unique annotation/revision
constraint. Calls cascade deletion to annotations; annotations cascade to events.
Source snapshots and registered source/cohort metadata cannot be changed by an
UPDATE. Audit events cannot be updated, and runtime grants deny direct deletion.
Parent deletion intentionally allows privacy erasure of copied transcripts.

## 5. Important code, functions and algorithms

**Contracts.** `Strict` forbids extra fields, so a body cannot supply a forged
reviewer identity. `CallEnrollment` accepts a lowercase 64-character SHA-256,
stable conversation/speaker references, explicit source attestation and partition.
Training permission defaults false. `SegmentCorrection` stores a complete indexed
set of 1–500 segments, bounded nonblank text, role and uncertainty. `QAOverride`
validates a finite 1–5 score and strictly increasing finite audio interval;
the service additionally checks its end against the original call duration.
`DecisionInput` requires rationale, positive observed duration and a listening
attestation. `ReviewSnapshot` preserves transcription, QA, model receipts and
finite source duration. Views and exports are separately typed public contracts.

**`enroll`.** Lock the unexpired tenant-owned call; reject duplicate registration.
Parse its stored report and reject missing/invalid timings or more than 500 spans.
Build a separate correction payload. Hash audio/conversation/speaker references,
sort them, acquire transaction-scoped advisory locks in that order, and reserve
the shared `EmotionPartitionKey` rows. A conflicting train/evaluation reservation
returns 409. Save the original JSON and canonical digest, registered source hash,
permission evidence and initial draft; append enrollment audit in the same commit.
The stable sorted lock order reduces deadlock risk between overlapping cohorts.

**`get_review`, `check_revision`, `edit`.** Select only the authenticated tenant's
annotation joined to an unexpired call. Evaluation annotations are hidden from
non-admin reviewers. Mutation reads use `FOR UPDATE`; after obtaining the lock,
compare the saved revision to `expected_revision`. A stale writer gets 409 before
any changes. Verify that segment indices are exactly the original index set,
with no missing/duplicate spans. Reject recognizable PII in corrected transcript
text; redact bounded metadata/rationales. Store the corrected payload, assign the
authenticated editor, clear submitter/approver, reset to draft, increment revision
and append an audit snapshot. Raw `CallRecord.report_json` is never written.

**`decide`.** The submitted checksum must equal the immutable registered source,
and observed duration must be within 0.25 seconds of the source snapshot. Only the
current editor can submit a draft. Approval/rejection requires submitted state and
an actor different from editor/submitter. Each successful transition increments
revision, records authenticated identity and saves the claimed listening evidence.
Out-of-order actions return 409; self-approval returns 403. The database also
rejects an approved row lacking distinct editor/approver identities.

**`fingerprint` and `event`.** Serialize JSON with sorted keys, compact separators
and UTF-8, then SHA-256 the bytes. The event stores correction, state, permission,
actor IDs/role, redacted rationale and playback attestation. Hashes identify exact
snapshots; they are not digital signatures or proof against a database owner.
One transaction commits mutation and audit together, or rolls both back.

**`eligible`, `dataset`, `erase`.** Export only approved, permissioned training
annotations with no uncertain or Unknown-role segments and a currently unexpired
source. Query at most 101 candidates, emit up to 100, and mark truncation. Include
source expiry and model-snapshot checksums; fingerprint the emitted items. Editing,
revocation, rejection, expiry or erasure removes current eligibility. `erase`
checks admin identity/revision even after source expiry, retains a minimal generic
erasure event and removes the annotation plus copied transcript audit history.

**`CallReviewPage`, `Enrollment`, `Editor`, `hashFile`.** Registration hashes a
bounded local file with Web Crypto. The editor preserves an original read-only
column of content and keeps corrections separately in React state. A sequence
guard ignores stale asynchronous hash results after a different file is chosen.
Player-ready events record decoded duration; checksum/duration match and explicit
listening confirmation enable decisions. Timestamp buttons use existing `safeSeek`
to clamp playback. QA evidence links seek to its supporting start. Unsaved changes
block decisions and are visibly marked. A failed save preserves local input.
Explicit refresh discards/reloads drafts; focus refetch is disabled. Saving resets
listening confirmation so a later decision concerns the newly saved revision.

**`sendResource` and generation.** Only allowlisted relative review paths receive
the in-memory bearer header. Requests omit cookies, refuse redirects, use an
eight-second timeout and show fixed error text. There is no automatic mutation
retry after ambiguous network failure: refresh before trying again. Offline Ajv
generates standalone schema validators, including an explicit browser-safe Unicode
length helper. Shared references reduce repeated validator code. Generation fails
if a future helper introduces unresolved CommonJS `require()` into browser output.

## 6. Imports and dependencies explained

No new Python or npm package was installed. Recorded runtime versions are in
[versions.json](evidence/step24-20261031/versions.json). Existing package lock and
dependency pins are preserved. Imports below cover each introduced module's
symbols and added integration imports; reused model-column imports need no new
package. Test-only imports do not enter production inference or training.

| Import/module and symbols | Origin/version | Why used / alternative |
|---|---|---|
| `hashlib`, `json` | Python stdlib 3.12.15 | SHA-256 and canonical JSON fingerprints; no external hashing service |
| `datetime.UTC`, `datetime.datetime` | Python stdlib | Timezone-aware audit times; avoids ambiguous local timestamps |
| `typing.Any`, `Literal`, `cast`, `Annotated` | Python stdlib | JSON boundary typing, bounded enums, ORM literal narrowing and annotated constraints; `cast` has no runtime authorization effect |
| `uuid.UUID` | Python stdlib | Typed route/output IDs; malformed route IDs rejected before database use |
| `math` | Python stdlib | Reject non-finite original timestamps |
| `collections.abc.Callable` | Python stdlib | Type the injected engine provider, keeping routing independent of deployment startup |
| `pydantic.Field`, `StringConstraints`, `model_validator` | Pydantic 2.11.3 | Scalar/list bounds, trimmed text, finite values and ordered audio range; avoids handwritten untyped body parsing |
| `fastapi.HTTPException`, `APIRouter`, `Depends`, `Query`, `Response` | FastAPI 0.162.0 | Safe 403/404/409/422 responses, additive routing, verified identity injection, bounded history and empty 204 |
| `sqlalchemy.select`, `func`, `text`; `orm.Session`; `engine.Engine` | SQLAlchemy 2.0.41 | Scoped queries, database time, parameterized advisory locks, transactions and typed engine/session contracts |
| `sqlalchemy as sa`; `alembic.op` | SQLAlchemy 2.0.41 / Alembic 1.20.1 | Frozen schema changes, checked downgrade and RLS/trigger DDL |
| Existing `Mapped`, `mapped_column`, `String`, `JSONB`, `Integer`, `Boolean`, `DateTime`, `UniqueConstraint`, `ForeignKeyConstraint`, `CheckConstraint` | SQLAlchemy, already imported in models | Store annotations/events and enforce tenant/source/user/state relationships; no parallel database introduced |
| `Principal`, `get_identity` | Local API auth modules | Actor comes from verified signed identity and enabled database account |
| `Call`, `CallAnnotation`, `CallAnnotationEvent`, `EmotionPartitionKey` | Local database models | Source/retention join, correction/audit records and shared cohort isolation |
| `require_reviewer` | Local review service | Reuses supervisor/admin policy; avoids a second role system |
| `Strict`, `ConsentInput` | Local emotion review contracts | Reuse forbidden-extra-field base and existing permission-change DTO |
| `AnnotationDataset`, `AnnotationExportItem`, `CallEnrollment`, `CallReviewView`, `CorrectionInput`, `CorrectionPayload`, `DecisionInput`, `ReviewSnapshot`, `SegmentCorrection`, `ReviewEventView` | New local call contracts | Typed registration, mutation, snapshot, history and export boundaries used by service/routes |
| `AuditLogEntry`, `CallRecord`, `CallReport`, `session_scope` | Existing local database/graph modules | Read existing predictions, leave minimal erasure audit, validate report and reuse tenant transaction management |
| `QAScoreResult`, `TranscriptionResult`, `ModelRun` | Existing local graph/model-receipt contracts | Preserve the actual original prediction/provenance without inventing a new inference schema |
| `redact_pii` | Existing local security module | Reject detectable corrected-text PII and redact bounded metadata; not a complete multilingual PII detector |
| `call_service as service`, `call_reviews_router` | New local service/router | Keep HTTP adapters separate from transactional workflow and register it in the existing app |
| `useState`, `useRef`, `useEffect`, `useCallback`, `FormEvent` | React 19.3.1 | Draft state, native player/hash lifecycle, stable ready callback and typed form events; no additional state framework |
| `Link`, `useParams` | React Router 7.18.5 | Shared-shell call navigation and UUID route inputs |
| `useQueryClient` | TanStack React Query 5.105.0 | Mark scoped cached reads stale after successful writes; no browser persistence |
| `useSession`, `ApiError`, `getResource`, `sendResource`, `useApiQuery`, `validateResource` | Existing/extended local frontend modules | Reuse transient identity, safe transport, scoped query lifecycle and generated response validation |
| `AnnotationDataset`, `CallEnrollment`, `CallReviewView`, `CorrectionPayload`, `DecisionInput`, `ReviewEventView` TS types | Generated from OpenAPI | Static frontend contracts, erased at runtime; actual runtime responses still validated |
| `AudioPlayer`, `Heading`, `Pending`, `QueryProblem`, `safeSeek`, `timeLabel`; `./reviews.css` | Local feature/shared modules | Reuse player, states, clamped seeking, time labels and approved visual tokens |
| `unicodeRuntime` from `ajv/dist/runtime/ucs2length.js` | Ajv 8.20.0 | Generated standalone Unicode character-count validation; explicit ESM import fixes browser loading |
| Existing Ajv2020, addFormats, standalone, `_`, fs/crypto generation imports | Existing compiler dependencies | Build-time contract compilation and reproducible artifacts; no browser dynamic code compilation |
| `ThreadPoolExecutor`, `timedelta`, `uuid4`, `pytest`, `DBAPIError`, test fixtures | stdlib / pytest 8.3.5 / SQLAlchemy / local tests | Real concurrent HTTP attempts, expiry/identity isolation and forbidden database operations |
| `afterEach`, `expect`, `it`, `vi`; local client/validator imports | Vitest 5.0.5 | Five isolated client/contract checks and cleanup of fetch mocks |
| Node `createRequire`, `readFile`, `mkdir`, `writeFile`, `fileURLToPath`, `assert/strict`; Playwright `chromium`, AxeBuilder | Node 24.18.0 / Playwright 1.64.1 / axe 4.14.0 | Resolve existing test dependencies, private fixture context, real browser actions, assertions and accessibility/screenshots; never included in application bundle |

Browser-native `crypto.subtle`, File, Blob, URL, FormData and HTMLAudioElement
need no imports or paid provider. There is no training runtime in this workflow.

## 7. Concepts from first principles

**Human in the loop:** a prediction is a machine's proposal; a correction is a
person's separate judgment. An independent reviewer checks that judgment before
it becomes a candidate label. Approval does not prove the judgment is correct.

**Optimistic locking:** a reviewer edits revision 1 while someone else also opens
revision 1. The first save locks the row and commits revision 2. The second saver
then compares 1 against 2 and receives a conflict. This combines a short database
row lock with the client's expected version; it never holds a lock while a person
listens. The concurrency test actually sends two competing requests and observes
exactly one 200 and one 409.

**Annotation provenance:** preserve what was predicted, which source was attested,
who changed it, what revision was reviewed and when permission expires. A hash
answers whether bytes/snapshots match; it does not establish ownership, consent
or that the transcript is a true account of the recording.

**Audit versus erasure:** append-only snapshots support accountability while the
annotation exists. Retaining transcript copies forever conflicts with erasure.
Parent erasure therefore removes those copied payloads and retains a minimal
non-content audit entry. Hashed cohort reservations persist to prevent split leaks.

**Training/evaluation isolation:** training examples teach a model; evaluation
examples measure behavior it did not learn from. Shared speaker/conversation
references must not cross those partitions. Incorrect aliases or unregistered
historical datasets can still defeat this bookkeeping.

## 8. Data, models, security, performance and reliability

All executed corrections used artificial call reports and a four-second silent
WAV. Synthetic text was intentionally paired with silence to test mechanics; it
cannot be considered a real transcription label. Browser credentials were signed
locally and stored only in private test context and tab memory. No real recording,
external provider key, transcript corpus or model was sent to a hosted service.

Security boundaries: fail-closed signed identity; enabled role checks on every
operation; tenant filtering plus forced PostgreSQL RLS; composite foreign keys;
original-source and event UPDATE triggers; append-only event/partition grants;
separate submit/approve identities; no actor override fields; bounded histories,
segments and text; no transcript HTML rendering; fixed error responses; explicit
permission and expiry filtering. Regex PII checks cover recognizable patterns,
not every name/address or multilingual sensitive detail. Review access still
requires an organizational data-handling policy.

Performance: no GPU inference or training. The existing player limits local files
to 25 MiB and 30 minutes, but native decoding can still allocate more memory.
Hashing reads the bounded file into browser memory. Source timings are immutable.
Review/history/export sizes are bounded; cohort locks are acquired in sorted
order; database locks last only for requests. Large-call/concurrent throughput was
not benchmarked. The new route is lazy-loaded; generated validators still add to
the main bundle and its >500 kB warning remains, documented rather than hidden.

Reliability: mutation and audit are one transaction; stale revisions never merge
silently; editing clears approval; user drafts survive a failed save. Downloads
are snapshots and cannot be retroactively revoked. Network timeouts may occur
after a server commit, so refresh before retrying. Existing database upgrades
remain owner-controlled, with readiness requiring revision `0005_call_review`.
Only new isolated test databases were migrated in this execution.

## 9. Executed verification and actual results

Commands executed from the repository in PowerShell; `.venv` is the existing
uv-managed environment. Test URL files refer only to the new local disposable
database. No secret URL or bearer token is included in evidence.

```powershell
$env:PROJECT28_TEST_ADMIN_URL_FILE='.local/step24_test_admin_url'
$env:PROJECT28_TEST_APP_URL_FILE='.local/step24_test_app_url'
.venv/Scripts/python.exe -m pytest tests/unit tests/security tests/api tests/integration tests/workers tests/llm tests/datasets tests/rag tests/emotion tests/reviews -q --tb=short -rs
.venv/Scripts/python.exe -m ruff check src/ services/ tests/ scripts/ stubs/ migrations/ app.py
.venv/Scripts/python.exe -m ruff format --check src/ services/ tests/ scripts/ stubs/ migrations/ app.py
.venv/Scripts/python.exe -m mypy src/ services/ app.py
.venv/Scripts/python.exe -m scripts.export_api_schema
npm --prefix apps/web run api:generate
npm --prefix apps/web run api:check
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
npm --prefix apps/web test
npm --prefix apps/web run build
$env:PROJECT28_REVIEW_WEB_URL='http://127.0.0.1:8786/workspace/'
node tests/frontend/call-reviews.mjs
```

| Check | Actual result | Evidence |
|---|---|---|
| Full backend regression | **484 passed, 2 skipped**, 92.04 s; exit 0 | `backend-tests.txt` |
| New correction backend cases | **26 passed**, initial focused run 11.09 s; all included in final 484 | `tests/reviews/test_call_reviews.py`, final full log |
| Skips | Two existing knowledge/pgvector integration tests lack their separate configured DB; not correction tests | Full log names/reasons |
| Python lint / format / strict types | Pass; **208 formatted files**, **91 typed files** | `ruff.txt`, `format.txt`, `mypy.txt` |
| Frontend unit/client/component | **32 passed in 4 files**, 11.11 s; includes 5 new cases | `frontend-tests.txt` |
| Frontend type/lint/generated-contract | Pass, exit 0 | `frontend-types.txt`, `frontend-lint.txt`, `frontend-contract.txt` |
| Original emotion build + workspace production build | Both pass, exit 0; upstream client-directive and main-size warnings retained | `frontend-build.txt` |
| Correction Chrome production-build workflow | **9 compound scenarios**, **14 screenshots**, **14 axe scans**, **0 violations / page errors**, no horizontal overflow | `browser-results.json`, `browser-run.txt` |
| Existing workspace Chrome regression | **13 compound scenarios**, **9 capability views**, **17 screenshots**, **16 axe scans**, **0 violations / page errors** | `workspace-regression/`, `workspace-regression-run.txt` |
| Migration lifecycle | Fresh head upgrade → empty downgrade to 0004 → head re-upgrade; both new tables force tenant RLS | `migration-check.json` |
| Populated downgrade | Refuses data loss; retained guard verified in final backend regression | Integration log and test |

New tests cover corrected word/speaker/score, raw-report equality and snapshot hash,
audit hash/playback evidence, agent denial, forged actor fields, missing rationale,
wrong checksum/duration, invalid QA ranges, concurrent saves, stale actions,
uncertain/Unknown exclusions, independent approval, rejection, revocation, expired
source/tenant isolation, erasure cascade, evaluation reservation conflicts, source
UPDATE rejection, event UPDATE/DELETE rejection, duplicate indices and PII input.

Browser proof includes selecting and actually playing a local source, seeking QA
evidence to 0.25 s, independent-account approval, downloaded manifest equality,
revocation changing export from two to zero segments, a real stale-save 409,
explicit refresh, agent denial, rejection and erasure with preserved source.

Problems encountered and resolved: an initial browser run exposed Ajv emitting a
CommonJS Unicode helper even though JS component tests passed; explicit ESM import
plus a generation guard fixed it. A populated-downgrade regression expected the
existing error prefix; the new guard was corrected while preserving refusal.
Exact label lookups exposed nested text/select label content; matching explicit
accessible labels were added. React lint caught render-time ref access; duration
now updates from a stable media-ready callback. A test helper initially reused a
same-document navigation and retained the prior identity; fresh-page navigation
now makes role changes explicit. Only final successful runs are counted above.

## 10. Analytics, metrics and benchmark interpretation

| Metric | Baseline → observed | Sample / formula / meaning |
|---|---|---|
| Human annotation time per segment | **Not measured → Not measured** | No timed human study. Formula would be active review seconds / reviewed segments; browser automation is not worker productivity |
| Verified real-world labels | **0 demonstrated → 0 demonstrated** for this step | No real human-reviewed call corpus used; approval mechanics cannot establish semantic truth |
| Synthetic approved export | **0 → 2 → 0** | One two-segment fixture; two after independent synthetic approval, zero after revocation, remaining excluded after edit/reject/erasure |
| Inter-reviewer disagreement | **Not measured → Not measured** | No independent blind labels. Would compare differing labels / jointly labeled segments; approve/reject mechanics are not an agreement study |
| Competing-write outcome | One 200, one 409 | Two simultaneous save attempts with the same expected revision; exactly one correction/audit revision commits |
| Browser accessibility | 0 detected violations in 14 review scans; 0 in 16 regression scans | WCAG2A/AA and WCAG2.1AA axe rules; not a complete assistive-technology certification |
| Workspace refresh smoke latency | p50 **39.06 ms**, p95 **52.46 ms** | 20 sequential warm calls-list refreshes, 3 synthetic reports, real local HTTP/render completion; includes automation overhead, not production/load benchmark |
| Workspace emitted build | STEP_23 **906,665 raw / 250,190 gzip bytes** → **1,018,967 raw / 264,803 gzip bytes** | Sum of 12 emitted files; final `bundle.json`. +112,302 raw / +14,613 gzip bytes, includes new lazy route and validators; no model-performance claim |
| Neural accuracy, model latency, VRAM, employee outcomes | **Not measured** | No model inference, training or employee evaluation occurred |

The synthetic export receipt records the approved state at test time. Later
revocation/erasure makes it stale by design. It is evidence of output formatting
and gating, not a permission to train on that downloaded artifact.

## 11. Technical questions and detailed answers

1. **Why not fine-tune on every edit immediately?** An edit can introduce mistakes,
   PII or incorrect speaker roles. Separate submission, independent approval,
   current training permission, expiry and uncertainty checks reduce those risks.
   They still require real source/label quality control before a training run.
2. **Why combine row locks and expected revisions?** A row lock serializes short
   database mutations. Expected revisions detect that the second request was
   based on stale information after it obtains the lock. Either alone would fail
   to provide this user-visible conflict contract.
3. **Why retain both original JSON and corrected JSON?** The comparison is the
   label's provenance. Overwriting predictions would erase model errors, corrupt
   benchmarks and prevent audit. Original report exports therefore keep reporting
   the original prediction; the annotation manifest carries corrections.
4. **Does a checksum prove the right audio was reviewed?** It proves a selected
   file matches bytes registered earlier. Registration still relies on an
   administrator's source attestation. A signed HTTP request cannot prove actual
   listening, and independent human verification remains necessary.
5. **What happens to approved data after a new edit or revocation?** Editing resets
   state to draft and clears approval. Revocation changes permission and revision.
   Both remove current export eligibility. Already downloaded files remain outside
   server control and must be revalidated/deleted by the consumer.
6. **Can an approver also submit the same revision?** The editor submits; approval
   requires a distinct authenticated user. A role change or forged actor field
   cannot replace this ID check. This is separation of identities, not proof that
   two accounts belong to two different physical people.
7. **Why exclude the whole call if one segment is uncertain?** This conservative
   manifest treats each approved call correction as one review unit. Partial
   segment exports would need additional inclusion/provenance semantics. Current
   behavior avoids silently treating uncertainty as a trusted label.
8. **Why preserve cohort hashes after erasure?** They prevent deleted evaluation
   examples from later being re-enrolled for training. Transcript/audit copies
   are erased; hashed reservations remain. Organizations must document that
   retention choice and reconcile aliases/historical split systems.

## 12. Decisions, limitations and next-step handoff

**Acceptance decision: PASS WITH LIMITATIONS.** All three STEP_24 gates are
implemented and executed: word/speaker/score correction, raw output preservation
and unauthorized-edit denial. No acceptance test remains failing. The two skipped
knowledge integration tests are unrelated existing environment limitations.

Remaining limitations and explicit owners/actions:

| Limitation / risk | Next action |
|---|---|
| No representative independently verified call labels or human annotation productivity/agreement study | Dataset/review owner supplies authorized real calls and a blind review protocol; measure before training/promotion |
| Source association/rights and listening are attestations | Administrator verifies storage provenance, source completeness, rights documents and actual reviewer practice; UI does not claim proof |
| Current shared partition keys cannot identify aliases or import historical external split locks | Reconcile stable speaker/conversation/source IDs before enrolling a real training cohort |
| Downloaded manifests can become stale after revocation, expiry or deletion | Training consumer re-fetches current membership/revision/permission/expiry and resolves matching authorized audio before use |
| Transcript PII detector recognizes patterns only; snapshots may contain sensitive source text | Restrict review access, use vetted data and operational privacy review; do not treat regex detection as complete anonymization |
| Local file decoding has no hard browser memory isolation; 500-span/100-candidate bounds; no capacity benchmark | Use bounded research datasets; evaluate pagination, long calls, native decode isolation and concurrent capacity before deployment |
| Main bundle remains >500 kB and client-directive build warnings persist | Track bundle growth; route is lazy but validator splitting can be a later measured optimization |
| Unsaved drafts can be discarded on navigation; timeouts can be ambiguous | Save before leaving; conflict refresh explicitly discards; re-fetch after ambiguous network failure before retrying |
| Production schema/auth/deployment were not changed | Review backup/migration/role provisioning and real OIDC rollout separately; isolated local credentials are not production access |
| No new ASR/emotion accuracy evidence, training, live transport or model promotion | Preserve all earlier ML, rights, retention and streaming limits in `CURRENT_LIMITATIONS.md` |

Next eligible implementation step is **STEP_25 — Create real browser-to-browser
audio and secure transport**, after reading its own prerequisites. It was not
started. STEP_24 exports annotations only and does not supply live transport.
Use the [review runbook](../development/call-annotation-review.md) to exercise this
step. Next safe verification command: `uv run --no-sync pytest tests/reviews -q`
with the isolated test URL environment variables configured.

Evidence checklist:

- [x] Prompt/master/design and existing implementation inspected.
- [x] New endpoints, correction UI, immutable source, decisions and export executed.
- [x] Real PostgreSQL permissions/RLS/concurrency tests and full regression passed.
- [x] Strict Python/frontend checks and both frontend builds passed.
- [x] Production-build Chrome workflow and existing capability regression passed.
- [x] Actual screenshot/accessibility evidence and synthetic-only metrics recorded.
- [x] Source fingerprints, Git artifacts, versions, migration and bundle evidence saved.
- [x] Limitations, progress and handoff updated; no STEP_25 advancement.

## 13. Approved ERP UI design / visual contract verification

Compared the implemented interface to
`design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png` and
`design/APPROVED_GREEN_ERP_REFERENCE.png`, after reading the design system and
acceptance checklist. Inspected actual full-page desktop and mobile captures.
The shared light sidebar/topbar, warm neutral canvas, rounded white cards, thin
muted borders, dark text, green actions, muted-green waveform and amber needs-review
states remain consistent. Approved state has a light-green badge. No blue or pink
dominant color was introduced. The silent fixture produces a flat waveform;
it is real decoded fixture audio, not a fabricated speech waveform.

The review uses responsive timestamped segment rows with original prediction,
confidence, corrected text, speaker selection and uncertainty controls. Native
playback, captions and clamped seeking are reused. QA rationale/range are visible
alongside decision actions and actor history. Permission and export controls only
appear for admins, while the server independently enforces permissions. Route
data continues to show the synthetic-validation banner. The original Gradio
analysis and standalone emotion review remain available and unchanged by this
feature's entry points.

Actual screenshot evidence under `evidence/step24-20261031/`:

- [Registration](evidence/step24-20261031/registration-desktop.png)
- [1440 px draft](evidence/step24-20261031/draft-1440.png), [1280 px](evidence/step24-20261031/draft-1280.png), [1024 px](evidence/step24-20261031/draft-1024.png), [390 px](evidence/step24-20261031/draft-390.png)
- [Submission](evidence/step24-20261031/submitted-independent-approval-required.png), [approved desktop](evidence/step24-20261031/approved-desktop.png), [approved mobile](evidence/step24-20261031/approved-mobile.png)
- [Revocation](evidence/step24-20261031/permission-revoked.png), [source mismatch](evidence/step24-20261031/mismatched-recording.png), [conflict](evidence/step24-20261031/concurrent-edit-conflict.png)
- [Agent denial](evidence/step24-20261031/agent-permission-denied.png), [rejection](evidence/step24-20261031/rejected-review.png), [erasure](evidence/step24-20261031/erased-annotation-source-preserved.png)

Fourteen correction-page axe scans found zero WCAG-rule violations and no
horizontal overflow at the captured sizes. Inputs have visible/accessibly matched
labels, keyboard-native controls and existing green focus styles; errors and
successful action notices are announced. The separate workspace regression adds
sixteen zero-violation scans across nine existing capability views. This is
automated and visual verification, not a completed screen-reader/user study.
