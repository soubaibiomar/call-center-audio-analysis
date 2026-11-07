# Timestamped transcript and QA review

Open a stored call in `/workspace/#/calls/<UUID>` and choose **Review transcript & QA**.
The review route is `/workspace/#/reviews/<UUID>`. Supervisors and administrators
can review; source enrollment, permission changes, export and erasure require an
administrator. Agents retain their existing call-reading permissions.

## Source registration and correction

1. An administrator selects the corresponding local WAV/MP3, supplies a source
   attestation, stable conversation/speaker references, partition and permission
   evidence. Training permission starts unchecked. Analysis permission alone does
   not grant training permission. The browser sends a SHA-256 checksum, not audio.
2. A reviewer selects the same recording. Checksum and duration must match before
   decisions become available. The registered source association remains an
   administrator attestation. The server cannot prove a person listened.
3. Correct text, assign Agent/Customer/Unknown, and flag uncertain segments. Timing
   and original predictions remain fixed. A QA override requires a score from 1
   through 5, a rationale of at least ten characters and an in-bounds audio range.
4. Save corrections, then enter a decision rationale and confirm listening before
   submitting. A different enabled reviewer approves or rejects the saved revision.
   Rejected reviews can be edited and resubmitted. Any new edit resets approval.
5. A conflict means another reviewer saved first. Unsaved text remains visible;
   copy it if needed, then explicitly refresh and reapply. Automatic refetch on
   focus is disabled for the editing query. Navigating away can discard unsaved
   edits; the page marks them as unsaved and refresh explicitly describes discard.

The API trusts its authenticated service/database boundary, not actor fields in
request bodies. It validates revisions even if a client bypasses the interface.
Raw report records are never updated by this workflow. Audit snapshots preserve
the actor, role, state, revision, corrections, permission evidence, decision
rationale and claimed playback checksum/duration. The history endpoint displays
actor/action/revision/time and snapshot fingerprints, without returning every old
transcript copy. Detailed snapshots remain in the scoped audit table.

## Export and retention

`GET /api/v1/call-review-dataset` returns the current administrator-only annotation
manifest. Membership requires independent approval, training partition, explicit
current permission, unexpired source, no uncertainty and no Unknown speaker role.
It contains corrected text, optional QA evidence, provenance IDs, source/original
checksums and source expiry; no audio or local storage paths. It considers at most
100 current candidates and explicitly reports truncation.

This is an annotation export, not a training job or a complete audio corpus.
Before a training job uses a downloaded copy, fetch current membership again,
compare revision/checksums, verify rights and retention, and resolve the source
through authorized storage. Revocation cannot retract a previously downloaded
file. Delete or replace stale exports under the recipient's retention policy.
The included browser-test export is a **synthetic test receipt**, not ground truth.

Shared tenant partition locks prevent registered audio, speaker and conversation
references from crossing train/evaluation cohorts, including the emotion workflow.
They cannot discover identity aliases or historical split locks not registered in
this database. An administrator must reconcile those references before real use.
Erasing an annotation cascades to its transcript audit copies, preserving the
original source call and a minimal erasure audit entry. Expired annotations can
also be explicitly erased. Source-call deletion cascades through annotation data.
Hashed cohort reservations remain to prevent later train/evaluation leakage.

## Database and launch

Migration head is `0005_call_review`. Existing running applications/databases were
not migrated by this step. Back up and review the target database before the
existing owner-controlled migration and runtime-role provisioning procedure.
Readiness fails closed if the schema revision does not match. Migration downgrade
is permitted only with empty annotation tables; populated downgrade refuses data
loss. Restore from a reviewed backup rather than forcing it.

For the **isolated local synthetic preview** prepared in this execution:

```powershell
$env:PROJECT28_TEST_ADMIN_URL_FILE='.local/step24_test_admin_url'
$env:PROJECT28_TEST_APP_URL_FILE='.local/step24_test_app_url'
$env:PROJECT28_PREVIEW_STEP='24'
$env:PROJECT28_PREVIEW_PORT='8786'
uv run --no-sync python -m scripts.preview_workspace
```

Use `http://127.0.0.1:8786/workspace/` after `npm --prefix apps/web run build`.
The preview writes short-lived synthetic credentials privately to
`.local/step24-ui-context.json`; it is not a production sign-in provider. Do not
publish this file. The optional Vite development server uses port 8787 and
`PROJECT28_DEV_API_PORT=8786`. Never point this seeder at a production database.

## Revalidation

```powershell
$env:PROJECT28_TEST_ADMIN_URL_FILE='.local/step24_test_admin_url'
$env:PROJECT28_TEST_APP_URL_FILE='.local/step24_test_app_url'
uv run --no-sync pytest tests/reviews -q
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
npm --prefix apps/web run api:check
npm --prefix apps/web test
npm --prefix apps/web run build
$env:PROJECT28_REVIEW_WEB_URL='http://127.0.0.1:8786/workspace/'
node tests/frontend/call-reviews.mjs
```

The browser harness erases/recreates only its synthetic tenant's fixture
annotations to exercise enrollment, approval, revocation, rejection and erasure.
It requires the private context emitted by the isolated preview. It never invokes
model inference or training. Detailed observed results are in the STEP_24 report.
