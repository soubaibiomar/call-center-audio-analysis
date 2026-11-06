# Dataset source and permission inventory — STEP12

**2026-10-29 Darija specialist follow-up:** A separate frozen sample adds 100
Casablanca `Morocco/test` broadcast clips (413.9006 seconds), excluding the prior
40 project clips, reference/audio hashes and source prefixes. All five local
model comparisons completed. See the
[Darija specialist report](../benchmarks/DARIJA_SPECIALIST_COMPARISON_20261029.md).
This sample is local non-commercial evaluation only, with no training or
redistribution and retention through 2026-11-28. Prefix separation does not prove
speaker/episode independence or absence from model training. It is not a real
Moroccan telephone benchmark; publisher references were not independently
relabelled by this project. Earlier candidate statuses remain historical intake
records, not a statement that this later evaluation acquired no data.

**2026-10-29 evaluation update:** The earlier candidate statuses below describe
the STEP_12 intake. A separate, evaluation-only multilingual comparison now uses
40 French Common Voice 22 test clips, 40 FLEURS `ar_eg` test clips and 40
Casablanca `Morocco` test clips. See
[the multilingual benchmark report](../benchmarks/MULTILINGUAL_ASR_COMPARISON_20261029.md)
for pinned revisions, source review, selection, actual results and limitations.
The evaluation manifest grants no new training permissions. Casablanca remains
restricted to this local non-commercial research evaluation; source audio and
references stay in ignored storage, with retention through 2026-11-28. Published
reference provenance is recorded without claiming independent listening or
manual verification by this project.

Reviewed source pages on 2026-10-27 and 2026-10-28. This is an intake catalogue,
The Common Voice entry below is now approved for the stated limited purposes; the other candidates retain their earlier status. Three small public LibriSpeech clips and their
unreviewed source references were acquired on 2026-10-28 into Git-ignored storage.
A license does not itself confirm every privacy, consent or contractual permission.
A designated reviewer must record purpose-specific approval, source version/subset,
evidence, identity mappings and retention before creating a usable manifest.

| Source/subset | Published source / availability | License and permitted purposes | Local review and limitations |
| --- | --- | --- | --- |
| Google FLEURS, French/Arabic subsets | [Dataset card](https://huggingface.co/datasets/google/fleurs) lists audio+text, train/validation/test and Parquet. No data acquired. | Card states CC BY 4.0; [Creative Commons](https://creativecommons.org/licenses/by/4.0/) permits sharing/adaptation subject to attribution and other rights. Review the precise subset/version and privacy constraints. | Candidate only; no reviewer approval. Viewer fields inspected do not expose a speaker ID; independent speaker-disjoint partitioning cannot be proved until reliable identity provenance is supplied. Arabic is not evidence of Moroccan Darija or call-center representativeness. Card lists multiple annotation-creation methods; review labels per record before calling them gold. |
| LibriSpeech SLR12, clean/other subsets | [OpenSLR](https://www.openslr.org/12/) lists train/dev/test archives; [dataset card](https://huggingface.co/datasets/openslr/librispeech_asr) describes audio, transcripts, speaker and chapter IDs. Three public clips acquired from train.100/validation/test as a bounded intake. | Source states CC BY 4.0 and its dataset card describes ASR model training; attribution/other rights and exact subset/version still need review for the intended project purpose. | Candidate only; English read speech, not a Darija/French call-center gold set. Speaker mapping and verified transcript provenance must be reviewed before splitting. |
| Mozilla Common Voice 17 | [Former Hugging Face location](https://huggingface.co/datasets/mozilla-foundation/common_voice_17_0) states files are empty and availability moved to Mozilla Data Collective. | Exact version/subset license, access/terms and training purposes **not verified** here. | Blocked pending current access conditions, subset-specific terms, reliable speaker identities, label review and approved provenance. |
| Repository `data/samples` | Existing 10 MP3 files; README says educational/testing use. No transcripts or speaker provenance established here. | The README does not grant model training. | Excluded from any training/evaluation manifest until independently reviewed and purpose-specific permission and gold labels are documented. Existing samples were not modified. |
| Customer recordings | Not inspected. | Analysis permission does not imply training consent. | Denied by default until authorized reviewers provide purpose-specific permission, retention and secure identity/label provenance. |

Three real public records total 24.625 seconds (0.00684 hours), with three source
speaker IDs and three chapter IDs. Audio hashes match the downloaded viewer WAV
bytes. All three permissions and reference labels remain pending/unreviewed; there
are zero approved training or evaluation records and no real locked split. The
viewer response was not pinned to the repository revision; the manifest records the
observed repository HEAD, not a proven viewer snapshot. Source IDs are public
pseudonyms, not anonymization. No Darija or French corpus hours are established.
LibriSpeech was prepared by Vassil Panayotov, Guoguo Chen, Daniel Povey and
Sanjeev Khudanpur; cite [the dataset card and ICASSP 2015 citation](https://huggingface.co/datasets/openslr/librispeech_asr).
The dataset card instructs users not to attempt to determine speakers' identities.
Use its provided speaker IDs solely for disjoint grouping; do not re-identify or
link them to real individuals. Cross-source linkage remains unknown when resolving
it would require prohibited identity investigation.

The above historical LibriSpeech section asserts no approved records or training-ready corpus hours for that intake; the reviewed French benchmark is described below. Source-level published
license availability is not record-level approval. `datasets` and `pyarrow` are not
installed in this environment and no Hugging Face loader or Parquet reader is used;
future acquisition must pin a revision and review schema and access conditions.

## Reviewed French benchmark — 2026-10-28

Nine Common Voice 22.0 French clips were selected from the [unofficial versioned mirror](https://huggingface.co/datasets/fsicoli/common_voice_22_0) at revision `ae911de250fe9375d08e2daa2105b671d659d446`. The mirror declares CC0-1.0; [Mozilla terms](https://commonvoice.mozilla.org/phr/terms) describe CC0 contributions including recordings and validations. The user selected a reviewed public benchmark and a 2026-11-28 retention deadline. This source-level review records training/evaluation approval for these nine clips, subject to the source terms and applicable privacy rights; it does not establish consent for unrelated customer data. Use speaker pseudonyms for split grouping only; do not re-identify participants.

Each chosen source row has at least two published positive community votes and no negative votes. Those votes are source-published evidence of community validation, not evidence that this project independently listened to each clip or measured inter-annotator agreement. The manifest uses `human_verified` for that community-reviewed provenance; its private source index preserves the source text, IDs and vote counts. It is French read speech, not Darija, code-switched speech, or call-center conversation. Its prompt-based conversation key is a conservative shared-prompt grouping, not a claim that clips come from actual calls. There are 9 clips, 4 pseudonymous speakers, 36.408 seconds (0.010113 hours), and split counts 4 train / 2 validation / 3 test. The tiny nonrepresentative sample cannot support reliable model quality or customer-domain claims. The previously described LibriSpeech intake remains pending, with no new permissions inferred.

## STEP_20 emotion evaluation sources — 2026-10-29

See [source review](EMOTION_SOURCE_REVIEW.md). A bounded evaluation-only intake contains 16 CREMA-D acted-English clips (ODbL/DbCL) and 16 MDER-MA Darija media clips (original Mendeley v1 CC BY 4.0; acquired via a pinned mirror). Human label provenance is source-published; no independent project relabeling, training or telephone-domain authorization is inferred. Selection used four classes, adult-age metadata for MDER-MA, and an existing project retention review deadline of 2026-11-28. These are not real Moroccan telephone calls. Source hashes, labels and record-purpose notes live in the ignored local manifest; public metrics must retain this scope.
