# Emotion review workflow — STEP_21

This is a local research annotation feature. STEP_20's production emotion-label NO-GO remains in effect. No model is retrained by saving a correction.

## Start and authenticate

Install pinned frontend dependencies with `npm ci --prefix apps/web`, then `npm run build --prefix apps/web`. The existing FastAPI factory serves the built feature at `/review-ui/`. Start it locally with `uvicorn services.api.app:create_app --factory --host 127.0.0.1 --port 8781` in the uv environment. An enabled supervisor/admin identity from the configured provider is required for data; default authentication remains fail-closed. The static shell is public but contains no records.

For development only, `scripts/preview_emotion_reviews.py` seeds an isolated database whose name contains `test`, generates signed synthetic identities and starts the same API on loopback. It reads the existing ignored test DB URL files and writes credentials solely to `.local/step21-ui-context.json`. Do not commit or paste these tokens. The generated tone is `.local/step21-synthetic-review.wav`; its labels/reviews are synthetic fixtures, not human judgements. Stop that helper before starting another service on port 8781. It is not a production login solution.

Browser checks: `node apps/web/tests/emotion-review.mjs` from the repository root. It refuses to mutate records outside the preview's exact synthetic call/model fixture. It reads local credentials in memory, validates desktop/tablet/mobile and saves redacted screenshots and axe findings. It never submits real reviews or customer audio.

## Database setup

Migration `0004_emotion` follows `0003_jobs`. It adds emotion items, votes and tenant-specific partition-key reservations, enables/forces tenant RLS, grants restricted runtime privileges and protects original snapshot fields with a trigger. Run a reviewed backup/migration procedure before any non-test deployment; this task migrated only the isolated test database. Application readiness now requires `0004_emotion`. Downgrade refuses populated emotion tables.

## Administrative enrollment

`POST /api/v1/calls/{call_id}/emotion-review-items` is admin-only. Supply segment index, partition (`train` or `evaluation`), source audio SHA-256, a stable conversation key, stable speaker keys and a consent evidence reference. `consent_to_train` defaults false. Original prediction/model/timing is copied from the stored call report, never from a submitted correction. Administrators must provide truthful, purpose-permitted source/group metadata; a self-declared hash is not proof of source rights or completeness.

Source audio, conversation and speaker keys reserve a partition within the tenant. Conflicting enrollment returns 409. Register known held-out groups as evaluation before collecting train labels; existing external test manifests are not automatically imported or globally resolved. Source identities and cross-tenant duplicates cannot be inferred automatically. Reserved digests remain as restrictive metadata after annotation deletion to prevent accidental reuse; their retention needs organizational policy.

## Reviewer workflow

1. Connect using an enabled supervisor/admin token; tokens stay in page memory, with no local/session storage or query-string token.
2. Select an item from the latest 100 registrations returned by the queue. Agents cannot review. Ordinary reviewers cannot see evaluation records; admins may inspect them.
3. Select the original recording locally. The browser checks its SHA-256 against enrollment before enabling confirmation; it never uploads audio. Use the timestamped player to inspect the segment. A confirmation is a reviewer attestation, not proof that a human listened.
4. Choose neutral/happy/angry/sad or Uncertain/abstain, optionally enter notes without personal data, and explicitly confirm. Notes receive the existing PII redaction, which is not exhaustive.
5. Two distinct active reviewer IDs must agree on a non-Unknown label to verify it. Disagreement stays excluded; an admin who is not an active voter can adjudicate with a reason. Any later vote edit/revocation clears adjudication.
6. Revoke your own correction, or ask an admin to delete the annotation. Deleting the source call cascades item/vote erasure. The original call prediction is not edited when changing/deleting a correction.

`POST .../votes` requires the current item revision; stale clients get 409. Review versions retain current provenance; this is not an append-only history of all past label values. Distinct account IDs do not independently prove distinct humans, and visible machine labels can influence reviewers.

## Consent, dataset membership and deletion

Admin `PATCH .../consent` updates training permission/evidence. An annotation becomes eligible only when train-partitioned, consented, unexpired and verified/adjudicated to a known label. Evaluation items can never be training-consented. Admin `GET /api/v1/emotion-training-dataset` returns a current metadata manifest and fingerprint, never audio. It is bounded to 1000 candidate items and uses item locks while constructing membership. It performs no training or automatic dataset promotion.

Revocation/deletion/consent withdrawal/expiry remove membership on the next manifest request; source erasure cascades physical removal of annotation rows. Previously downloaded files, backups or externally copied manifests cannot be remotely recalled by this API. Consumers must revalidate current membership/fingerprint before use. Storage-level erasure and full training-run lineage remain later deployment work. Admin deletion is allowed even after a source expires; normal review access to expired calls is denied.

## Review metrics and safeguards

`GET /api/v1/emotion-review-metrics` returns current corrected segments, exactly-two-reviewer audit pairs, agreeing pairs and nullable raw exact-label agreement (including Unknown). This is descriptive, not Cohen's kappa or a population reliability estimate. Zero pairs yields null. Metrics are role/tenant scoped and bounded, like data access.

Backend tests use real RSA signatures, the restricted PostgreSQL role and synthetic reports. Browser review metrics are explicitly synthetic. No new human labels or accuracy improvements were collected. No HR/QA score is automatically changed. Keep real inference output out of punitive decisions and retain the approved green-neutral, uncertainty-first presentation.
