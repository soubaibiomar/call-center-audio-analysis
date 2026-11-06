# STEP_13 — Benchmark Whisper against Qwen3-ASR

## 1. Execution header and plain-English goal

**Current status: DONE — PASS WITH LIMITATIONS for the user-selected research benchmark.** Results are in section 16 and final acceptance review in section 17; earlier partial and Qwen-pending statements are historical. 2026-10-28, Africa/Casablanca; owner: AI/ML engineering. Windows 11, PowerShell, uv-managed Python 3.12; branch `feature/project28-foundation`, working HEAD `a37e4634af1d2947fc3c548d54e62bda0b0daf89`, upstream pinned `fed4b610742c1337147281fcec8f2cdcc0a79be5`. The working tree includes earlier uncommitted changes. The requested telephone benchmark and evidence-based deployment choice remain blocked by the lack of an authorized, reviewed and representative telephone corpus. This document records what was implemented and actually tested.

STEP12 supplied nine reviewed-vote Common Voice French read clips with a locally frozen partition; its lack of telephone, Darija, independently audited labels, automatic retention handling, and independently controlled lock remains material. The user authorized downloading Qwen and asked us to inspect the Kaggle dataset. A CPU smoke test on two project-validation clips checks the infrastructure, not telephone performance. No production provider, model routing, Gradio workflow, GPU stack, training or model promotion was changed.

## 2. Existing versus upgraded implementation

| Surface | Upstream at pinned SHA | Current working tree | Compatibility |
|---|---|---|---|
| ASR | `src/agents/transcription.py` invokes faster-whisper and upstream workflow | Preserved original production entry point; an independent `WhisperAdapter` invokes a supplied model with automatic language detection | Additive; benchmark settings do not change production defaults |
| Alternate ASR | No Qwen3-ASR comparison adapter | `QwenAdapter` wraps a supplied Qwen3ASRModel; Qwen lives in a separate experimental environment | No default change, no network loading in adapter |
| Metrics | No project benchmark WER/CER pipeline verified in upstream | `src/datasets/asr_benchmark.py` normalizes, measures edit distance, latency, RTF, failures and language aggregates | Offline only; aggregate contract can support future UI |
| Evaluation data | No verified locked permission-aware split in upstream | STEP12 metadata/lock validation plus `scripts/benchmark_asr.py` validation-only smoke path | Fails closed on expired/revoked rights, missing references or audio hash mismatch |

The captured `git-diff-stat.txt`, `git-diff-names.txt` and `git-status.txt` under `evidence/step13-20261028/` show the broader prior dirty workspace, not just this step. Untracked files do not appear in ordinary Git diffs.

## 3. Files and interfaces

| Path | Action | Purpose and verification |
|---|---|---|
| `src/datasets/asr_benchmark.py` | Created | `Transcript`, `Transcriber`, model adapters, `normalize`, `edit_distance`, `observe`, `summarize`; synthetic tests and cross-check against jiwer |
| `scripts/benchmark_asr.py` | Created | Metadata/permission/lock checks, local-only model loading, validation-partition smoke run and exclusive private result file |
| `tests/datasets/test_asr_benchmark.py` | Created | Metric, normalization, adapters, failure, empty-reference and model-fingerprint tests |
| `docs/benchmarks/ASR_BASELINE.md` | Created | Source survey, evaluation protocol and limitations |
| `docs/implementation/PROGRESS.md` and this report | Updated/created | Step state, evidence and handoff |
| `docs/implementation/evidence/step13-20261028/` and `step13-final-validation/` | Created | Source inventory, actual Git snapshot, checks and JUnit output; no source audio or transcripts |
| `.local/step13-asr-venv/` and `.local/step13-qwen3-asr-0.6b/` | Local ignored experimental artifacts | Isolated Qwen runtime and model download; not production dependencies |
| `src/agents/transcription.py` | Kept | Existing Gradio/worker transcription remains intact |

## 4. Code and execution flow

`Transcript` is a strict immutable Pydantic object carrying text and optional language; `Transcriber` is the uniform `transcribe(Path)` protocol. The Whisper adapter consumes the generator returned by faster-whisper; the Qwen adapter requires exactly one result. Both accept already constructed models, and neither loads or downloads weights. An exception fails the current sample rather than inventing text or a confidence.

`normalize` applies NFC, case-folding and whitespace folding equally to reference and hypothesis. It retains punctuation and accents. `edit_distance` computes the Levenshtein dynamic program using one previous row: substitutions, insertions and deletions each cost one. `observe` times transcription with a monotonic clock and records integer error and reference counts; `summarize` sums numerators and denominators per language, uses nearest-rank p50/p95, total latency/audio duration for RTF, and reports failures separately. Empty references are rejected. GPU peak is `null` because this CPU path does not measure it.

The command validates the manifest and supplied lock checksum, rechecks fingerprints and rights on today's date via STEP12, restricts selection to project validation, verifies each local audio hash and keeps audio paths within the dataset root. It rejects multi-language labels rather than misrepresent code-switched metrics. It requires a local model directory, sets Hugging Face offline mode, fingerprints local model bytes, and writes a private result with model/manifest/lock/audio/reference hashes and configuration. Output is created exclusively; transcripts are not written into evidence. The caller must independently protect the lock digest and frozen reference hashes; this script does not authenticate users or guarantee immutable storage. Per-clip failures are counted without logging private contents, and cause a nonzero exit.

## 5. Imports and dependencies

`asr_benchmark.py` imports standard `math` (nearest-rank percentiles), `time` (monotonic durations), `unicodedata` (NFC), `collections.abc.Sequence` (typed inputs), `pathlib.Path` (local audio), and `typing.Any`/`Protocol` (backend interface). Existing Pydantic `BaseModel`, `ConfigDict`, and `Field` validate the stable output and counts. `scripts/benchmark_asr.py` imports standard `argparse`, `hashlib`, `importlib`/`importlib.metadata`, `json`, `os`, `date` and `Path` for CLI, digests, optional local backend loading/versioning, metadata, offline mode and paths; local imports provide the adapters, schema and lock planner. The tests use standard `Path`/`SimpleNamespace`, existing `pytest`, and local symbols. No production dependency was added.

Existing faster-whisper is 1.2.1 (`WhisperModel`); isolated experimental `qwen-asr` is 0.0.6 (`Qwen3ASRModel`), PyTorch 2.14.1+cpu, and `jiwer` 4.0.0. `jiwer` is used only as an independent synthetic cross-check, not imported by project runtime; this avoids changing existing dependencies. Four hand-picked and 1,000 seeded randomized synthetic pairs agreed with jiwer's word/character insertion, deletion and substitution counts. The pure-Python edit-distance implementation is simple but quadratic, so long transcripts need an optimized alternative before production-scale benchmarking.

## 6. Concepts for beginners

A transcription model maps sound to text. Different ASR models can vary in their language support and hardware use. WER counts word insertions, deletions and substitutions divided by the number of reference words: `hello world` versus `hello there` gives 1/2 = 0.5. CER applies the same operation to characters; in this protocol spaces count. Normalization must be declared before examining results because it changes scores. RTF divides processing time by audio time; 0.5 means half as much inference time as audio duration for that measurement, but it does not include model loading. GPU memory and latency can disqualify a model even when its WER is lower. A validation partition is for development; a locked held-out test partition is for a final pre-registered assessment.

## 7. Data, security, lineage and privacy

The selected [Kaggle archive](https://www.kaggle.com/datasets/satvicoder/call-center-data) was inspected through Kaggle's public API: version 1, CC0 as reported, a 22,935-byte ZIP containing one 66,754-byte `Call Center Data.csv`, no audio. Its aggregate call metrics cannot produce WER/CER. The archive inventory and SHA256 are in `evidence/step13-20261028/kaggle-inventory.json`; the archive itself was not saved. [Potential French telephone source](https://huggingface.co/datasets/ud-nlp/french-speech-recognition-dataset) is marked CC BY-NC-ND; its current API tree contains only CSV and README even though its card describes samples, and human label review and commercial rights are not established. [A second French call-center listing](https://huggingface.co/datasets/AxonData/french-call-center-speech-dataset) advertises samples but paid commercial access and the sample references' human verification remain unresolved. The user also supplied [UniData's Kaggle audio preview](https://www.kaggle.com/datasets/unidpro/call-center-audio): public API metadata shows five FLAC files and two CSV files, with five matching transcript entries in `metainfo.csv`; the user-supplied preview is CC BY-NC-ND 4.0 and the source does not establish human verification or speaker-disjointness for these particular records. The provider describes the full dataset as mostly English, and offers samples for testing while licensing the full dataset separately. The sample is a promising research-only candidate, not approved gold or evidence of commercial rights. The initial check read CSV metadata to count matching IDs and nonempty transcript fields; after the user asked to use the preview, one 3,230,264-byte FLAC was acquired into ignored local storage for the restricted research smoke test described in section 14. No transcript text was retained in the report or evidence. See `evidence/step13-20261028/kaggle-audio-inventory.json`. No transcript content was disclosed.

The smoke dataset is the STEP12 CC0 French read-speech sample, with source community votes and a 2026-11-28 retention deadline. It is not Darija, code-switched speech, a phone conversation, or evidence of call-center deployment fitness. Its two local validation examples originated in the source dataset's own test subset; we did not use the *project's* locked test assignment, but do not claim the source's held-out test set remained untouched. Further work must protect frozen references against changes; a reference hash recorded after use is not independently precommitted proof. No model was trained.

## 8. Verification

- `.venv/Scripts/python.exe -m pytest tests/datasets -q`: **32 passed** after the last code change.
- Service-configured regression `python -m pytest tests/unit tests/security tests/api tests/integration tests/workers tests/llm tests/datasets -q --tb=short`: **333 passed**, one deprecation warning, 46.09 seconds after the final code refactor. JUnit and exact executed commands are in `evidence/step13-post-refactor/`.
- Ruff check passed and formatting passed for 142 files; mypy passed 70 application files plus a separate check of the new runner; `uv pip check`, compileall and key scan passed.
- Independent isolated `jiwer` check: four hand-picked and 1,000 seeded randomized synthetic reference/hypothesis pairs agreed with the edit-distance calculations.
- Actual faster-whisper CPU validation invocation used the exact manifest, lock SHA, and cached tiny snapshot in the private result file; two successful clips, no failures. Model load excluded. No results are extrapolated to phone calls.
- Qwen installation and model download are tracked in the execution addendum below. A Kaggle metadata probe initially failed to print an emoji on the Windows console (UnicodeEncodeError); the subsequent probe escaped non-ASCII output and completed successfully without exposing transcript contents. No real telephone comparison was run.

## 9. Quantitative results and interpretation

The final Whisper smoke run (`faster-whisper` 1.2.1, tiny snapshot `d90ca5fe260221311c53c58e660288d3deb8d356`, CPU int8, two project-validation French read clips) observed WER **0.3125**, CER **0.0813953**, p50 **0.3857 s**, p95 **0.5007 s**, RTF **0.10523**, failures **0/2**. The p50/p95 are individual nearest-rank values for only two examples, not reliable latency percentiles. Results include decoding and inference, not model loading. Since the new check is a smoke test, a production-domain baseline, Darija/code-switch slices, paired telephone accuracy, peak GPU memory, production concurrency and statistical uncertainty are **not measured**. The machine has an RTX 4060 Laptop GPU with 8188 MiB total, observed 140 MiB used before execution; this is not peak benchmark VRAM.

## 10. Questions and answers

1. **Why compare both models?** Published multilingual scores do not establish Moroccan Darija or real telephone performance on this project's data.
2. **What is WER?** Total word-level substitutions, deletions and insertions divided by the reference word count.
3. **Why measure latency and VRAM?** An accurate model may not fit the 8 GB GPU or meet live-response needs.
4. **Can two French clips establish a winner?** No; they only exercise the smoke path and cannot characterize call-center quality.
5. **Why is Kaggle unsuitable here?** Its downloaded archive contains an aggregate CSV and no sound or reviewed reference transcripts.
6. **Why is the test lock hash insufficient by itself?** Anyone able to replace both an adjacent lock and its hash can make them agree; trusted independent storage and authorization are still needed.
7. **What happens with code-switching?** The current runner refuses multiple language labels because it lacks time-aligned language spans; aggregate mixed-language CER/WER cannot honestly be attributed to each language.

## 11. Decisions, risks and remaining work

Keep the existing faster-whisper deployment and adapter as the operational baseline, not an evidence-based STEP13 winner. Obtain usage/retention permission, human-reviewed transcripts and speaker/conversation identifiers for a representative telephone corpus, preserve held-out data and reference hashes under independent control, and pre-register both model configurations and measurement policy. Run both on the same audio under controlled GPU load, measure peak VRAM and failure rate, then document the model selection and fallback. Verify any dataset card's exact sample files, reviewer provenance and license; CC BY-NC-ND or commercial-only terms may not fit intended deployment. The small French smoke data, source-test lineage, low sample size and CPU results are explicitly limiting.

## 12. Handoff and evidence checklist

- [x] Existing implementation, step prompt, previous report, environment and working tree reviewed.
- [x] Additive adapters, metrics, private-result runner and tests implemented.
- [x] Real CPU Whisper smoke execution and synthetic metrics verification completed.
- [x] Kaggle archive and alternative source availability checked without collecting private recordings.
- [ ] Same-corpus telephone comparison, representative language slices and GPU peak measurement.
- [ ] Evidence-based deployment candidate and fallback decision.
- [ ] Independently controlled reference/lock integrity and current retention review.

Next safe action is to complete STEP13 after acquiring a rights-cleared, human-reviewed telephone benchmark and confirming model/runtime availability. STEP14 is not claimed ready; review its prerequisites only once STEP13 is complete. See `docs/benchmarks/ASR_BASELINE.md`, the private `data/datasets/common-voice-22-fr-20261028-review/` results, and the two evidence directories. No commits or pushes were made.

## 13. Approved ERP UI design / visual contract verification

Not applicable: no frontend, API route, CSS or existing Gradio surface was changed. The aggregate JSON records model fingerprint, language, WER/CER, latency, RTF, failure counts and nullable GPU memory for future authorized model-comparison screens. No browser screenshots, responsive checks, color-token or accessibility measurements were made; a later UI must display missing measurements as unavailable rather than fabricated values, and follow `design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png`.


## 14. UniData preview smoke test and continued source search

After the user selected “use it and continue searching,” one file from the five-file [UniData Kaggle preview](https://www.kaggle.com/datasets/unidpro/call-center-audio) was used only for non-commercial exploration under the preview's stated CC BY-NC-ND terms. The source does not establish human transcript review; speaker linkage and applicable broader-use rights remain unverified. The sample was not added to an approved dataset manifest, split, or gold benchmark. The preview metadata and actual call may contain personal information, so the 3,230,264-byte FLAC and generated local receipt are under ignored `.local/step13-unidata-preview/`; neither source nor predicted transcript was retained or published. The selected prior local benchmark retention deadline, 2026-11-28, is recorded for this local sample, but no automatic deletion exists.

Actual `faster-whisper` tiny CPU/int8 execution completed on the single recording in **12.3815 seconds**, excluding model load. The decoder observed **299.0 seconds** of audio, giving an illustrative RTF of **0.04141**. Source metadata reported **313.0 seconds** of total call duration; this discrepancy needs source-specific investigation and the two values may represent different duration definitions. The model generated non-empty text, but this proves neither transcript correctness nor model quality. WER and CER are **not measured** because a verified reference was unavailable; the public report does not contain the call's contents. Receipt: `evidence/step13-20261028/unidata-smoke.json`. Timing on one recording, under concurrent downloads and unspecified CPU load, is not a production benchmark.

Further search identified [ALAMA](https://github.com/Ackanel/alama_audio_dataset), which describes three independent Darija transcribers but does not identify a license or sufficient speaker/split provenance; [Darija ASR Corpus](https://huggingface.co/datasets/abnajlae/darija-asr-corpus), with distinct subset licenses and speaker IDs but unverified per-record review and recording context; and [OrienTel Moroccan telephone corpus](https://catalogue.elra.info/en-us/repository/browse/ELRA-S0183/), which requires rights/access and suitability review. None proves a currently usable, human-reviewed and representative held-out call-center benchmark.

### Additional user-supplied sources

[AxonData English on Hugging Face](https://huggingface.co/datasets/AxonData/english-contact-center-audio-dataset) lists two English recordings and two DOCX files. The user also provided [AxonData's multilingual Kaggle sample](https://www.kaggle.com/datasets/axondata/call-center-speech-dataset): the API lists ten MP3 files and ten DOCX files in English, French and other languages, licensed CC BY-NC 4.0. We opened the two French DOCX files in memory and verified they contain text, without retaining or displaying their contents. A French document and audio in the same folder are not proof of alignment: one audio filename bears the identifier of the other French sample. The source describes machine-generated speaker-role labels and does not establish human transcript verification. The provider says the full commercial dataset is purchased separately. Until the pairings, labels, exact permitted use and speaker separation are reviewed, these are research candidates, not verified reference material or a deployment benchmark. See `evidence/step13-20261028/axondata-inventory.json`. [UniData](https://unidata.pro/datasets/call-center-audio/) is the provider of the five-call sample tested above and states that its sample is for testing while the full dataset is licensed separately.

### Qwen download and memory constraint

The user authorized Qwen3-ASR 0.6B and its dependencies. An isolated uv environment was created under `.local/step13-asr-venv`; `qwen-asr` 0.0.6 imported successfully with CPU PyTorch 2.14.1. The official model revision resolved to `5eb144179a02acc5e5ba31e748d22b0cf3e303b0`; its advertised weights are 1,876,091,704 bytes, SHA256 `79d6cbd4c98c7bbffe9db2edac07f56cd6637d0d5944b27f6c2b8353840323ea`. The ordinary Hugging Face transfer stalled, so a resumable range downloader was attempted. After the initial interruption, the range downloader resumed and assembled all 112 parts. The 1,876,091,704-byte model matched the publisher SHA256 exactly. The downloaded model and partial files are preserved in ignored `.local/step13-qwen3-asr-0.6b/` and `.local/step13-qwen-parts/`. No Qwen inference was run.

The RTX 4060 reported 7,844 MiB free, but the host reported approximately 491,448 KiB free physical and 4,736,128 KiB free virtual memory while multiple applications were active. An isolated CUDA PyTorch 2.8.0 installation attempted a 3.2 GiB download; it was interrupted before installation to avoid further resource pressure. No production environment was changed. The isolated environment still has CPU-only PyTorch. Once memory and connectivity are adequate, install and verify an appropriate compatible GPU runtime there, recheck available system and GPU memory, and only then run Qwen on the same authorized validation inputs. The downloader used `.venv\Scripts\python.exe .local\step13_download.py`; its final hash was verified, and the existing output must not be overwritten by rerunning it.

**Current decision: PARTIAL / blocked on reviewed telephone benchmark and Qwen runtime execution.** No model was selected for deployment; STEP14 has not been started.


## 15. Follow-up: real-call provisional benchmark (2026-10-28)

The user asked to fix the remaining issue and use the supplied call data as a benchmark. Five actual UniData preview recordings and their supplied transcript fields were acquired from Kaggle version 1 into the ignored `data/datasets/unidata-preview-research-20261028/` folder, using the already selected 2026-11-28 local retention deadline. Source metadata and recording bytes were checked during intake; reference turn/timestamp markers were parsed by a strict format and excluded from comparison. A non-empty line with an unknown format causes intake to fail. The source transcript text, audio, file-level results and IDs remain private; none is published in this report. The first transfer failed partway through the largest recording; a range-checked `--resume` path preserved and continued the partial download, then completed all five.

The source declares CC BY-NC-ND 4.0 and the user directed use of the preview; this is a **non-commercial research evaluation** only. The source does not establish that the particular transcripts were human-reviewed, the speaker identities and overlap across calls are unknown, the dataset contains only five calls, and no Darija/French or held-out speaker split is established. We measure against the provided references without calling them gold. No claim about commercial permission or generalizable accuracy is made.

`scripts/intake_unidata_benchmark.py` creates the private input manifest, source and reference hashes, validates lengths, limits storage, supports exclusive and range-checked resume, and retains explicit unverified label status. `scripts/benchmark_unidata.py` verifies the frozen input-manifest hash, file and reference hashes, purpose, retention and model files, uses RapidFuzz Levenshtein distance after the fixed NFC/casefold/whitespace normalization, and stores per-call counts and timing without predicted transcripts. Its optional Qwen path processes 30-second chunks on CUDA FP16; Whisper uses CPU int8 with greedy decoding. Such hardware and chunking differences must be considered when comparing timings. As with the original smoke runner, the operator's checksum and source assertions require independent governance; the pipeline is not an immutable or authenticated test system.

Actual faster-whisper tiny CPU/int8 execution over all **5/5 calls**, **3,781.637 seconds** of decoded audio: WER **0.36511**, CER **0.26277**, measured against the **unverified** supplied references, nearest-rank p50 **13.6633 s**, p95 **29.0668 s**, total RTF **0.02182**, **0/5 failures**. Timing excludes model load and is an observed local result, not a production latency guarantee. The model fingerprint and frozen input digest, formulas and aggregate result are recorded in `evidence/step13-unidata-20261028/whisper-aggregate.json`; these scores may change after transcript correction. The previous French read-speech smoke is a different experiment.

New imports are Python standard-library argparse, csv, hashlib, io, json, re, date and pathlib for private ingestion and validation; `httpx` 0.28.1 (already installed) fetches source data. The benchmark script uses argparse, hashlib, importlib/metadata, json, os, time, date and pathlib, local normalization/fingerprint helpers, `rapidfuzz` 3.14.6 in an isolated target for fast edit distance, and dynamic local faster-whisper or optional `torch`/`qwen_asr`/`soundfile` for inference. No dependency was added to the production environment. `tests/datasets/test_unidata_benchmark.py` checks turn extraction and rejection of malformed references; additional dataset tests and final quality checks are listed in the execution addendum.

At the time of this follow-up Qwen inference and matched metrics were pending; section 16 records their subsequent completion. The prior project test partition is not modified; this five-call research set is an evaluation snapshot with no demonstrated speaker-disjoint train/test split. The source reference uncertainty and non-commercial license remain limitations even after Qwen runs.

Further AxonData inspection found that one French sample document advertises an `English transcription` heading but no identified original-language section, while the other includes an `Original Transcription` heading. This strengthens the need to verify the audio/wording alignment before scoring: comparing French audio with translated English would not measure French ASR accuracy. No source transcript content was logged.


Final follow-up validation: service-configured suite **336 passed**, one warning, in 46.76 seconds; 35 dataset tests passed in 2.16 seconds; Ruff check and formatting passed for 145 files; application mypy passed 70 files, and the two new scripts passed a separate mypy run. Dependency, compile and key checks passed. Commands and JUnit output are stored in `evidence/step13-real-benchmark-20261028/`.


## 16. Completed local paired comparison and GPU runtime repair

On 2026-10-28 Qwen3-ASR 0.6B was run on the **same five calls and the same frozen reference snapshot** as Whisper. Both runs checked input digest `52b18eb7ca1d058f77a2e41c06bee8da5f0f0e02ed89c72d8d965081b90c3843`; both completed **5/5 calls, 3,781.637 seconds of audio, zero failures**. These scores measure agreement with the source-provided, **unverified** references, not independently confirmed ground truth. The sample is non-commercial, very small, not verified speaker-disjoint and not demonstrated to cover Darija or code-switching. This is actual telephone audio, but cannot establish production-domain generalization.

| Configuration | WER vs source text | CER vs source text | p50 per call | p95 per call | Aggregate RTF | Failures |
|---|---:|---:|---:|---:|---:|---:|
| faster-whisper tiny 1.2.1, CPU int8, full-call decode | 0.36511 | 0.26277 | 13.6633 s | 29.0668 s | 0.02182 | 0/5 |
| Qwen3-ASR 0.6B / qwen-asr 0.0.6, RTX 4060 FP16, 30-second chunks | 0.26169 | 0.17939 | 53.1539 s | 126.2277 s | 0.07940 | 0/5 |

These are observed totals over five calls, with nearest-rank percentiles and loading excluded; they are not confidence intervals. Qwen's GPU peak **PyTorch allocated** memory was **1,881,212,416 bytes (about 1,794 MiB)**, including the model; this is not total device-wide reserved memory. CPU Whisper has no GPU peak measurement. Different device, precision and chunking settings mean the latency/RTF values are not a hardware-normalized speed comparison. Qwen used a 256-token generation limit per 30-second chunk; truncation at that limit was not measured. The runtime also reported that a temperature generation setting might be ignored; no sampling behavior was inferred from that warning. Qwen's lower observed WER/CER makes it a **provisional candidate for further validation** on these references. Existing faster-whisper remains the unchanged operational fallback and default; no production model promotion is claimed.

The laptop's existing local CUDA image provided PyTorch 2.14.0+cu130. A new isolated local benchmark image, `project28-step13-qwen:headers`, SHA256 `353fa0a122a46406dc198c65e72708d82910cda28fd93caa11f9825ad431f795`, included qwen-asr 0.0.6, transformers 4.57.6, RapidFuzz 3.14.6 and `libc6-dev`. The first Qwen attempt reached the GPU but all five calls failed with `CalledProcessError`: Triton's C compilation could not find `stdlib.h`. Installing the headers in the separate image fixed this; the second run exited zero. The first failed private receipt is preserved as `qwen-results.json`; the successful private receipt is `qwen-results-fixed.json`. The second container used `--network none`, read-only workspace and model mounts, and a writable private result directory. Neither model sent audio to a remote inference service. The image is locally derived from an existing unrelated image and is not yet a portable, pinned project production image.

Machine-readable aggregate evidence: `evidence/step13-unidata-20261028/whisper-aggregate.json` and `qwen-aggregate.json`. The full service-configured suite previously passed **336 tests**, one warning, in 46.76 seconds; dataset tests passed **35**, and Ruff, formatting, mypy, dependency, compile and key checks passed as described above. No project source code changed during this follow-up. The development and production providers remain unchanged.

**Current decision: PARTIAL WITH MEASURED RESULTS.** STEP13's paired exploratory test and candidate comparison have been executed. Remaining acceptance limitations are independently reviewed transcripts, a separately controlled and verified held-out/speaker-disjoint set, relevant French/Darija/code-switching slices, and deployment/commercial rights. A larger representative authorized benchmark is needed before selecting a production model; STEP14 was not started.


## 17. Completion review — 2026-10-28

**Decision: DONE — PASS WITH LIMITATIONS** for STEP13's research benchmark and provisional candidate selection. The user explicitly directed the use of the supplied call preview. Both configurations were executed on the same fixed five-call evaluation snapshot; the project did not train either model on this snapshot. Model-provider pretraining overlap is not known. Qwen3-ASR 0.6B is the candidate for further deployment evaluation, and the existing faster-whisper transcription path and benchmark adapter remain available as the fallback; the production default was not changed. This candidate decision is based on source transcripts of unknown review status and does not approve a production deployment.

| Done gate | Actual evidence and limit |
|---|---|
| Two configurations evaluated | Five successful real-call runs for each model, paired by the same manifest digest; aggregates in `evidence/step13-unidata-20261028/`. |
| Reproducible benchmark manifest | Private manifest pins source version, input/reference hashes, retention, purpose and selected IDs; result records model content hash, runtime, normalization and decoding choices. The local lock/checksum is not independently immutable, and the exploratory Docker image depends on a local base image. |
| No hidden test-set tuning | The Qwen/Whisper configurations and input snapshot were fixed for the paired runs; the STEP12 project locked test partition was not used. Candidate selection used this disclosed evaluation snapshot, so it is no longer an independent final model-promotion test. A new, independently held-out set is needed for that decision. Vendor pretraining overlap is not established. |

Language-specific and code-switching WER/CER were **not measured**: the five-call source does not supply verified language spans. Source references have not been independently checked by human reviewers, speaker overlap is unknown, the sample is small, and the CC BY-NC-ND preview is restricted to non-commercial research. No production-wide, commercial-use, representative Darija/French, or generalization claim follows from this step. Retention handling is manual and the saved local deadline is 2026-11-28.

The completion review found that the benchmark runner validated its license and retention but did not enforce the recorded non-commercial purpose or the unverified source-reference status. `scripts/benchmark_unidata.py` now rejects a mismatched purpose or unexpected label provenance before model loading. `tests/datasets/test_unidata_runner.py` verifies scoring with synthetic fixtures, rejection of changed audio and an invalid purpose, and absence of reference text from results. The earlier measurements preceded this guard change; an independent check verified that both measured result files match the current input digest and satisfy the new guards. No model was retrained, and no earlier measurements were recomputed.

Validation after the correction: the service-configured suite passed **339 tests**, one deprecation warning, in 43.21 seconds; the focused dataset suite passed **38 tests**. Ruff passed, formatting checked **146 files**, mypy passed **70 application files** plus the changed benchmark script, and dependency, compile and hardcoded-key checks passed. An earlier concurrent review run found one formatting failure while a test file was being edited; it was formatted, and the final run passed. Logs and JUnit are in `evidence/step13-completion-final-20261028/`; prior evidence remains intact. No frontend was changed, so section 13 remains applicable.

STEP14 is the next numbered step, subject to its own prerequisites and the stated research and licensing limitations. No commit, push, training, production deployment or change to the existing inference default was made.
