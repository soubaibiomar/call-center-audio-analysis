# Darija specialist comparison — source review and frozen protocol

Date: 2026-10-29. Scope: user-authorized local non-commercial inference evaluation.
This review records published provenance; it does not certify every underlying
recording permission or prove that public test media was absent from pretraining.

## Selected checkpoints

| Candidate | Pinned revision | Published model license | Declared provenance |
|---|---|---|---|
| [AtlasIA MoulSot v0.3](https://huggingface.co/atlasia/moulsot.v0.3) | `8ae8d752ab4218c84e59a7b2ce69becb30cc6393` | Apache-2.0 | Qwen3-ASR Darija adaptation using MoulSot-Full media speech |
| [Anass-Srk Darija Whisper Small](https://huggingface.co/Anass-Srk/fine-tuned-whisper-small-darija) | `d3c4fd5048c5f182dea49e4af8670037a699cfe6` | Apache-2.0 | Whisper Small adapted on the author's stated DVoice Darija v2.0 dataset |

The user approved approximately 5.1 GB of weights for these two checkpoints.
Only safetensors and required configuration/tokenizer files are loaded. Training
pickles and duplicate PyTorch weight files are excluded. No local training occurs.

The [MoulSot-Full dataset card](https://huggingface.co/datasets/atlasia/MoulSot-Full)
describes automatic Gemini 2.5 Pro transcription, preserving Latin-script French
and English words. Therefore training-reference provenance must not be described
as independently human-verified by this project. The model card's quality claims
and the Whisper author's own evaluation scores are publisher results on other
protocols/data, not results of this comparison. Exact upstream recording rights,
train/test identities and source-media overlap have not been independently audited.

Other checkpoints were considered. The
[Qwen2-Audio Darija multitask card](https://huggingface.co/Tilas/qwen2audio-darija-multitask)
declares Casablanca training; record-level train/test separation is not resolved
by the card, so it was not selected for this Casablanca evaluation. Other Qwen
replicas add another multi-gigabyte download from the same adaptation family;
the original explicitly licensed MoulSot checkpoint is the selected representative.

## Fresh project test sample

Source: [UBC-NLP/Casablanca](https://huggingface.co/datasets/UBC-NLP/Casablanca),
revision `8951b1b88e28c1107142ced57967b8d16350951d`, `Morocco/test`.
Published license: CC BY-NC-ND 4.0. Use here is local non-commercial evaluation;
no audio/reference redistribution or training is authorized by this manifest.
Local retention ends 2026-11-28. Publisher transcription provenance is retained,
without claiming an independent human listening audit.

One hundred unique clips were selected by a fixed hash rank before model runs.
They exclude all prior clip IDs, raw and normalized reference duplicates, matching
audio hashes and source-segment prefixes. The resulting sample has 100 distinct
prefix groups, approximately 413.9 seconds of audio, and 73.02 MB of stored audio.
Prefix groups do not prove independent episodes or speakers. The sample is fresh
to this project's comparison; it is not proven unseen by every checkpoint creator.
These are broadcast clips, not a permissioned Moroccan telephone-call corpus.

The previous 40 source/reference mappings were rechecked. Five audio files were
re-downloaded and matched their prior SHA-256 values. Their stereo downmix checks
showed correlations of approximately 0.963–1.000 and no substantial phase
cancellation. This checks source mapping/bytes and audio handling, not semantic
correctness of every reference. See `prior-mapping-audit.json` and `disjointness.json`.

## Planned matched comparisons

- Whisper Small base versus DVoice-adapted Whisper Small, both in FP16 CTranslate2.
  The specialist conversion is an offline export, not training; `conversion.json`
  records the parent revision, tool versions and derived-file hashes.
- Qwen3-ASR 1.7B base versus MoulSot, both requesting BF16 in the same pinned
  Qwen runtime. Parameter dtype counts are captured when the wrapper exposes them.
- Whisper Turbo is the additional faster general-model reference.

All models receive the same frozen sample, known Arabic decoding hint, common
normalization and one pass. The Arabic mode is used for Darija; no separate
language-identification accuracy is evaluated. Qwen's token budget is 256.
Whisper uses beam 1, temperature fixed explicitly to zero, previous-text
conditioning disabled and no VAD filter.
Runtime network access is disabled and GPU jobs are serial. Previously authorized
temporary Ollama interruption frees GPU memory; the driver restores its running
state in `finally` after the jobs.

Model loading and a one-second synthetic-silence warmup are excluded from timed
speech observations. The warmup output is separately recorded as a limited
negative control, not a complete no-speech safety evaluation. Private predictions
remain under `.local/` for later review; public evidence contains counts/hashes.

Primary metrics are the previous multilingual experiment's reference-weighted
WER/CER, using NFKC/casefold, punctuation boundaries and removal of Arabic
diacritics/tatweel while retaining distinct letters and French accents. Script,
spelling and clitic-boundary variations can still be penalized. Raw strict counts
are retained. No dictionary or semantic correction is tuned to the test labels.

Paired candidate-minus-baseline WER differences use 5,000 source-prefix-group
bootstrap resamples with seed 20261029. The intervals are conditional on this
sample and the group-independence assumption; they are not guarantees about real
call-center speech or unseen speakers. No model is automatically promoted from
this research comparison.

## Decoding-default correction

Installed faster-whisper code inspection showed that beam 1 alone still permits
the library's default temperature/sampling fallback. The initial attempt was
interrupted before its scores were interpreted or selected. Its partial outputs
and original protocol remain in `initial-default-fallback-attempt/`. Protocol v2
sets the zero-temperature option explicitly and reruns every primary checkpoint
on the unchanged frozen data. `protocol.json` records the new code hashes and
the correction; raw primary reports record the policy and runner hash. This
correction does not rewrite the earlier English or multilingual benchmark results.
