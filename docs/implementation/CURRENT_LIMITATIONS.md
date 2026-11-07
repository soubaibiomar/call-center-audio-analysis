# Current Project 28 limitations

Recorded at the user's request on 2026-10-28. Recheck against source and execution evidence before marking any item resolved. This list supplements the STEP_15 report; it is not proof of production readiness.

1. **Deployment isolation:** The restricted Docker decoder preflight is a host-only option and is not integrated end-to-end into the deployed application. Parent metadata parsing and later inference can still process untrusted media.
2. **Recognition evaluation:** Reviewed validation currently covers three English support role-plays. Representative real customer calls, other languages and broader noise/accent coverage remain unvalidated.
3. **Chunk reconciliation:** Overlapping context and word-timestamp ownership reduce boundary issues, but timestamp errors and differing recognition hypotheses may still lose or repeat words.
4. **Stereo:** Channel bleed, duplicate speech and some partial cancellation cases may still escape detection.
5. **Integrity provenance:** Detecting all damaged compressed files requires trustworthy original metadata or a source checksum. An upload's self-computed digest does not establish source completeness or authenticity.
6. **Speaker roles:** Agent/customer mapping requires independently verified metadata. Channel position alone is insufficient.
7. **Denoising:** Disabled by default because broad transcription-quality benefit has not been established.

The STEP_15 service-configured regression recorded 384 passing tests at that historical checkpoint. A subsequent focused decoder run passed seven tests. Later step-specific reports record newer results, including STEP_19 with 417 passing tests. These results validate tested behavior and do not close the limitations above.

Detailed implementation and evidence: [STEP_15 report](STEP_15_harden_audio_preprocessing_vad_and_segmentation_REPORT.md).

Update this file whenever a limitation changes, with the implementation and execution evidence supporting its new status. Do not infer resolution from a green test suite alone.

STEP_18 knowledge limitations (2026-10-29): Extractive references only; no semantic agent-policy entailment or multi-source synthesis. Multiple hits and undated/future policies abstain. Trusted scoped service must be injected; default workflows abstain. Known malicious patterns are screened but unknown malicious quotations may still be displayed as untrusted text. Source content has no tool/LLM dispatch path. Representative retrieval relevance, production auth/RLS, erasure/history and post-retrieval revocation races remain open. See STEP_18 report and synthetic benchmark evidence.

STEP_19 acoustic emotion limitations (2026-10-29): English/IEMOCAP-derived checkpoint, no representative call-center/French/Darija validation, no macro F1 or calibration. Pilot probability thresholds do not establish true feelings; the real synthetic-tone smoke produced a confident classification on non-speech. No automatic QA/HR score changes. Default graph is disabled unless a local service is injected. Mono-only inference; stereo, overlapping/uncertain identities and turns outside 0.5–10 seconds remain Unknown. Maximum 120 turns and ten-minute decoded input; no full-call streaming or hard total inference deadline. CPU per-instance serialized inference has only single-sample resource evidence, not sustained capacity. Weights are pinned/hash-verified; config/runtime and production packaging remain trusted experimental setup. Audio/result caching is disabled for this stage, but report retention and inherited native decoder isolation remain unresolved. See STEP_19 report, local runbook and model-smoke.json.

STEP_20 update (2026-10-29): Small real-checkpoint labeled evaluation now exists: 16 CREMA-D acted-English and 16 MDER-MA Darija media clips, plus correlated seeded-noise variants. This replaces STEP_19's statement that all emotion macro-F1/calibration were unmeasured only for those narrow subsets. Clean raw macro F1 0.267857 / 0.335852 and ECE 0.592812 / 0.434244 do not establish operational accuracy; Darija remains unsupported/Unknown. Real Moroccan telephone/French performance and verified accent comparisons remain unmeasured; no untouched promotion holdout, calibration fit, confidence-interval-powered coverage or broad noise validation exists. Production UI emotion labels remain NO-GO and automatic punitive/QA score changes remain prohibited. Source licensing/annotation/pretraining assumptions and manual 2026-11-28 retention review remain explicit. See STEP_20 report and EMOTION_SOURCE_REVIEW.md. Final 427-test passing regression does not close these evidence gaps.

STEP_21 (2026-10-29): Feedback capture is implemented and tested, but no genuine human labels, population inter-rater reliability or model adaptation were collected. Validation uses signed synthetic accounts/generated audio. Production OIDC/SSO onboarding and static-asset/image integration remain pending; the preview is not production identity. Audio review uses matching local files, not an integrated cloud playback workflow. Group-key reservations protect declared partitions within each tenant; historical external test locks, cross-source identities and cross-tenant duplicates are not automatically resolved. Consent evidence is an administrator attestation; distinct accounts do not prove independent people or blind review. Revocation/deletion refresh live membership and source cascades remove annotation rows, but external copies/backups cannot be recalled; consumers must revalidate manifests. Restrictive split-key digests remain after annotation erasure and need governance. No append-only history of deleted corrections or trainer-enforced lifecycle exists yet. Queue/export/metric limits and production load remain documented. STEP_20 production emotion NO-GO and earlier platform limitations remain in force. Final 437-test regression and browser checks validate tested behavior only.


## STEP_22 frontend foundation — 2026-10-31

The shared shell and health/auth error states pass their scoped acceptance tests.
Six feature pages remain explicit placeholders for later steps. Manual short-lived
bearer connection is validated against the server; production OIDC/PKCE onboarding,
refresh/session design, CSP rollout and container packaging of frontend assets are
not implemented. The two isolated pgvector integration cases were skipped; all
453 remaining configured backend tests passed. Browser axe and keyboard checks do
not constitute full WCAG/assistive-technology certification or load evidence. The
existing Compose Redis was observed restarting; STEP_22 worker regression used a
separate test Redis and did not repair that service. Model accuracy and human-review
limitations remain; this UI does not promote a model or enable production emotion
judgments. See [STEP_22 report](STEP_22_initialize_react_vite_typescript_frontend_REPORT.md).


## STEP_23 integrated workspace - 2026-10-31

Selected views are now integrated with stored scoped API records. This supersedes
STEP_22's six-placeholder limitation for the selected capability views, not its
production sign-in/deployment limits. Live transport and training/promotion remain
unavailable. Knowledge is saved report evidence, not global current-policy search;
coaching is stored action items, not measured employee improvement. Emotion is
withheld by default in shared HTTP report conversion and exposed only from the
explicit synthetic preview setting. Local WAV/MP3 playback has byte/duration
limits but no source identity verification or hard decoded-memory guarantee.
Lists/selectors are bounded; large-call/concurrent capacity and full assistive
technology checks are unmeasured. Two separate pgvector integration tests remain
skipped. Existing ML/data/rights/retention restrictions remain. See STEP_23 report.

## STEP_24 transcript/QA review — 2026-10-31

Timestamped corrections, speaker reassignment, uncertainty, audio-backed QA score
overrides, independent submit/approve/reject, immutable original snapshots, audit,
revision conflicts and current permissioned export are implemented and validated.
This supersedes STEP_23's lack of source-file matching **only within registered
annotation reviews**: the browser matches SHA-256 and duration to an administrator-
attested source. General call playback still has no registered source association.
Checksums do not prove rights, completeness, physical listening or correct labels.

No real human-verified labels, annotation productivity, blind agreement or model
improvement were established. Two synthetic segments were exported after synthetic
independent approval, then excluded by revocation/edit/rejection/erasure. The saved
test manifest is a historical receipt and is not authorized training ground truth.
External historical split locks and identity aliases require reconciliation; shared
database cohort reservations only protect registered stable references. Downloaded
exports require current permission/revision/expiry and matching audio checks before
training. They cannot be retracted remotely after revocation. Regex PII detection
is incomplete; authorized reviewers can still encounter sensitive source snapshots.

Local native audio decoding lacks a hard memory bound. Reviews are limited to
500 spans and export considers 100 candidates with explicit truncation. Large-call
and concurrent capacity, full assistive-technology studies and representative
label quality remain unmeasured. Unsaved edits need saving before navigation.
The main bundle remains above the advisory 500 kB threshold. Production OIDC and
schema rollout were not performed; only isolated databases were migrated to
`0005_call_review`. Inherited ML, privacy, corpus, retention and live-streaming
limitations remain. Final backend validation: 484 passed, 2 unrelated pgvector
tests skipped; frontend: 32 passed. See the STEP_24 report for browser, migration
and regression evidence. STEP_25 is eligible for its own prerequisite review.


## STEP_25 browser audio transport — 2026-10-31

This supersedes the absence of browser calling only for the explicitly enabled
single-worker local prototype. Two authenticated Chrome users exchanged real
DTLS-SRTP/Opus audio using synthetic microphone speech. Both users' separate
analysis consent gates bounded HTTP PCM capture to real cached local Whisper CPU
inference. End, signaling disconnect and navigation clear sessions/tickets/buffers
and native tracks. The tested reconnect creates a new room and requires fresh
consent; it is not transparent session resumption or network-handoff recovery.

Remaining: no STUN/TURN or SIP/PBX/PSTN, no remote/mobile/NAT study, no production
HTTPS/WSS deployment test (HTTP/WS was explicitly loopback-only), one ASGI worker,
eight-room/ten-minute limits, ephemeral consent rather than a durable ledger, and
no capacity/ingress or physical microphone/echo study. Native inference already
running cannot be interrupted; revoked/terminated results are fenced and discarded.
Cross-party timestamps are receipt-anchored estimates; four-second ASR windows are
not stabilized partial revisions and partial tails are discarded at termination.
No final full-call transcript, assistant events, multilingual accuracy, model
training or benchmark promotion was established. The cached Tiny CPU checkpoint
was transport-path evidence, not a replacement for existing batch model choices.
Regex PII limitations and all earlier dataset/rights/retention restrictions remain.

Current checks: 505 backend passed, two unrelated pgvector skips; 36 frontend
passed; seven native-media browser scenarios, 11 live screenshots/zero-violation
axe scans; existing nine-view regression also passed. Short synthetic loopback
metrics (zero of 597 packets lost, no concealment in sampled receivers, one of one
fresh-room reconnect) do not establish real-world reliability. See STEP_25 report,
transport-metrics.json and browser-calling runbook. STEP_26 is next eligible for
its own prerequisite review.


## STEP_26 update — 2026-10-31

The STEP_25 fixed four-second append-only limitation is superseded for the local
live prototype: speech windows now publish replaceable provisional rows and
immutable final revisions, reconcile overlapping word context and retry one
transient decoder failure. This does not establish native streaming or correct
recognition on arbitrary speech.

Remaining limitations:

- Energy-based speech detection can miss quiet speech or activate on noise.
- The cached Tiny CPU adapter repeatedly decodes bounded chunks; measured
  incremental effective RTF was 0.2531 versus 0.1292 for the four-second baseline.
  Earlier partial text costs additional computation.
- Boundary ownership relies on model word timestamps; estimated timings from
  older adapters are explicitly labeled. Explicit finalization can cut a word.
  Final immutability is a display contract and does not prove transcript accuracy.
- Evidence uses synthetic English speech and short local 1/2/4-source runs,
  including only five final events in the four-source case. It provides no
  human-reviewed multilingual call accuracy or production capacity guarantee.
- Participant receipt anchors approximate cross-party time. Consent revocation
  and termination discard unfinished text; no durable complete call transcript
  or transparent network-handoff recovery is implemented.
- One worker and four pending inference windows bound compute. Overload still
  pauses analysis safely; already-running native inference cannot be interrupted.
- Existing TLS/NAT/telephony, ephemeral consent, PII, corpus rights, retention,
  training and deployment limitations above remain applicable.

Validation: 522 backend tests passed, two unrelated pgvector tests skipped;
43 frontend tests passed. Seven live and 13 existing-workspace browser scenarios
passed. Source, raw execution logs, actual screenshots and precise metric scopes
are linked from [STEP_26 report](STEP_26_implement_stabilized_incremental_asr_with_partial_revis_REPORT.md).
STEP_27 is eligible for prerequisite review and has not started.
