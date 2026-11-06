# STEP_21 — Collect reviewed emotion labels without contaminating data

**DONE — PASS WITH LIMITATIONS**, for authenticated local research feedback capture. Owner Platform / Codex. Date 2026-10-29, Africa/Casablanca. Windows 11, PowerShell, uv Python 3.12, local PostgreSQL; React/TypeScript built with Node 24.18.0. Branch `feature/project28-foundation`; working HEAD `a37e4634af1d2947fc3c548d54e62bda0b0daf89`; upstream `fed4b610742c1337147281fcec8f2cdcc0a79be5`. No model training, commit, push or public deployment.

## 1. Goal and completed work

Built a real annotation interface and authenticated API for later emotion adaptation. The interface separates the immutable original prediction from human corrections, supports the four-class taxonomy plus uncertainty/abstention and reviewer notes, requires explicit confirmation, and verifies a local source file checksum before enabling UI confirmation. Recordings stay on the laptop; no new audio-upload route was added.

Corrections are stored separately with authenticated reviewer IDs and current versions. Two distinct active reviewer IDs must agree on a known label; disagreement remains excluded until independent-admin adjudication. Training eligibility separately requires a train partition, permission attestation and an unexpired source. Revocation, deletion, consent withdrawal and source-call erasure propagate to current dataset membership.

Read master/index, full STEP_21 prompt/template, STEP_20 report and limitations, current schemas/auth/API/migrations/data contracts, approved design system/checklist and reference image before implementation. STEP_20's research evaluation prerequisites are available, but its production emotion-label NO-GO remains. This step implements a collection workflow; it does not create a real human-reviewed corpus or improve neural weights. All validation identities, recordings and corrections were synthetic.

## 2. Original upstream and preceding implementation comparison

| Area | Actual original / preceding state | Actual upgrade and compatibility |
|---|---|---|
| Frontend | Original Gradio; no `apps/web` feature. STEP_20 adds no rendered UI | New isolated React annotation feature; original Gradio preserved |
| Reviews | STEP_08 generic Review table exists but has no emotion-specific HTTP workflow | Separate emotion item/vote tables; existing generic review rows untouched |
| Predictions | STEP_19 typed acoustic outputs in call reports | Enrollment reads stored report signal/model/timestamps; corrections never replace it |
| Auth | STEP_09 signed identities resolved to enabled tenant users; default fail-closed | Reuses same boundary, with supervisor/admin-only review and admin-only evaluation/permission/export actions |
| Training data | No emotion correction manifest | Live role-scoped consent/dual-review manifest and fingerprint; no training launch |
| Test isolation | Dataset manifests existed offline | Tenant-specific immutable partition-key reservations for declared source/conversation/speaker keys |
| Erasure | Existing call/retention lifecycle | New FK cascades remove dependent items/votes; consent/review changes remove live membership |

The pinned upstream contains neither the proposed emotion API nor React app; the normalized platform was introduced in earlier uncommitted steps. The captured whole-workspace tracked diff remains **40 files, 1063 insertions, 369 deletions**, predominantly prior work; new untracked directories are listed separately. `working-tree-stat.txt`, `working-tree-names.txt` and `new-files.txt` are evidence, not a claim that the entire accumulated diff belongs to STEP_21.

## 3. Created/modified files and interfaces

| Path | Purpose and change |
|---|---|
| `services/reviews/__init__.py`, `contracts.py`, `service.py` | New typed input/output and transaction-bound enrollment, voting, revocation, consensus, dataset and agreement logic |
| `services/api/routes/reviews.py` | New nine authenticated emotion-review paths |
| `services/api/db/models.py` | New EmotionItem, EmotionVote and EmotionPartitionKey mappings |
| `migrations/versions/0004_emotion.py` | Frozen PostgreSQL DDL, constraints, RLS/grants, original-snapshot trigger and guarded downgrade |
| `services/api/db/settings.py` | Expected schema revision advanced to 0004_emotion |
| `services/api/app.py` | Router registration; optional built `/review-ui/` static mount; no-store remains and nosniff/no-referrer headers added |
| `src/services/analysis.py` | Typed optional downloads kwargs preserve legacy invocation shape and strict typing |
| `apps/web/package.json`, lockfile, tsconfig, Vite config, index and `.gitignore` | Minimal feature build with pinned dependencies; generated assets/node_modules excluded |
| `apps/web/src/features/emotion/EmotionReview.tsx`, `review.css`, entrypoint/type declaration | Real form, local playback/hash checking, comparison, consent controls and responsive approved-style presentation |
| `apps/web/tests/emotion-review.mjs` | Signed synthetic browser flow, source mismatch, save/revoke, permission form, axe, screenshot and overflow checks |
| `tests/api/test_emotion_reviews.py`, `tests/api/test_api.py` | Ten new real-PostgreSQL/API cases; updated schema path count |
| `scripts/preview_emotion_reviews.py` | Development-only synthetic signed preview; refuses non-test DB names and keeps credentials ignored |
| `docs/api/openapi.json` | Regenerated actual API contract; 23 total paths |
| `docs/development/emotion-review.md`, this report, progress/limitations and evidence | Setup, source/permission boundaries, measured results and next handoff |

No production database migration was applied: only the explicitly isolated test database was upgraded. The synthetic preview listens on loopback and is not the production identity provider.

## 4. Important code, functions and architecture

`Enrollment` excludes any client-supplied original prediction: only an admin can select a stored call/segment. `EmotionSignal` validates the copied machine output. Source model ID/revision, probabilities and timestamps live in `EmotionItem.prediction`, while reviewed labels/notes live in `EmotionVote`. The PostgreSQL trigger compares original identity/call/segment, JSON prediction, partition, source digest and grouping fields before updates; changes to those fields fail even through direct restricted-role SQL. Authorized deletion remains possible: immutable does not mean undeletable.

Enrollment hashes audio/conversation/speaker keys and reserves their partition within the tenant. Sorted advisory transaction locks serialize competing reservations; conflicting existing partitions return 409. Partition keys are deliberately not mutable by the application DB role. Keys are only as reliable as administrator-supplied source/group metadata; there is no automatic global identity discovery or import of every historical external test lock.

`get_item` checks reviewer role, tenant, source expiry and evaluation access; unauthorized evaluation lookup returns 404. `vote` takes an item lock and checks `expected_revision`; stale clients get 409. Reviewer identity comes from verified request state, never from JSON. One active vote per reviewer/item is enforced by a unique constraint. Editing increments vote version and item revision, redacts notes with existing PII redaction and clears prior adjudication. Revocation deletes that user's vote and clears derived verification/adjudication.

`view` derives status from current votes. Fewer than two votes remains pending. Multiple labels disagree; two or more all-Unknown labels remain uncertain. Known unanimous labels are verified. An admin who is not an active voter can reconcile a disagreement with explicit confirmation/reason. Subsequent votes invalidate that adjudication. Distinct user IDs establish separate accounts, not independently verified distinct humans or blind review.

Training eligibility is derived, not an arbitrary reviewer flag: partition=train, explicit training permission, known verified/adjudicated correction and unexpired source. Admin consent updates have revision checks; evaluation permission cannot be changed to training. The dataset query locks candidate items while building the current metadata manifest, is bounded to 1000 candidates and includes source digest, span, label, revision and reviewer/model lineage. It never reads or returns recording bytes and never starts training. Its fingerprint changes with membership/revision.

Deleting an annotation deletes votes through FK cascade while preserving the original call report. Deleting the original call record cascades through its normalized call to annotation/votes. Admin annotation erasure also works after source expiry; ordinary review access does not. Live membership is rebuilt on every request. External copies/backups cannot be recalled by this API; future consumers must revalidate current membership/fingerprint.

The React component uses real server responses for queue, status, original/corrected comparison and permission results. The token stays in component memory and is cleared on sign-out; it is never placed in local/session storage or URLs. Selecting audio computes SHA-256 with Web Crypto, refuses mismatch and only creates a local blob URL for playback; replacing the URL releases it. Confirmation is still an attestation, not proof that a human listened. The API has no client-supplied original-label override and does not accept a fabricated reviewer ID.

## 5. Imports and dependencies explained

| Import/library | Role and reason |
|---|---|
| Python hashlib/json/UUID/typing | Stable metadata fingerprints, safe JSON, validated identities, typed contracts/heterogeneous manifest output |
| Pydantic BaseModel/ConfigDict/Field/StringConstraints/Literal | Reject extra/spoofed fields, unknown labels, false/missing confirmation, excessive notes and invalid revisions |
| FastAPI APIRouter/Depends/HTTPException and Principal | Authenticated routes and meaningful 403/404/409/422 boundaries; existing signed identity verifier reused |
| SQLAlchemy select/delete/update/func/text/Session and model column/FK/index types | Parameterized transactional queries, locks, bounded manifests, relationships and tenant-scoped storage |
| Alembic op and SQLAlchemy text | Reviewed frozen schema migration and guarded downgrade, not automatic request-time schema changes |
| Existing redact_pii, session_scope, CallRecord, EmotionSignal | Reuse note masking, transaction-local tenant identity, stored report and model schema |
| TypedDict in AnalysisService | Describes the optional downloads keyword without altering the legacy default call shape |
| React useState/useEffect/useRef and FormEvent; react-dom createRoot | Form/network/audio state, cleanup and mounting; no chart framework or external UI theme |
| TypeScript/Vite and CSS import | Type checking, local bundled assets and scoped approved tokens/layout |
| Web Crypto, fetch, File/blob, audio and URL APIs | Browser-local checksum/playback, authenticated same-origin requests and object URL cleanup |
| Playwright/chromium, axe-core/playwright, Node fs/path/assert | Real browser automation, automated accessibility, local fixture access, screenshots and assertions |
| Test pytest, SQLAlchemy, RSA/JWT helpers and synthetic audio builders | Real signed identities and DB behavior; no mocked authorization or fake human annotation claims |

Versions from the locked feature: React/React DOM **19.3.1**, TypeScript **7.0.2**, Vite **8.3.5**, Playwright **1.64.1**, axe-core/playwright **4.14.0**. Existing Python framework/database pins were reused; no neural package or model download occurred. npm audit during dependency installation reported zero vulnerabilities at that moment, not a permanent security guarantee. Prettier was added only for source formatting; package-lock pins its exact installed version. No dominant blue/pink component default or decorative icon library was introduced.

## 6. Concepts from first principles

Annotation provenance links a label to its source segment, machine version, authenticated reviewer and confirmation. A supervised label is an input to later training, not evidence that training has occurred. Original-versus-corrected storage allows errors to be examined without rewriting what the model actually predicted.

Two-reviewer agreement means two independently authenticated accounts supplied the same current label. Raw agreement is agreeing pairs divided by exactly-two-reviewer pairs; Unknown participates as an explicit response. It is not chance-corrected Cohen's kappa or a population reliability estimate. Adjudication resolves a recorded disagreement; it is not a model deciding which person is right.

Test contamination occurs when evaluation groups enter training. Stable source/conversation/speaker keys reserve a declared partition, and evaluation records cannot enter the training view. For example, a train enrollment whose declared speaker key already belongs to evaluation is refused. Unknown identity linkage and cross-tenant duplication are not magically solved by hashes.

## 7. Security, privacy, data and model implications

API requests reuse RSA-signed issuer/audience/lifetime checks and enabled-user resolution. Agents cannot review; supervisors/admins can review train items; only admins can access evaluation, enroll, change training permission, adjudicate or obtain the training manifest. RLS is enabled/forced for all new tables; the application role has no UPDATE/DELETE on partition reservations. Tenant isolation does not turn a privileged database owner into an untrusted actor or provide per-reviewer SQL authorization independently of the API.

Only synthetic test reports/tone/audio hashes and accounts were used. Existing STEP_20 labeled public data/test snapshots were not relabeled, moved into training or changed. No real human correction, actual inter-rater study, training run, fine-tuning or accuracy improvement was performed. Production emotion exposure remains NO-GO.

Reviewer notes use the existing incomplete PII redactor; the interface explicitly asks for no personal data. Consent is an admin-managed flag plus evidence reference, not an automated legal determination or independently signed proof. Matching source checksum attests bytes relative to declared metadata, not rights/completeness. Original inference is copied from the stored report, not a new inference run.

Delete/revoke/expiry affect server-side annotations and live membership. Restrictive grouping digests remain after annotation erasure to avoid accidental reuse; their privacy/retention policy and any cross-source resolver need organizational governance. Previously downloaded copies, backup expiration, full source-storage erasure and past training-run lineage remain beyond this workflow. Current vote versions are stored; there is no append-only history retaining every withdrawn label value.

## 8. Tests, exact execution and corrections

- Isolated migration: `DATABASE_URL_FILE=.local/step08_test_admin_url`, `python -m alembic upgrade head`; succeeded, head **0004_emotion**. Primary project data was not migrated or reset.
- Focused signed HTTP/PostgreSQL suite: **10 passed, 1 warning in 8.11s**. Covers dual review, stale revisions, immutable prediction, tenant RLS, held-out visibility, conflicting speaker partition, invalid consent, disagreement/adjudication invalidation, consent withdrawal, correction deletion, source cascade and paired metrics. Invalid clinical label, false confirmation and reviewer spoofing are separately rejected.
- Full configured command: `pytest tests/unit tests/security tests/api tests/integration tests/workers tests/llm tests/datasets tests/rag tests/emotion -q --tb=short` using ignored isolated DB URL files. Final **437 passed, 1 warning in 76.33s**, exit 0, no skips. Evidence `regression-final.txt`.
- Ruff lint passed; ten changed Python files passed format check. Mypy passed seven API/review/DB/shared-service source files.
- `scripts/export_api_schema.py`: regenerated the real 23-path schema and schema equality test passed.
- `npm run build --prefix apps/web`: TypeScript and production Vite build passed. Final JS bundle about **232.24 kB / 72.64 kB gzip**, CSS **6.70 kB / 2.10 kB gzip**; these are build sizes, not runtime performance benchmarks.
- `node apps/web/tests/emotion-review.mjs`: real local production assets/API, signed synthetic identities and local generated audio. Six recorded interaction assertions passed; eight captured states had no document overflow. Three reviewed viewports had **zero axe findings** under selected WCAG A/AA tags; **zero page errors**. The one HTTP 401 was the intentional invalid-auth test. See `browser-qa.json`.

Initial full run preserved in `regression.txt`: 420 passed, two failed and 15 setup errors. The readiness constant still expected 0003_jobs after the new migration; updating it fixed readiness/setup. A temporary explicit downloads keyword broke a legacy positional-only test seam; a typed optional-kwargs object restored the previous call shape and strict typing. Initial migration draft branched from the wrong head; it was corrected to follow 0003_jobs before successful upgrade. Migration DDL was frozen rather than importing mutable current table models.

Browser harness setup corrections: explicit preview item selection, explicit Playwright browser context for axe and synthetic-state reset for reruns. These were test-harness issues, not hidden passes. Real UI findings corrected: mobile grid overflow and a success notice that incorrectly requested a second review after verification. Recaptured final desktop/tablet/mobile evidence confirms those fixes. Existing pytest-asyncio and Starlette/AnyIO deprecation warnings remain. No failing/omitted check is presented as passed.

## 9. Analytics and evidence

| Metric | Actual observed result | Interpretation |
|---|---|---|
| Corrected segments during browser fixture | **1**, before revocation | Two signed synthetic accounts agreed on sad while original angry stayed unchanged |
| Browser paired agreement | **1/1 = 100%** | One synthetic pair, not measured human reliability |
| Controlled API audit fixture | **1/2 = 50%** | Two synthetic paired items: one agreement, one disagreement; corrected_segments=1 |
| No paired reviews | **null**, not 0% | Zero denominator is explicitly unmeasured |
| Invalid labels | **1 controlled unsupported clinical label refused; zero such stored labels** | Additional confirmation=false and spoofed reviewer submissions also refused; not a production invalid-label rate |
| Real human labels / population inter-rater agreement | **Not measured** | No people were recruited or asked to label clips in this step |
| Model accuracy / learning improvement | **Not measured; no training** | Annotation capture is infrastructure, not adaptation |
| UI automated checks | 3 axe-audited viewports, 8 captured states, 0 overflow/page errors | Scoped synthetic browser evidence, not complete accessibility certification |

Raw browser metric response is saved in `browser-qa.json`; API tests assert exact expected pair/count behavior against real storage. No reference-image sales figures or invented customer activity is used. Operational latency percentiles, field Core Web Vitals, full screen-reader testing and real reviewer throughput remain Not measured.

## 10. Technical questions with answers

1. **Why preserve original predictions?** A correction should not erase the evidence of a model error. Model ID/revision, probabilities and time span remain in an immutable snapshot while the human label is separate.
2. **What if reviewers disagree?** The item remains excluded from training. An admin who is not a current voter can reconcile with a reason, or the item can remain uncertain. Later edits/revocations invalidate reconciliation.
3. **Can every call become training data?** No. It needs purpose-specific organizational permission, a train partition, current eligible review and an unexpired source. Checkbox/annotation alone does not establish rights.
4. **How does withdrawal propagate?** The current vote is deleted or consent revoked, derived verification changes, and the next live manifest excludes it with a different fingerprint. Remote copies/backups cannot be recalled automatically.
5. **How is evaluation protected?** Normal reviewer listing/lookup cannot expose evaluation items; training permission is forbidden for them. Declared source/conversation/speaker keys cannot switch partition within the tenant. Cross-source identity discovery still needs trusted metadata.
6. **Does agreement prove true emotion?** No. Labels express reviewer perception. Synthetic agreement tests the workflow, and visible model predictions can bias real reviewers. No clinical or punitive judgement follows.
7. **Why local playback?** It lets reviewers validate matching bytes without adding a broad audio-download surface. Integrated authorized source storage/playback and reviewer assignment are later work.
8. **Why no automatic training?** STEP_20 remains NO-GO for production emotion labels; collecting labels must precede separate consent, split, evaluation and training approval procedures.

## 11. Decisions, limitations and risks

Use an isolated feature page, preserving Gradio and avoiding implementation of the entire STEP_22 application shell. The review queue is limited to the latest 100 registrations, and dataset/metric candidate scans are bounded at 1000. Large-scale pagination, bulk assignment and workload performance are not established.

Production OIDC/provider onboarding remains unconfigured; default API authentication fails closed. Validation used a local signed synthetic provider against real restricted PostgreSQL. The access-token connection form is a local integration surface, not a completed SSO login product. Built assets are served from the checkout when present; production image/static asset packaging remains future deployment work.

Source/group metadata and consent evidence are administrator attestations. Historical external test manifests are not automatically imported, keys are tenant-specific, and cross-tenant/source duplication cannot be guaranteed absent trusted identity mappings. Distinct reviewer IDs are not proof of distinct people or blind annotation. No actual human corpus was collected. PII redaction, backup/object retention, source-storage erasure and copies of exported manifests retain prior limitations.

No append-only history of deleted corrections is claimed. Consumers must revalidate current manifest membership; there is no trainer enforcing that lifecycle yet. This feedback workflow does not override the production emotion NO-GO or any previously saved ASR/RAG/security limitations.

## 12. Acceptance decision and next handoff

**PASS WITH LIMITATIONS for local feedback capture.** All step gates have actual tests: original inference snapshots cannot be updated, corrections can be revoked/deleted with current dataset membership refreshed, and evaluation access is restricted. The source-call erasure cascade was executed and checked against item/vote tables.

Next eligible step: **STEP_22**, subject to its own prompt/prerequisites. It was not executed. Reuse this scoped feature/contracts when building the larger approved application shell; do not treat this narrow page as completion of that future work. Human labeling, rights governance and any emotion training/evaluation remain separately required.

- [x] Real schema, authenticated routes and typed annotation capture implemented.
- [x] Reviewer confirmation, uncertainty, model/correction separation and independent-account workflow tested.
- [x] Consent/deletion/live-manifest and held-out protections executed against PostgreSQL.
- [x] Actual React build, browser interactions, screenshots and axe results captured.
- [x] Synthetic metrics labeled; no human labels or neural improvements invented.
- [x] Initial failures and fixes retained; final full regression passed.
- [x] Report/progress/limitations and local runbook updated; no push/deployment/training.

## 13. Approved ERP UI design / visual contract verification

Approved baseline visually inspected: `design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png`; system/checklist read. The new `/review-ui/` page uses white rounded cards, warm neutral canvas, forest-green controls, dark readable text and a light rounded sidebar. Original and corrected results sit side by side on desktop and stack on mobile. No blue/pink theme, decorative icon library or fake dashboard numbers were introduced. The original Gradio baseline remains separate and unchanged by this feature.

Tokens include background **#F6F6F3**, cards **#FFFFFF**, primary forest **#1D5B49**, text **#182820**, secondary **#56645D**, border **#E4E8E1** and muted green selected surfaces. Semantic errors use red/brown on a pale warm background. The approved light-green emphasis is adapted to darker green buttons for readable text contrast. Sidebar/nav, top account area, quiet cards, rounded inputs and restrained pills match the reference principles; a task-specific review workspace replaces sales charts/KPIs intentionally. No pixel-equality claim.

Actual screenshots use synthetic source/audio/accounts only:

- [Desktop review](evidence/step21-20261029/review-desktop.png)
- [Tablet review](evidence/step21-20261029/review-tablet.png)
- [Mobile review](evidence/step21-20261029/review-mobile.png)
- [Source mismatch error](evidence/step21-20261029/source-mismatch-desktop.png)
- [Empty search](evidence/step21-20261029/empty-mobile.png)
- [Admin permission form](evidence/step21-20261029/permission-desktop.png)
- [Invalid authentication](evidence/step21-20261029/access-error-mobile.png)
- [Keyboard focus](evidence/step21-20261029/keyboard-focus.png)

Desktop/tablet/mobile captures are **1440×1000, 768×1024 and 390×844** viewports, saved full-page. The mobile queue originally overflowed and now scrolls inside its card; final document widths pass overflow checks. Visible success text now reflects actual verification. Native labels/fieldset/radios/checkboxes, a tested keyboard skip link, focus styling, live status/error regions and reduced-motion rules support accessibility. Axe reported zero findings under selected rules across three viewports, which is not a full assistive-technology or WCAG conformance audit.

The design-visual-qa and browser-qa workflows were applied on this local synthetic preview. See `visual-qa.json` and `browser-qa.json`. UI decision: scoped research review interface passes with documented integration limitations; production emotion analytics remains NO-GO. No user token, customer audio, provider secret or genuine employee emotion judgement appears in the saved evidence.


## STEP_22 compatibility follow-up — 2026-10-31

The standalone /review-ui/ source entry, review feature and CSS remain unchanged.
STEP_22 adds /workspace/ separately. The synthetic preview now optionally accepts
PROJECT28_TEST_ADMIN_URL_FILE and PROJECT28_TEST_APP_URL_FILE, retaining original
defaults and the test-database guard. The browser harness optionally accepts
PROJECT28_REVIEW_EVIDENCE_DIR so new screenshots preserve this report's historical
evidence. Reused synthetic helper annotations were made explicit. The legacy
workflow was rerun with six assertions, eight viewport captures, zero axe
violations and zero console errors; evidence is in ../implementation/evidence/step22-20261031/legacy-review/.
No STEP_21 historical measurement is replaced.
