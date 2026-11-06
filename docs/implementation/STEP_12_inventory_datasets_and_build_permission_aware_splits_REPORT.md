# STEP_12 — Inventory datasets and build permission-aware splits

## 1. Execution header, goal and status

**Current status: DONE — PASS WITH LIMITATIONS.** The original PARTIAL findings below describe the earlier LibriSpeech intake; see section 14 for the subsequent reviewed French benchmark, final validation and limitations.
Date: 2026-10-28, Africa/Casablanca. Owner: AI/ML / Codex implementation.
Branch `feature/project28-foundation`, working HEAD
`a37e4634af1d2947fc3c548d54e62bda0b0daf89`; verified upstream clone HEAD
`fed4b610742c1337147281fcec8f2cdcc0a79be5`. All work is uncommitted in the
existing Windows11/PowerShell/uv Python3.12 project. No Conda or training used.

This step builds a metadata-only manifest, purpose/retention checks, reproducible
speaker/conversation/duplicate-aware partitioning, a hash-verified prior lock,
source-rights catalogue and Darija/French annotation guide. It also takes a
bounded public LibriSpeech intake after the user selected a public candidate.
The three LibriSpeech records remain **pending permission and human-label review**, so the
planner refuses to create a lock for that intake. The separately acquired Common Voice records and lock are described in section 14. Synthetic inputs verify the code paths;
they are not a legally approved corpus or evidence of model improvement.

Read the master instructions, STEP_INDEX, complete STEP12 prompt/template, the
STEP11 final correction report, the existing database/report architecture and Git
state. STEP11 passed with documented OIDC, production and mutable-model limitations.
At the earlier review, a target-language evaluation corpus was unavailable; section 14 records the subsequent public benchmark and its limits. STEP13 prerequisites require their own review.

## 2. Actual upstream versus updated implementation

| Surface | Verified upstream | Current implementation | Compatibility |
| --- | --- | --- | --- |
| Dataset manifest / split tooling | Pinned upstream tree has no dataset/consent/split source module | New `src/datasets` metadata schema, deterministic connected components and lock | Additive; original Gradio, audio analysis, QA and reports unchanged |
| Training consent | Existing samples README grants educational/testing usage only; no project training approval established | Separate purpose flags, rights/reviewer/evidence and retention fields; rejected unless explicitly reviewed | Does not infer permission from possession or analysis |
| Source inventory | No project dataset catalogue or code-switching guide in upstream | Source cards, limits and annotation workflow in `docs/data/` | No source or private recording is published |
| Git data protection | Earlier ignore rules covered some audio and `.local` | Add MP3 and private dataset/manifest root rules, preserving tracked samples | Tracked upstream samples remain tracked; Git ignore is not access control |
| Evaluation lock | No project split lock | New digest-verifiable lock records assignments and content fingerprints | External trusted hash and review are necessary; no immutable service is claimed |
| Model Lab | No STEP12 UI in upstream/current scope | JSON Schema and catalogue can inform a future safe metadata API | No endpoint or screenshot implemented in this backend step |

`git-diff-stat.txt`, `git-diff-names.txt` and `git-status.txt` in evidence capture
the actual broader dirty workspace; the many previous STEP01–11 changes are not
attributed to this step. New untracked files do not appear in ordinary diff stats.

## 3. Files, interfaces and purpose

| File | Action | Interface / rationale |
| --- | --- | --- |
| `src/datasets/__init__.py` | Create | Marks the standalone metadata module; no inference or storage initialization |
| `src/datasets/manifest.py` | Create | Pydantic StrictModel, Rights, Sample and Manifest; validates structure without reading audio |
| `src/datasets/split.py` | Create | Lock, plan_splits and load_lock_verified; explicit permissions, grouping and freeze rules |
| `src/datasets/__main__.py` | Create | CLI: metadata input, date/seed, optional pinned prior lock, exclusive new output; generic safe errors |
| `scripts/inventory_librispeech_sample.py` | Create | Bounded three-clip public intake, metadata/hash/WAV checks, pending status and ignored output |
| `tests/datasets/test_manifest_and_split.py` | Create | Synthetic validation, leakage, lock, permission, security and CLI cases |
| `tests/datasets/test_public_intake.py` | Create | Mock HTTP intake, pending-rights behavior, hashes and output-path boundary |
| `.gitignore` | Modify | Ignore MP3 plus private dataset/manifest roots; existing tracked sample exception retained |
| `docs/data/DATASET_CATALOG.md` | Create | Source terms, access, purpose and unresolved restrictions with primary links |
| `docs/data/ANNOTATION_GUIDE.md` | Create | Darija/French spans, script/normalization, human review, consent and no re-identification |
| `docs/data/README.md` | Create | CLI, lock, trust boundaries and real public intake instructions |
| `docs/data/manifest.schema.json` | Create | Generated JSON Schema for metadata consumers; no raw audio or transcript content |
| `docs/implementation/PROGRESS.md` | Modify | STEP12 PARTIAL and next gate |
| This report and `evidence/step12-20261027T190603Z/` | Create | Actual execution, source review, failures, metrics and handoff |

The private public-candidate intake resides in ignored
`data/datasets/librispeech-intake-20261028T091407Z/`; it contains three WAVs,
metadata manifest and unreviewed reference text/source index. The synthetic CLI
input and lock are in ignored `.local/step12-20261027T190603Z/`. No customer
recording, unapproved data, private path content or source transcripts were
copied into documentation/evidence. No existing sample or volume was deleted.

## 4. Important code, data flow and failure behavior

### Metadata schema

`StrictModel` sets extra=forbid, frozen=True and strict=True. `Rights` stores status
approved/pending/denied, basis license/consent/unknown, license identifier, terms
URL, evidence/reviewer references, review/retention dates and separate train and
evaluate booleans. HTTPS terms URLs cannot embed credentials, query or fragment;
approved rights cannot use placeholder evidence/reviewer/license IDs and retention
cannot precede review. URL checks are syntactic and do not verify reviewer authority
or legal permission. The frozen model does not make nested lists/dictionaries into
an authorization mechanism.

`Sample` requires unique sample/source/version/subset, conversation and at least one
speaker pseudonym, exact-audio SHA256, positive finite duration, language tags, label
status, label reviewer/evidence for human_verified, and Rights. No audio path, raw
transcript or arbitrary extra field is accepted. `Manifest` requires schema version1
and unique sample IDs. Pydantic validates JSON dates and fields without opening the
referenced audio. Reviewer and evidence identifiers are operator-provided attestations;
the schema cannot prove their authenticity or that their values contain no PII.

### Permission-aware grouping and locking

`plan_splits(manifest, as_of, seed, prior)` rejects the entire manifest if any record
is pending/denied, unknown basis, lacks **both** training and evaluation permission,
was reviewed in the future, is past retention, or lacks human-verified labels. This
conservative policy also excludes training-only/evaluation-only records; it does not
silently discard them or promote pseudo-labels. A trusted operator must revalidate
against current rights/date at each actual use. The explicit date can be backdated;
this standalone planner is not wired into a live training authorization service.

Union-find groups connected records sharing any project-wide speaker pseudonym,
conversation ID or exact audio hash, including transitive links. Group member IDs
are sorted and SHA256(seed, members) ranks components deterministically. For a new
lock the first max(1, groups//10) groups are test, the next equal count validation,
and the rest train; at least three groups and all three nonempty partitions are
required. The target is approximately80/10/10 **by groups**, not by samples/hours;
large connected groups can yield skewed totals. Changing a seed or inputs without
using a previous lock can create a different split.

`Lock` stores version, algorithm, seed, assignments and per-record SHA256 of
canonical metadata JSON. `load_lock_verified` checks the supplied SHA256 of the
actual prior lock bytes before parsing. On extension, seed and old fingerprints
must match; old records cannot disappear or change; a component bridging old splits
fails; no new record may join an existing test component; new independent groups
enter train. A previously pinned validation component retains its assignment. The
caller must independently store/authenticate the expected hash. Someone able to
create a new lock or replace both file and expected hash can bypass this convention;
immutable storage, authenticated approvals and revocation/deletion workflows are
future integration work. All group IDs must be consistently pseudonymized across
sources. Same speaker under unrelated IDs, different encodings or near duplicates
cannot be automatically detected; published speaker IDs are not permission to
re-identify people.

### Public intake and CLI safety

`inventory_librispeech_sample.main` restricts its new output directory to the
resolved ignored `data/datasets/` root. It queries the public source metadata and
three first-row pages for clean train.100, validation and test; accepts WAV only
from the expected HTTPS dataset-server host; streams at most2 MiB per clip; measures
WAV duration and hashes received bytes; writes files exclusively and records their
unreviewed source references privately. It observes the Hugging Face repository HEAD
but the viewer response does not prove that revision, so real reproducibility
requires a pinned source workflow. No model, large archive, speaker identity search
or unrelated private dataset was accessed. Errors do not print response bodies.

The real manifest deliberately sets rights.status=pending, train/evaluate=false,
label_status=unreviewed and a provisional retention date equal to intake date.
It cannot be used for splitting until an authorized reviewer verifies the terms,
source revision, labels, identity links and retention and records appropriate
purpose approvals. The source's original train/validation/test designations are
metadata, not this project's approved lock. Automated retention deletion is absent.
The sample corpus is tiny English read speech and is not representative Darija/French
call-center material.

`python -m src.datasets` validates the metadata, optionally verifies a prior lock,
plans it, then opens the output with exclusive-create mode; an existing lock is
not overwritten. Invalid metadata/split policy exits nonzero without echoing
potentially sensitive invalid input. It does not parse or open audio.

## 5. Imports and dependencies

No runtime package was installed or version changed. Existing Pydantic2.11.3
provides BaseModel, ConfigDict, Field, StringConstraints and model_validator for
typed records and validation. `typing` provides Annotated/Literal; `datetime.date`
provides explicit review and as-of dates; `urllib.parse.urlsplit` checks terms URLs.

The splitter uses stdlib hashlib/json for canonical fingerprints and component
ranking, collections.defaultdict for groups and Pydantic Field for the lock schema.
The CLI uses argparse/date/pathlib and local Manifest/Lock functions. The bounded
public intake uses existing HTTPX0.28.1 for source calls, stdlib argparse, hashlib,
io, json, re, wave, datetime, pathlib and urlsplit for safe paths, SHA256 and WAV
lengths. `wave` reads the small public clips on intake only; manifest validation
and split planning do not open audio. Tests use existing pytest, HTTPX MockTransport,
unittest.mock and stdlib copy/hash/json/subprocess/sys/pathlib/date.

Hugging Face hosts the source and Parquet is a columnar file format shown in its
viewer. Neither `datasets` nor `pyarrow` is installed or imported; this step uses
public HTTP metadata and three bounded WAV examples, not a Parquet loader. Pydantic
and HTTPX were already declared runtime dependencies. No new database migration,
training library or GPU runtime is introduced.

## 6. Concepts explained

A manifest is a list of facts needed to decide whether a record may be used. It is
not the recording itself and a checked box is only as trustworthy as the reviewer
and evidence behind it. License coverage records the existence of a source license;
it does not establish an individual's consent or all privacy rights.

A speaker-disjoint split prevents one identified speaker from appearing in training
and held-out evaluation. If one conversation links speakers A and B, and B appears
in another conversation, the connected component groups all those records together.
Identical content hashes add another exact duplicate link. Pseudonyms must be
consistent; otherwise the software cannot prove that differently named entries are
different humans. A locked test set requires a trustworthy saved lock and external
hash; a newly generated file or an attacker-controlled expected hash is not immutable.

Darija and French may alternate in a single sentence. Preserve the reviewed original
script and language spans, then version an agreed normalization policy before WER.
Do not convert machine-only guesses into gold by changing a status field.

## 7. Dataset, privacy and rights evidence

Source and terms: [LibriSpeech OpenSLR](https://www.openslr.org/12/),
[LibriSpeech dataset card](https://huggingface.co/datasets/openslr/librispeech_asr),
[CC BY 4.0 terms](https://creativecommons.org/licenses/by/4.0/), and
[FLEURS dataset card](https://huggingface.co/datasets/google/fleurs). Mozilla's
[former Common Voice location](https://huggingface.co/datasets/mozilla-foundation/common_voice_17_0)
states that access moved to Mozilla Data Collective. The LibriSpeech card describes
English audio/text/speaker/chapter IDs and ASR training; CC BY permits adaptation
subject to attribution and other rights. Its annotation process is not sufficiently
documented for per-record human verification. Its card prohibits attempts to
determine speaker identities; the intake uses provided IDs only for grouping.

Actual intake: three clips, three distinct source speaker IDs/chapter IDs, English,
source subsets train.100/validation/test; bytes total788132; duration24.625s.
All three source license fields record CC BY 4.0, while rights statuses are pending,
train/evaluate approvals false and labels unreviewed. Their WAV bytes match the
recorded SHA256. The saved viewer references are public but are kept in an ignored
private index. Review the provisional 2026-10-28 retention date promptly; this step
cannot automatically remove retained files. There is no evidence of an approved
Darija/French corpus, gold review or real locked test split.

The repository's existing 10 educational/testing MP3 samples are excluded from
training by default: their README does not grant training permission or establish
gold transcripts/speaker linkage. Do not use customer calls for training based only
on an analysis request. Git ignore rules cover the selected private roots and common
audio extensions, but are not access control or protection for files elsewhere,
previously tracked data, or force-adds.

## 8. Tests and execution evidence

| Command / check | Actual result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest tests/datasets -q --tb=short` |25 passed,0 failed in4.10s; synthetic data and mocked HTTP |
| Full pytest: tests/unit tests/security tests/api tests/integration tests/workers tests/llm tests/datasets |326 passed,0 failed,0 skipped in147.02s; isolated PostgreSQL/Redis/S3 |
| Ruff check / format |0; all checks pass,137 Python files formatted |
| `mypy src/ services/ app.py` |0;69 source files; separate `mypy src/datasets scripts/inventory_librispeech_sample.py` passes5 files |
| `uv pip check --python .venv/Scripts/python.exe`; compileall; hardcoded-key check |0 each |
| Synthetic CLI with eight metadata records / no audio |Exit0;6 train,1 validation,1 test; current date/seed recorded |
| Public intake CLI |Exit0;3 WAVs,788132 bytes,24.625s, all pending/unreviewed |
| Real metadata validation, independent audio-hash verification and Git ignore checks |3 records validate without audio;3/3 hashes match in separate read; all intake files ignored |
| Real candidate split attempt |Exit1; no output lock created because rights and label review are pending |
| UI tests/screenshots |Not applicable: no frontend changes |

`evidence/step12-20261027T190603Z/` contains exact commands/results and JUnit output,
including the initial full-suite timeout at120s while Docker/services were starting.
That timed-out run had no completed pytest result; cause was not established. Once
services reported healthy,323 tests passed before the final intake changes, then
326 passed on the final code. An intermediate expired-date test fixture conflicted
with a newly added review-date validator; the fixture was corrected to represent
an actually expired but chronologically valid review. An earlier mypy variable-name
collision and initial formatting findings were fixed before final checks.
Starlette/AnyIO and pytest asyncio deprecation warnings remain nonfailing.

## 9. Actual analytics and metrics

- English candidate duration: **24.625/3600 = 0.00684028 hours**, n=3 clips.
  French and Darija: **0 recorded hours in this intake**, not a statement about all
  available datasets. This is a tiny convenience intake, not a representative corpus.
- License metadata coverage: **3/3 =100%** of these records cite the source's stated
  CC BY 4.0; project training/evaluation approvals **0/3 =0%**. License metadata
  coverage is not legal approval, consent verification or proof of label quality.
- Human label agreement: **Not measured**; no human-reviewed references or two-reviewer
  adjudications were performed. Human-verified labels **0/3**.
- Synthetic planner example:8 independent synthetic components,6/1/1 assignments,
  96 seconds of invented metadata. These are test fixtures, not real corpus hours.
  Additional tests verify transitive shared-speaker/conversation/hash grouping,
  disallowed rights, label status, retention, lock tampering and test-set bridges.
- Peak VRAM, WER, accuracy, training improvements, and real split leakage rate:
  **Not measured**. This step runs no neural inference/training; no verified real
  disjoint lock exists. The three sampled public source speaker IDs are distinct,
  but this does not establish disjointness of a future full corpus.

## 10. Questions and answers

1. **Why per-subset licensing?** A source can combine versions/subsets and individual
   restrictions; a single dataset-level label cannot attest all rights for each record.
2. **Why speaker-disjoint groups?** The same speaker in train/test can make evaluation
   appear stronger through identity characteristics rather than generalizable speech.
3. **How handle Darija script variation?** Preserve reviewed original script and
   explicit language spans; agree and version normalization before WER. Do not silently
   transliterate or translate code-switches.
4. **Why require both purposes?** The present planner can assign any group to any
   partition. Requiring both prevents a training-only item entering evaluation or an
   evaluation-only item entering training. Supporting one-purpose pools is future work.
5. **Is a permission flag proof of consent?** No. It is an operator assertion. An
   authorized person must verify underlying evidence, purpose, retention and applicable
   rights; this schema is not a legal approval or authenticated policy service.
6. **Can the lock prevent every change?** No. A checked prior lock preserves existing
   assignments and detects content/hash mismatch, but only a separately trusted hash
   and governance can stop someone making a new lock or replacing both values.
7. **Why are these real LibriSpeech labels not gold?** The dataset card does not
   establish per-record human review for the acquired viewer references. Their
   status remains unreviewed until independent review and provenance are documented.
8. **What can the hashes detect?** They connect byte-identical recordings. They do not
   detect other encodings, edited excerpts or the same person under different IDs.
9. **What failed during execution?** A chronological fixture mismatch and mypy naming
   issue were fixed; an initial full-suite timeout while services started had no final
   result. The final full run passed. No real-corpus acceptance was declared from it.
10. **Does this train a model?** No. It records metadata and intake only. No optimizer,
    gradient update, WER improvement or training authorization is claimed.

## 11. Decisions, risks and limitations

Use existing Pydantic/stdlib rather than add a large datasets/Parquet stack. Store
only metadata in manifests; keep actual files/index under an ignored root. Fail the
whole plan on a denied/unknown/expired record rather than silently omit it. Reject
changes and new links into a locked test group. These choices are conservative and
make review visible, but they require a later workflow for train-only/eval-only
material, withdrawals, re-approval and immutable lock administration.

Risks requiring action: current real records have pending rights/labels, no actual
approved test lock, no Darija/French gold, unpinned viewer revision, limited read-speech
representativeness, provisional retention due2026-10-28, no auto deletion, no live
training gate, trusted operator/reviewer IDs and potential unidentified cross-source
speakers/near duplicates. CC BY attribution and no-reidentification requirements must
be honored. Existing identity-provider/production limits from STEP11 remain.

## 12. Deliverables and next handoff

- [x] Source cards and actual terms/access observations documented with links.
- [x] Metadata schema validates without audio and forbids unknown fields.
- [x] Synthetic speaker/conversation/hash-disjoint groups and lock safeguards tested.
- [x] Actual public intake is ignored by Git, metadata-only validation passes,
      audio hashes match and unapproved split creation is refused.
- [x] Darija/French annotation and human-verification guidance written.
- [x] Final326-test regression, static checks and actual intake receipts retained.
- [ ] Independent reviewer confirms rights, retention, stable identity linkage and
      per-record human-reviewed labels for a sufficiently representative real corpus.
- [ ] Create and independently preserve the approved real train/validation/test lock.
- [ ] Verify a suitable Darija/French test set and frozen gold before STEP13 benchmark.

**Next eligible action is to finish STEP12 review**, not to claim STEP13 completed or
ready for a real benchmark. User-facing reviewable intake directory:
`data/datasets/librispeech-intake-20261028T091407Z/` (private/ignored). A reviewer
should inspect source-index/transcripts and recordings in authorized local storage,
verify project usage permissions and retention, and supply authenticated review
references. Three English clips alone are not sufficient target-language evidence.

## 13. Approved ERP UI design / visual contract verification

**Not applicable to visual implementation:** no UI component, route or CSS changed;
original Gradio remains the baseline. Schema/catalogue define future source,
permission and language information; future Model Lab must expose only authorized,
aggregate metadata and omit private audio paths, raw transcripts and reviewer
secrets. Empty/pending data must not be displayed as an approved corpus or fake KPI.
The approved primary reference remains `design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png`.
No actual frontend screenshots, token changes, responsive/keyboard or contrast
checks were performed because there is no new frontend surface in this step.

**Final status: STEP12 PARTIAL — pending real rights/label review and a reviewed
locked test set. STEP13 is not yet eligible for a real benchmark.**


## 14. Completion: reviewed public French benchmark (2026-10-28)

**Decision: DONE — PASS WITH LIMITATIONS.** The user selected an already reviewed public benchmark and specified retention through **2026-11-28**. The earlier LibriSpeech observations remain historical and correct for that separate intake. The selected Common Voice data and locally generated split now satisfy the three STEP12 done gates. This section supersedes statements above that no real approved lock exists, but does not reclassify LibriSpeech.

### What was built, source review and scope

`scripts/inventory_commonvoice22_fr.py` obtained nine short French clips and their source metadata from [Common Voice 22.0's unofficial Hugging Face mirror](https://huggingface.co/datasets/fsicoli/common_voice_22_0), pinned at `ae911de250fe9375d08e2daa2105b671d659d446`. The mirror explicitly identifies the corpus as CC0-1.0; [Mozilla's Common Voice terms](https://commonvoice.mozilla.org/phr/terms) describe contributions, including recordings and validation, as CC0. The source terms review is documented as `project28-source-terms-review`; the project records training and evaluation approval for this selected public sample, not unrelated private recordings. A CC0 declaration does not by itself resolve every privacy issue. Do not identify or re-identify contributors.

Each selected TSV row recorded at least two positive and no negative community votes. The manifest's `human_verified` means the source reports those community validations; the source index retains the actual vote counts and transcript. The project did not listen independently, audit individual voters, establish that every label is perfect, or measure inter-rater agreement. This is read French, not an actual call or Darija/code-switching speech. `conversation_id` is a shared-prompt identifier derived from `sentence_id`; it deliberately prevents shared prompts crossing splits but is not a real conversation ID. Source-supplied speaker pseudonyms are hashed for grouping, not identity verification or anonymization. These limits constrain interpretation and are not evidence of model accuracy.

### Files, code, dependencies and upstream comparison

- Added `scripts/inventory_commonvoice22_fr.py`: the CLI requires a new directory under ignored `data/datasets` and an explicit retention date; `fetch_range` accepts only bounded HTTP 206 responses and caps received bytes. `reviewed_clips` parses source TSV and reads only matching regular TAR members without extracting source paths. It requires published vote counts, source speaker/prompt IDs and French locale. The CLI pins a 40-character source revision, validates MP3 duration using Mutagen, writes audio with exclusive creation, hashes its bytes, then validates the metadata manifest. The private source index retains provenance and transcripts. It returns a generic error on common failures; partial outputs require manual review.
- Added `tests/datasets/test_commonvoice_intake.py`: synthetic TAR/TSV verifies filtering of low-vote and disputed rows, and an HTTP mock verifies rejection when a server ignores ranges. No real transcript is used in these tests. Existing manifest and split tests remain in place.
- Updated `docs/data/DATASET_CATALOG.md`, `docs/data/README.md`, this report and `docs/implementation/PROGRESS.md` with the source review, reproduction instructions, actual counts and limitations. Added `docs/implementation/evidence/step12-reviewed-20261028/` validation evidence. The audio, private source index, manifest and lock are ignored local files, not Git-tracked fixtures. No frontend file or API was changed; section 13's visual assessment remains applicable.
- New script imports: standard-library `argparse` (CLI), `csv`/`io` (bounded TSV and in-memory bytes), `hashlib` (stable metadata/audio digests), `json` (manifest and private index), `re` (revision validation), `tarfile` (read archive members), `date` (review/retention), and `Path` (controlled output). Existing pinned `httpx` 0.28.1 retrieves source content; existing `mutagen` 1.47.0 reads MP3 duration; local `Manifest` validates types and evidence. No dependency was added. The test adds standard `io` and `tarfile`, existing `pytest` and `httpx` mock transport, and the local intake functions. The sources are ordinary TSV/TAR/MP3; no Parquet or Hugging Face `datasets` import was required.
- Pinned upstream `fed4b610742c1337147281fcec8f2cdcc0a79be5` has no corresponding intake, permission schema or split planner. These additions are independent of the existing Gradio pipeline and introduce no training or model inference. Existing uncommitted changes from earlier steps were preserved; `git diff --stat` reports tracked changes across previous steps and does not include untracked additions.

### Executed verification and analytics

The actual intake command used `--output data/datasets/common-voice-22-fr-20261028-review --retention-until 2026-11-28`. Then `python -m src.datasets .../manifest.json --as-of 2026-10-28 --seed cv22-fr-v1 --output .../split-lock.json` validated metadata without reading audio and created a new lock. An independent inspection recomputed every audio SHA256, checked the nine source vote records, loaded the lock with its SHA256, recomputed the deterministic plan, and checked speakers, prompt groups and exact audio hashes for cross-split overlap. All checks passed; `git check-ignore` verified the manifest, source index and sample MP3 are ignored. The lock checksum was saved alongside the lock for convenience; **an adjacent checksum is not an independently trusted or immutable lock store**.

- 9 clips, 291,669 audio bytes, 4 source speaker pseudonyms and 9 shared-prompt groups; 4 train / 2 validation / 3 test records. Different source speakers can still be the same individual; cross-source identity cannot be established by these hashes.
- French duration: 36.408 seconds / 3,600 = 0.010113 hours, based on the nine local MP3 durations; this is an intake sample, not a benchmark for population estimates. The earlier baseline was no approved French audio. Darija/code-switch duration remains unmeasured.
- License coverage: 9 / 9 selected records = 100% have documented CC0 source terms and purpose approvals, not a claim about any other corpus. Community validation coverage: 9 / 9 meet this source-vote filter. **Inter-annotator agreement is not measured**; aggregate positive/negative votes are not an agreement statistic. No WER, model improvement, training time or VRAM metric was measured.
- Focused `python -m pytest tests/datasets -q`: **27 passed** in 2.19s. Full service-configured suite: **328 passed**, one warning, in 44.99s; JUnit XML and command outputs are in the evidence folder. A separate unconfigured `python -m pytest -q` run yielded **261 passed, 67 skipped**, one warning, in 28.19s; it is not represented as full integration coverage.
- Ruff check passed; Ruff format checked 139 files; strict mypy passed 69 application source files, and a separate mypy check passed the intake script. `uv pip check`, compileall and hardcoded-key checks passed. One exploratory `docker compose -f compose.local.yml ps` command failed because it did not supply the project's required `.env.docker` interpolation; this was not a service health test and no service was modified.
- Machine-readable source/sample and split evidence: `evidence/step12-reviewed-20261028/benchmark-validation.json`; test/check outputs and JUnit XML are in the same directory. The earlier sealed evidence is preserved.

### Questions, risks and handoff

1. **Why keep licenses per subset?** A mixture can contain sources with different permissions; approval is recorded for each selected record and purpose.
2. **Why split by speaker?** Reusing a recorded speaker across training and test can inflate apparent generalization; linked records remain together.
3. **How are Darija script variants handled?** The annotation guide specifies human-reviewed language spans and normalization choices before scoring; this French-only intake does not validate Darija.
4. **Are community votes independent project review?** No. They are source-published human validation evidence; the reviewers' individual identities and agreement are not independently verified.
5. **Why group prompts as conversations?** These clips are independent read utterances with no call ID; shared prompts are grouped conservatively, without asserting an actual conversation.
6. **Does the checksum enforce a permanent test set?** No. Verification detects changed bytes relative to a trusted checksum, but a checksum stored beside the file can also be changed. Independent retention and governance remain future work.
7. **Can this sample prove production quality?** No. Four speakers and nine French read clips are too small and unlike customer calls. A separately permissioned, representative evaluation set is necessary.

The retention date is a review deadline, not an automatic deletion mechanism. Revalidate permissions against the real current date before any training/evaluation, arrange retention handling and independently trusted lock storage, and obtain appropriately consented, representative call-center/Darija/French material before making domain claims. The unrelated LibriSpeech intake remains pending and expired provisional retention requires owner review. STEP_13 is the next numbered step, subject to its own prerequisites and the limitations above; it was not executed.

Evidence checklist: [catalogue](../../data/DATASET_CATALOG.md), [annotation guide](../../data/ANNOTATION_GUIDE.md), [dataset tooling](../../../src/datasets/), [intake code](../../../scripts/inventory_commonvoice22_fr.py), [validation evidence](evidence/step12-reviewed-20261028/benchmark-validation.json). No commits, pushes, model downloads or training were performed.
