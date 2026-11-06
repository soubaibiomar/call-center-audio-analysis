# French, standard Arabic and Darija — local ASR comparison

Date: 29 October 2026. Status: all six model executions completed. Scope: an evaluation adjunct, with no numbered implementation step advanced and no application default changed.

## Findings and recommendation

- **French: Parakeet is the best observed speed/accuracy tradeoff.** Word error was 3.60%, versus Qwen3-ASR 1.7B's 3.08%. Parakeet used 0.0159 inference seconds per audio second, about 8.8 times faster. Qwen 1.7B had two fewer word errors across the 389 normalized reference words; Parakeet had the lower character error.
- **Standard Arabic: Qwen3-ASR 1.7B for accuracy; Whisper Turbo for lower latency and memory.** Their word errors were 9.52% and 12.50%. Turbo was about 3.2 times faster by aggregate real-time factor. These are MSA read-speech results, not Moroccan telephone-call acceptance.
- **Darija: none of the tested configurations demonstrated reliable recognition.** The lowest observed word error was Qwen 1.7B's 82.89%, with 37.08% character error. I would require Darija-specific adaptation and fresh target-call validation before unattended use. Parakeet was excluded from Arabic/Darija evaluation because Arabic is absent from its listed supported languages.

Keep the current production configuration while validating a French Parakeet pilot and the Arabic accuracy/latency choice. This evaluation does not automatically introduce a language router or approve deployment.

## Data and permissions

All models saw the same frozen examples within each language: 120 unique audio clips in total, approximately 13.35 minutes. References came from the publishers; this project did not independently listen to and verify all clips. Training, audio redistribution and commercial use of the restricted Darija subset were excluded. Local retention is 28 November 2026. Raw audio and reference text remain in Git-ignored storage.

| Language | Source, split and domain | Clips | Audio seconds | Normalized reference words | Published license |
|---|---|---:|---:|---:|---|
| French | Common Voice 22, test; community-validated read speech | 40 | 204.36 | 389 | CC0-1.0 |
| Standard Arabic | FLEURS `ar_eg`, test; read speech, Egyptian locale | 40 | 408.22 | 704 | CC BY 4.0 |
| Moroccan Darija | Casablanca `Morocco`, test; broadcast speech | 40 | 188.33 | 596 | CC BY-NC-ND 4.0 |

French has 21 source-pseudonymous speakers and 40 distinct reference strings. Arabic has 39 distinct reference strings among 40 clips; speaker identifiers were not available. Darija has 40 distinct reference strings; independent speaker/episode counts were not established. Forty clips must not be described as forty independent calls or speakers.

The French FLEURS dataset viewer returned a server error: its approximately 445 MB Parquet scan exceeded a 300 MB service limit. Instead of downloading that entire file, the intake reused the already reviewed Common Voice release. French selection takes the first 40 matching test archive entries in a bounded 32 MB prefix, requiring at least two positive community votes and zero negative votes. This is a prefix sample, not a uniform sample of the complete French test set. Arabic and Darija selection uses a fixed SHA-256 rank across the complete pinned test metadata, retaining 2–20-second clips with at least three reference words. Selection and normalization were fixed before model results were observed.

New stored audio totals 60,988,324 bytes. Viewer `x-revision` headers and audio URLs were checked against pinned dataset revisions; local audio and reference hashes were then checked before inference. All records use an evaluation-only manifest schema, preserving the existing training-intake gates.

## Protocol and metric definitions

RTX 4060 Laptop GPU, 8,188 MiB. Docker GPU inference ran one model at a time. With the user's existing authorization, Ollama was temporarily stopped to release its allocated GPU memory and restarted after the jobs; its API was verified reachable afterward. No other service configuration was changed.

All inference used local cached weights and network-disabled containers. Audio was decoded, downmixed to mono and resampled to 16 kHz before timing. Clips were processed separately, with a 30-second maximum chunk. One complete pass per model was run, with 40 measured clips per evaluated language. A separate one-second silence warmup and model loading were excluded from timed observations. Whisper uses FP16, beam 1, no VAD filter, no previous-text conditioning and a known `fr` or `ar` language hint. Qwen uses FP16, a 256-token generation limit and a known French/Arabic hint; Darija uses Arabic decoding mode because there is no separate Darija option. Parakeet uses native FP16 TDT generation and was evaluated only on French. There was no hyperparameter search against the observed scores.

Primary scoring applies Unicode NFKC, casefolding, punctuation/symbol boundaries and whitespace normalization; Arabic diacritics and tatweel are removed. French accents and distinct Arabic letters are preserved. No transliteration, translation, spelling dictionary or semantic equivalence correction is applied. Raw NFC/punctuation-retained error counts are also saved for audit. **These normalized percentages are not directly comparable to the earlier English report's punctuation-retained percentages.**

WER is summed word-level Levenshtein errors divided by summed reference words; CER is the analogous character metric. RTF is total inference time divided by total audio duration; lower is faster. Error rates are reference-weighted, not averages of clip percentages. Median and nearest-rank p95 clip latency are recorded; startup and sampled whole-device GPU peaks are separate. GPU peaks are sampled, not exact isolated-model memory requirements.

The following tables are rendered from the complete execution receipts by `scripts/summarize_multilingual_benchmarks.py`.

## French

| Model | Word error | Character error | Median clip seconds | RTF |
|---|---:|---:|---:|---:|
| Whisper Tiny | 33.93% | 15.83% | 0.090 | 0.0208 |
| Whisper Small | 9.77% | 5.17% | 0.153 | 0.0318 |
| Whisper Turbo | 6.68% | 3.90% | 0.294 | 0.0584 |
| Qwen3-ASR 0.6B | 6.17% | 2.31% | 0.544 | 0.1160 |
| Qwen3-ASR 1.7B | 3.08% | 1.50% | 0.669 | 0.1393 |
| Parakeet TDT v3 | 3.60% | 1.13% | 0.074 | 0.0159 |

## Standard Arabic

| Model | Word error | Character error | Median clip seconds | RTF |
|---|---:|---:|---:|---:|
| Whisper Tiny | 67.47% | 26.40% | 0.160 | 0.0159 |
| Whisper Small | 30.68% | 9.43% | 0.298 | 0.0320 |
| Whisper Turbo | 12.50% | 3.62% | 0.383 | 0.0387 |
| Qwen3-ASR 0.6B | 16.90% | 5.66% | 1.057 | 0.1136 |
| Qwen3-ASR 1.7B | 9.52% | 3.35% | 1.247 | 0.1252 |
| Parakeet TDT v3 | Not supported | — | — | — |

## Moroccan Darija

| Model | Word error | Character error | Median clip seconds | RTF |
|---|---:|---:|---:|---:|
| Whisper Tiny | 96.14% | 52.43% | 0.638 | 0.1601 |
| Whisper Small | 89.26% | 42.38% | 0.271 | 0.0960 |
| Whisper Turbo | 85.74% | 41.16% | 0.371 | 0.1065 |
| Qwen3-ASR 0.6B | 90.10% | 42.58% | 0.717 | 0.1871 |
| Qwen3-ASR 1.7B | 82.89% | 37.08% | 0.832 | 0.2126 |
| Parakeet TDT v3 | Not supported | — | — | — |

## Model startup and memory

GPU peak covers all tested languages for each model and includes whole-device usage.

| Model | Cold model load seconds | Peak GPU MiB |
|---|---:|---:|
| Whisper Tiny | 1.43 | 441 |
| Whisper Small | 2.69 | 1203 |
| Whisper Turbo | 12.54 | 2485 |
| Qwen3-ASR 0.6B | 32.17 | 2115 |
| Qwen3-ASR 1.7B | 48.17 | 4819 |
| Parakeet TDT v3 | 7.84 | 1527 |


## Interpretation and remaining limits

French supports a Parakeet pilot, while the small difference between its word error and Qwen 1.7B should not be treated as a general quality ranking. For standard Arabic, Turbo is the practical lower-latency candidate and Qwen 1.7B is the accuracy candidate; the latter also consumes more of the 8 GB GPU budget. Cold model loading and coexistence with the language model matter: end-to-end multi-model throughput was not benchmarked.

Darija remains a material limitation. Orthographic and word-boundary variation can inflate WER, so CER is included; its observed error is still substantial. The data is broadcast material, and read speech is used for French/MSA. No performance claim is established for noisy real call-center audio, Moroccan French accents, Darija/French code-switching, long calls, live partial transcripts or concurrent sessions. Pretrained-model exposure to public benchmark data is unknown. This is a small fixed sample with no independent manual label audit or robust general performance confidence interval.

A next Darija experiment should use a separate, permission-reviewed development corpus for adaptation and a fresh frozen telephone test corpus. The Casablanca subset here remains evaluation-only; these results do not grant training or commercial rights. Future model changes should preserve human review until the target-call acceptance criteria are defined and met.

## Source review and reproducibility

- French: Mozilla Common Voice community, [Common Voice 22 mirror and license](https://huggingface.co/datasets/fsicoli/common_voice_22_0), revision `ae911de250fe9375d08e2daa2105b671d659d446`; source-published community validation, no independent listening claimed.
- Standard Arabic: Conneau et al., [FLEURS](https://huggingface.co/datasets/google/fleurs), revision `70bb2e84b976b7e960aa89f1c648e09c59f894dd`; publisher's prompted read-speech references. [FLEURS paper](https://arxiv.org/abs/2205.12446).
- Darija: Talafha et al. (2024), [Casablanca](https://huggingface.co/datasets/UBC-NLP/Casablanca), revision `8951b1b88e28c1107142ced57967b8d16350951d`; published Moroccan dialect transcription. [Paper](https://arxiv.org/abs/2410.04527), [license text](https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.en).
- [Parakeet model card](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) documents its supported languages. Arabic is excluded, rather than being assigned a fabricated score.

Source review was performed for this user-authorized local non-commercial evaluation. Published licenses and label provenance do not independently establish every third-party recording consent or benchmark generalization claim.

Evidence is under `docs/benchmarks/evidence/multilingual-20261029/`: `intake.json` records source review, selection, hashes and retention; `execution.json` records exact Docker arguments, timestamps and exit codes; six model JSON files contain all measured observations; `summary.json` contains per-language aggregates; `environment.json` records hardware, Git baseline and image IDs. The manifest hash must match across every model and sample sets must match exactly before summary generation succeeds. Unsupported languages remain explicit.

Implementation files:

- `scripts/intake_multilingual_benchmark.py`: bounded, pinned dataset acquisition; reuses the existing Common Voice vote validator and keeps source audio/references local.
- `scripts/benchmark_upgrade_asr.py`: adds optional multilingual manifests, language hints, conservative normalized metrics, audio/reference hashes, retention checks and path boundaries. Its legacy English mode keeps its prior scoring and decoding defaults.
- `scripts/run_multilingual_asr_benchmarks.ps1`: serial model jobs and restoration of Ollama in a `finally` block.
- `scripts/summarize_multilingual_benchmarks.py`: completeness/matched-input checks, reference-weighted metrics and generated tables.
- `tests/unit/test_multilingual_benchmark.py`: accent/Arabic normalization, changed references, path traversal, duplicate IDs and evaluation-purpose/retention guards.
- `docs/data/DATASET_CATALOG.md`: dated links to this evaluation, preserving earlier training-intake decisions.

No new runtime dependencies were installed for this follow-up. Existing HTTPX, SoundFile, SciPy, NumPy, RapidFuzz and local model runtimes were reused. Hashes, JSON, timing, Unicode handling, tar access and concurrency use the Python standard library. Model/runtime image identities are in the environment receipt; application dependency locks remain unchanged. No frontend changes, training, commits or pushes were made.

## Validation

**35 tests passed, with no skipped tests.** Lint, formatting, Python compilation and PowerShell syntax checks passed. All six model jobs exited successfully. Ollama was restarted and its API returned HTTP 200.

Actual commands and results are recorded in `verification.txt` and `verification.json` alongside the model receipts. The six model jobs completed successfully; inference covered 640 clip/model observations. The final verification records automated scoring/input-boundary tests, existing ASR/preprocessing regressions, lint, formatting, compilation and PowerShell syntax checks. Application defaults remain unchanged.
