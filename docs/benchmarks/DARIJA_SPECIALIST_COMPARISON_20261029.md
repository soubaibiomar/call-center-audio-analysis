# Local Darija specialist ASR comparison — 2026-10-29

## Outcome

MoulSot v0.3 is the strongest Darija research candidate tested here. On the same
100 fresh clips, it reduced normalized word error from Qwen3-ASR 1.7B's 86.25%
to 53.93%: **32.32 percentage points, approximately 37.5% relative reduction**.
Its aggregate inference time was about 9.4% higher. This is a useful measured
upgrade, but 53.93% word error does not support unattended call transcription.

The Darija Whisper Small adaptation did not establish a convincing improvement:
its paired word-error interval includes zero, and character error worsened.
Application defaults were left unchanged. This is a benchmark follow-up, not a
new numbered implementation step or a production promotion.

## Data, provenance and permitted scope

The frozen sample contains **100 clips, 413.9006 seconds (6.90 minutes), 1,411
normalized reference words and 100 distinct source-prefix groups**. It uses
[UBC-NLP/Casablanca](https://huggingface.co/datasets/UBC-NLP/Casablanca),
`Morocco/test`, revision `8951b1b88e28c1107142ced57967b8d16350951d`.
The publisher identifies this as Moroccan Darija broadcast speech. These are
not real customer telephone recordings. References retain publisher annotation
provenance; this project did not independently listen to and relabel them.

Selection used a fixed hash rank before inference. All 40 previous project test
clip IDs, source prefixes, matching reference hashes (raw and normalized) and
audio hashes were excluded. Recorded overlap counts are zero. Prefixes do not
prove distinct speakers or episodes. Freshness to this project does not prove
absence from checkpoint training or pretraining.

Manifest SHA-256:
`cdeb7d8d47b895598dcede04d966c64f27f04fd16af7ba9ed9f582d896d59c68`.
Stored audio occupies 73,015,908 bytes. Audio, references and prediction text
remain in ignored `.local/darija-specialist-20261029/`; public evidence contains
counts, source identifiers and hashes. The manifest permits local non-commercial
evaluation only, no training or redistribution, with retention through
**2026-11-28**. The dataset's published CC BY-NC-ND 4.0 terms and other applicable
rights remain relevant; this evaluation creates no commercial deployment rights.
See [source review](evidence/darija-specialist-20261029/SOURCE_REVIEW.md).

The earlier 40 ID/reference mappings were checked against publisher metadata;
five audio files were downloaded again and matched their previous hashes.
Those five stereo checks found channel correlations approximately 0.963–1.000
and no substantial downmix cancellation. This validates mapping and byte/audio
handling for those checks, not the semantic correctness of every label.

## Checkpoints and local runtime

| Model | Pinned source revision |
|---|---|
| Whisper Small base, Systran CTranslate2 export | `536b0662742c02347bc0e980a01041f333bce120` |
| [Anass-Srk Darija Whisper Small](https://huggingface.co/Anass-Srk/fine-tuned-whisper-small-darija) | `d3c4fd5048c5f182dea49e4af8670037a699cfe6` |
| [Whisper Turbo, Dropbox export](https://huggingface.co/dropbox-dash/faster-whisper-large-v3-turbo) | `0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf` |
| [Qwen3-ASR 1.7B](https://huggingface.co/Qwen/Qwen3-ASR-1.7B) | `7278e1e70fe206f11671096ffdd38061171dd6e5` |
| [AtlasIA MoulSot v0.3](https://huggingface.co/atlasia/moulsot.v0.3) | `8ae8d752ab4218c84e59a7b2ce69becb30cc6393` |

The user authorized both new downloads. Their model cards declare Apache-2.0.
The Whisper author describes DVoice Darija v2.0 adaptation. The
[MoulSot-Full card](https://huggingface.co/datasets/atlasia/MoulSot-Full) describes
automated Gemini 2.5 Pro transcription; this is training provenance, not an
independently human-verified gold set. Exact training identities and underlying
recording rights were not independently audited. No local training occurred.
Whisper's conversion was an offline FP16 CTranslate2 export, with parent and
derived-file hashes recorded in `conversion.json`.

Inference ran on the user's laptop: **NVIDIA RTX 4060 Laptop GPU, 8,188 MiB,
driver 610.88**, in serial Docker jobs with network disabled. Whisper used
faster-whisper 1.2.1 / CTranslate2 4.8.4. Qwen used qwen-asr 0.0.6,
Transformers 4.57.6 and PyTorch 2.14.0+cu130. Both Qwen checkpoints actually
held **2,038,052,480 parameters in BF16**, as captured in the reports.
No new runtime dependency was installed for this follow-up.

Image identities and Git context are recorded in
[environment.json](evidence/darija-specialist-20261029/environment.json).
The temporarily stopped Ollama container was restored; its local API returned
HTTP 200 after completion. No hosted inference service processed this sample.

## Matched protocol and correction

Protocol version 2 was frozen at `2026-10-29T20:52:52.579450+00:00`, before all
five primary runs. It records the manifest and five source-file hashes.
Every model received the same mono, 16 kHz input, known Arabic language hint
(including Darija), no VAD and one pass. Whisper used FP16, beam 1, explicit
temperature 0 and previous-text conditioning disabled. Qwen used BF16 greedy
decoding with a 256-token maximum. This does not evaluate language detection.

Audio preparation, model loading and a separate one-second synthetic-silence
warmup were excluded from speech inference timing. RTF is total measured
inference seconds divided by total input-audio seconds. Median clip latency
is not end-to-end call latency; sampled peak GPU memory is an observed peak,
not a worst-case capacity guarantee.

Code inspection caught that faster-whisper's default temperature fallback can
sample despite beam 1. The initial attempt was interrupted before its scores
were interpreted or selected, preserved under `initial-default-fallback-attempt/`,
and replaced by all five primary runs using explicit temperature 0 on unchanged
data. Older English/multilingual reports retain their actual runs and library
defaults. Their different data, precision and decoding settings must not be
treated as matched measurements against this study.

WER is reference-weighted word edit distance divided by reference word count;
CER uses character edits. Insertions can make WER exceed 100%. Common scoring
uses Unicode NFKC/casefold, punctuation boundaries and removal of Arabic marks
and tatweel. It retains French accents, digits and distinct Arabic letters.
Strict NFC counts are also retained. No reference-tuned dictionary, translation
or semantic correction was applied. Spelling and clitic boundaries still matter.

## Executed results

| Model | Word error | Character error | Median clip seconds | RTF | Peak GPU MiB |
|---|---:|---:|---:|---:|---:|
| Whisper Small base | 99.50% | 54.82% | 0.227 | 0.0617 | 960 |
| Whisper Small / DVoice Darija | 94.33% | 55.62% | 0.210 | 0.0547 | 960 |
| Whisper Turbo base | 100.35% | 55.96% | 0.328 | 0.0841 | 2364 |
| Qwen3-ASR 1.7B base BF16 | 86.25% | 39.64% | 0.859 | 0.2290 | 4735 |
| MoulSot v0.3 BF16 | 53.93% | 20.89% | 0.934 | 0.2505 | 4562 |

All models completed all 100 speech clips. Lower error and RTF are better.
The summary is generated from raw counts, not averages of per-clip percentages.

Candidate-minus-baseline WER differences use 5,000 paired source-prefix-group
bootstrap resamples, seed 20261029. Negative favors the candidate.

| Comparison | Difference, percentage points | Conditional paired 95% interval |
|---|---:|---:|
| Darija Whisper Small versus Small base | -5.17 | [-19.67, 6.11] |
| MoulSot versus Qwen base | -32.32 | [-35.59, -29.20] |
| MoulSot versus Turbo | -46.42 | [-82.05, -28.83] |

These intervals assume the prefix groups are independent. They describe this
source/sample, not real-call or unseen-speaker performance. Large insertion
outliers contribute to the wide Turbo comparison interval.

Every model emitted text on the one-second zero-audio control with VAD disabled:
329, 335, 16, 4 and 11 characters respectively in the table's order. This is a
limited negative control, not a measured false-positive rate or a test of the
application's existing VAD. Validate silence/noise rejection before integration.

## Implementation and comparison with existing code

The original upstream application does not provide this matched local specialist
evaluation. This follow-up extends the existing benchmark tooling rather than
changing its production transcription route. Existing English scoring defaults
remain the defaults; BF16, private prediction capture and strict Whisper decoding
are explicit benchmark options. No frontend changed, so UI screenshots do not apply.

| New or modified file | Important behavior and rationale |
|---|---|
| `scripts/download_upgrade_models.py` (modified) | Adds pinned candidate IDs; `fetch_range_bytes` checks range/status/size before accepting bytes; bounded worker pool and shared HTTPX client resume downloads; `digest` verifies file hashes. Safetensors avoids downloading duplicate pickle weights. |
| `scripts/intake_darija_specialist_benchmark.py` (new) | `prefix` and `eligible` exclude prior source groups and references; `fetch_audio` restricts the source host/revision; `main` freezes metadata, hashes, disjointness and mapping checks. |
| `scripts/convert_darija_whisper.py` (new) | `main` rejects an existing destination or wrong source revision, exports FP16 weights and saves the fast tokenizer and file receipt offline with remote code disabled. |
| `scripts/benchmark_upgrade_asr.py` (modified) | Optional precision/decoding controls, actual dtype counts, source hash, silence control and private prediction JSONL. Existing manifest validation and normalization remain shared. |
| `scripts/run_darija_specialist_benchmarks.ps1` (new) | Runs five isolated jobs serially, captures commands/exit codes, preserves existing outputs and restores Ollama in `finally`. |
| `scripts/summarize_darija_specialist_benchmarks.py` (new) | Validates matched inputs/policy; `paired_interval` resamples shared groups and weighted denominators; `main` writes summary and tables. |
| `tests/unit/test_darija_specialist_protocol.py` (new) | Seven focused checks cover exclusions, download range validation, weighted paired intervals and private output-path restrictions. |
| This report, evidence directory and `docs/data/DATASET_CATALOG.md` | Record actual execution, source/rights scope, limitations and reproducible interpretation. |

Standard-library `hashlib`, `json`, `pathlib`, `random` and `math` provide receipts,
paths and deterministic resampling. `concurrent.futures` bounds concurrent
downloads. Existing HTTPX/Hugging Face Hub dependencies retrieve pinned files;
SoundFile reads audio; CTranslate2/Transformers perform conversion and inference.
Shared intake/scoring imports keep this comparison consistent with existing
benchmark definitions. No new application dependency or infrastructure is needed.

The workspace contains earlier uncommitted implementation work; this report's
file inventory describes this follow-up, not the entire repository diff. No
commit, push or history rewrite was performed. Frozen source hashes identify
the evaluated code despite the uncommitted workspace.

## Verification and reproduction

Actual final results in [verification.json](evidence/darija-specialist-20261029/verification.json):

- Ruff check passed; formatting check passed for all six scoped Python files.
- Python compilation passed.
- **42 tests passed in 4.66 seconds, none skipped**, across specialist protocol,
  multilingual protocol, upgrade protocol, ASR benchmark and audio preprocessing.
- Five primary inference jobs exited 0; all 500 public/private prediction hashes,
  manifest hashes, common decoding policy and frozen runner/source hashes matched.
- PowerShell driver parsed successfully. Ignored-storage checks passed.
- Pytest emitted an existing unset asynchronous fixture-loop-scope deprecation
  warning. These scoped synchronous checks passed; this is not a full API,
  database, frontend or production regression-suite result.

After the pinned downloads and offline conversion, reproduce from the project
root in PowerShell (preserve or move prior outputs before intentionally rerunning):

```powershell
./scripts/run_darija_specialist_benchmarks.ps1
./.venv/Scripts/python.exe -m scripts.summarize_darija_specialist_benchmarks
./.venv/Scripts/python.exe -m pytest tests/unit/test_darija_specialist_protocol.py tests/unit/test_multilingual_benchmark.py tests/unit/test_upgrade_benchmark_protocol.py tests/datasets/test_asr_benchmark.py tests/unit/test_audio_preprocessing.py -q -rs
```

The driver reuses complete same-manifest reports; that is not a new timed run.
Inspect `execution.json` for actual Docker arguments and timestamps, `protocol.json`
for frozen sources, `conversion.json` for export provenance, individual model JSON
files for per-clip counts, and `summary.json` for aggregate metrics and intervals.
Receipts and code remain usable after retention expiry; reacquiring the sample
requires renewed purpose/retention review.

## Limitations and next actions

1. Accuracy remains insufficient. Treat MoulSot as a Darija research candidate,
   requiring human review; no automatic production promotion is justified.
2. The sample is small broadcast speech. Obtain a permissioned Moroccan telephone
   benchmark with reviewed transcripts, speaker/conversation grouping, noise and
   code-switch coverage before making call-center claims. No suitable usable
   real-call benchmark was established in this source review.
3. Public-media training overlap and label/orthographic variation remain unresolved.
   Audit provenance and independently review errors; do not infer semantic accuracy
   from CER or change reference normalization to improve this test's score.
4. All five raw models produced text on silence without VAD. Evaluate the existing
   intake's speech gate against silence, music and background noise before routing.
5. One pass and short clips do not establish repeatability, long-call latency,
   concurrent capacity or multilingual automatic routing. Keep the prior French/MSA
   measurements as separate evidence; this follow-up tests Darija only.
6. No training uses this frozen evaluation sample. Any future adaptation needs a
   separate permissioned training corpus and a newly untouched final holdout.
   Keep the stated non-commercial restriction and retention deadline visible.

### Technical questions

**Why test MoulSot against Qwen at the same precision?** It isolates the adaptation
more closely: both use the same runtime, BF16 parameter storage, input and decode
budget. Different training data still prevents attributing gain to one technique.

**Why can WER exceed 100%?** Inserted words add errors beyond the number of reference
words. Capping would hide failures; the raw edit counts are retained.

**Does a lower CER mean the transcript is safe to use?** No. CER measures character
edits, not factual meaning, names, amounts or downstream decision correctness.

**Why not choose the faster small adaptation?** Its WER difference is uncertain
on this sample and its CER is worse, while absolute error remains very high.
Speed alone does not meet the user's accuracy objective.

**Can this sample be used for fine-tuning?** Not under this manifest. It is a frozen,
non-commercial evaluation sample; training would also destroy its holdout role.

**What is the next eligible action?** Review MoulSot errors and validate a separate
permissioned telephone holdout plus speech/noise rejection. Numbered Project 28
progress and production defaults are unchanged by this benchmark.
