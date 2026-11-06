# Permission-aware metadata and split planner

`python -m src.datasets <manifest.json> --as-of YYYY-MM-DD --seed <safe-token> --output <new-lock.json>`
validates JSON metadata without opening audio. Store real manifests, raw data,
consent evidence and locks under private `.local/` or the ignored `data/datasets/`
and `data/manifests/` roots with appropriate OS access controls. Git ignore is a
convenience, not access control and cannot protect files placed elsewhere or force-added.

Every record requires pseudonymous project-wide sample, source/version/subset,
conversation and speaker IDs; SHA256 of the exact audio bytes; duration; language
labels; reviewed-label status and independent label evidence/reviewer references; and explicit approved training plus evaluation rights,
basis, license/terms, reviewer/evidence references, review and retention dates.
Only reviewed human-verified labels are eligible. Unknown speaker linkage, rights,
missing hashes, unreviewed or machine-only labels must be resolved before this
planner can create a split. It rejects an entire manifest on any ineligible record;
it does not silently filter records. HTTPS terms URL validation is syntactic and the
planner does not verify reviewer authority, evidence, actual bytes, consent or license.
Approval fields are operator attestations, not an authorization service.

The planner joins records by shared project-wide speaker ID, conversation ID or
identical audio SHA256, including transitive links. It sorts component hashes using
an explicit seed and assigns roughly 80/10/10 by **component count**, with at least
one component per partition; sample counts or hours can differ substantially. The
same metadata and seed reproduce assignments regardless of input order. Different
identities for the same real speaker, altered audio encodings and unidentified
cross-dataset duplicates cannot be detected automatically. Resolve these before
claiming a real dataset is disjoint. Per-record language tags can overlap: summing
hours by language would double count code-switched audio unless span durations exist.

The first lock stores assignments and record fingerprints. Store its SHA256 through
an independent trusted channel, then supply both `--prior-lock` and `--prior-sha256`
to extend it. The new output must not already exist. Old assignments/content must
match, new cross-partition links fail, and no new sample may join a locked test
component; new independent groups go to train. A new independently created lock can
still be made by an authorized operator: lock governance/immutable storage and
identity authentication are not implemented. A changed/revoked record is rejected;
reviewed revocation/deletion workflow and a new version must be handled separately.
The explicit `--as-of` date enables reproducibility but can be backdated; downstream
training/evaluation must revalidate against the actual current date and current
rights before accessing files. There is no automatic retention deletion or live
training gate in this step.

The user selected a public candidate after source-rights review. A bounded execution
of `python -m scripts.inventory_librispeech_sample --output data/datasets/<new-folder>`
acquired three CC BY 4.0 LibriSpeech viewer WAV examples and their unreviewed
reference texts (788132 bytes of audio, 24.625 seconds) into the ignored output
folder. It reads train.100/validation/test first rows, checks each asset host and a
2 MiB per-file limit, records the observed repository HEAD, verifies WAV length and
hash, and writes a private source index and metadata manifest. It does not establish
that the viewer response corresponds to that observed HEAD. The per-record review
status is pending, both purpose flags are false, label status is unreviewed, and the
provisional retention date is the intake date; no automatic deletion is implemented.
Public source identifiers are pseudonyms, not anonymous. The source splits are not
our approved locked split. The planner rejects this manifest until authorized
rights and label reviews, retention and identity verification are completed.

See DATASET_CATALOG and the annotation guide. The separate Common Voice French intake below now supplies a small reviewed sample and a local lock; it does not supply a representative Darija/call-center evaluation corpus.

A bounded intake can be reproduced into a new ignored folder with:

```powershell
.\.venv\Scripts\python.exe -m scripts.inventory_commonvoice22_fr --output data/datasets/<new-folder> --retention-until 2026-11-28
.\.venv\Scripts\python.exe -m src.datasets data/datasets/<new-folder>/manifest.json --as-of 2026-10-28 --seed cv22-fr-v1 --output data/datasets/<new-folder>/split-lock.json
```

The source repository revision is recorded and requested explicitly; selection is bounded to the beginning of each TSV and archive. Community votes attest the published validation, not an independent project review. The lock and its adjacent SHA256 are local conveniences, not independently controlled immutable evidence. Establish trusted external hash storage, current rights revalidation and retention handling before downstream use. Do not re-identify speakers. Delete or re-review the local benchmark by its user-selected deadline; no automatic deletion exists.

