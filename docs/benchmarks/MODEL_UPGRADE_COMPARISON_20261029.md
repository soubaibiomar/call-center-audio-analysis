# Local model upgrade benchmark — 29 October 2026

Completed the five approved candidate comparisons on the laptop. Application defaults remain unchanged. This is a preliminary English ASR and synthetic text/retrieval evaluation, not production acceptance.

## Environment and provenance

RTX 4060 Laptop GPU, 8,188 MiB; Windows host with Docker/WSL GPU inference; local Ollama. Each heavy GPU workload runs serially. Existing application containers and Ollama configuration were preserved. [Hardware, Git baseline and inventory](evidence/upgrade-20261029/environment.json), [runtime versions](evidence/upgrade-20261029/runtime-versions.json). These are observed laptop timings; power and thermals were not experimentally fixed.

New weight downloads total approximately 11.1 GB. Qwen3.5 4B was already cached. Pinned revisions, file sizes and verified weight SHA-256 values are in the four `*-download.json` receipts under the evidence directory. Model weights and public audio remain outside versioned source; no training occurred.

## ASR: matched English support roleplays

AppTek call-center dialogues, revision `b98967d9946f7f59f58d08624a2a00fe98fe0219`, CC BY-SA 4.0. Three publisher-transcribed English roleplays (Australian, Indian, US), 992.2 seconds and 2,217 reference words per pass. Two passes repeat the same three calls; they are not six independent calls. Audio hashes and manifest hashes are checked. This is a custom subset evaluation, not an official benchmark leaderboard score or genuine customer-call validation.

All models receive the same mono 16 kHz, non-overlapping 30-second chunks. English is explicitly selected where supported. Whisper uses beam 1, no VAD and no previous-text conditioning; Qwen uses FP16 and a 256-token chunk limit. Parakeet uses FP16 generation. Model loading, audio decoding and a separate one-second silence warmup are excluded from timed calls. NFC, casefolding and whitespace normalization retain punctuation. References are ordered by start/end; overlapping speech and annotation disfluencies can increase error. No reference-dependent tuning was used.

WER = summed word edit distance / summed reference words; lower is better. CER is the analogous character score. RTF = inference seconds / audio seconds; 0.1 means ten times faster than audio playback. GPU peak is sampled whole-device memory, including other GPU usage; it is not model-only allocation. CPU and GPU rows are separate deployment comparisons; use GPU rows to isolate model/runtime differences.

| Model/configuration | WER | CER | RTF | Median call seconds | GPU peak MiB |
|---|---:|---:|---:|---:|---:|
| Whisper Tiny — GPU FP16 | 32.12% | 18.19% | 0.0097 | 3.36 | 343 |
| Whisper Small — GPU FP16 | 26.21% | 14.96% | 0.0176 | 5.37 | 899 |
| Whisper Turbo — GPU FP16 | 24.40% | 13.30% | 0.0216 | 6.31 | 2359 |
| Qwen3-ASR 0.6B — GPU FP16 | 23.73% | 10.45% | 0.0938 | 26.67 | 2163 |
| Qwen3-ASR 1.7B — GPU FP16 | 23.41% | 10.24% | 0.0929 | 27.00 | 4751 |
| Parakeet TDT 0.6B v3 — GPU FP16 | 23.59% | 10.49% | 0.0095 | 2.94 | 1501 |
| Whisper Tiny — CPU INT8 (Docker) | 32.84% | 18.97% | 0.0167 | 5.86 | N/A |

Lowest observed English WER: **asr-qwen17-cuda**. Fastest observed GPU ASR: **asr-parakeet-cuda**. These rankings apply only to these inputs and settings.

## LLM: current application and controlled comparison

The application-level run executed the existing summary and QA agents: 7B and 4B each returned 6/6 schema-valid outputs. Their maximum request times were 8.31 s and 55.55 s respectively, mixing cold/warm requests. 9B's first summary timed out at 180.13 s; its remaining application requests were cancelled. Preserve this failure separately from the successful controlled run; it is not a zero-speed result. [Raw application results](evidence/upgrade-20261029/llm-rerun/results.json).

The controlled local native-API run fixes context to 4,096 tokens, thinking off, temperature 0, seed 42, maximum 2,048 output tokens, one attempt. A separate warmup precedes two passes over nine synthetic English/French/Arabic summary cases. Each model sees the same per-case prompt and schema; repeat UUIDs differ. This compares a controlled inference configuration, not unchanged application API latency. Correctness below tests only the expected resolution status, not comprehensive summary factuality or QA scoring accuracy.

| Local model | Valid JSON/schema | Expected resolution | Median seconds | p95 seconds |
|---|---:|---:|---:|---:|
| qwen2.5-coder:7b | 18/18 | 12/18 | 1.754 | 3.055 |
| qwen3.5:4b-q4_K_M | 18/18 | 12/18 | 2.164 | 4.119 |
| qwen3.5:9b-q4_K_M | 18/18 | 13/18 | 3.248 | 7.497 |

7B remains the speed choice on these tasks. 4B uses less resident GPU memory (3.13 GB versus 4.75 GB for 7B, native API allocation) but did not improve latency or the tested labels. 9B succeeded at the bounded context with 5.59 GB resident GPU allocation; its one additional correct label is too little evidence for a quality upgrade. The transfer fixtures use ongoing/future handoff wording, which can be interpreted differently from a completed transfer; review those labels before treating the score as a gold quality gate. Fixtures were retained unchanged after observing results.

## Retrieval: BGE-M3 plus optional reranker

Twelve fixed synthetic English policy passages and eighteen labeled queries (six English, six French, six standard Arabic), two passes. CPU FP32, four Torch threads. The existing BGE-M3 adapter encodes documents once and queries one at a time. The candidate cross-encoder reranks the same dense top five. Authorization filtering is assumed before ranking; this benchmark does not replace authorization or the production answer-abstention policy. Load, index and warmup times are excluded from request latency and separately recorded.

| Configuration | Top-1 | MRR@5 | Median request seconds |
|---|---:|---:|---:|
| BGE-M3 | 100.00% | 1.0000 | 0.063 |
| BGE-M3 + reranker | 100.00% | 1.0000 | 0.443 |

Candidate Recall@5: 100.00%; reranking cannot recover a relevant document missing from that candidate set. MRR@5 is the mean reciprocal rank, zero when absent. This small synthetic set cannot establish production retrieval improvement.

## Failures, corrections and verification

The first Whisper GPU attempts failed because CTranslate2 required CUDA 12 cuBLAS. The existing Torch runtime uses CUDA 13. A separate image now supplies pinned CUDA 12 cuBLAS/cuDNN in an isolated path, and the three Whisper GPU comparisons were rerun. The failed receipts remain in `asr-execution.json`; final tables use successful complete observations. Parakeet uses its own pinned Transformers 5.21.1 runtime; Qwen retains Transformers 4.57.6. No shared project dependency lock or persisted service configuration was changed.

An unrelated Ollama workload overlapped the initial ASR attempt. Those successful-but-confounded measurements were archived under `evidence/upgrade-20261029/overlap-attempt/` and excluded from the final matched tables. With the user's authorization, Ollama was temporarily paused while the clean ASR and retrieval runs executed, then resumed. Parakeet's generation output also required extracting `.sequences` before decoding; the corrected adapter was executed on the real model.

One Hugging Face metadata connection closed during downloading; the download resumed, and final weight hashes were verified. An initial LLM invocation produced no receipts and was interrupted; the report uses the fresh rerun and controlled evidence only.

Validation commands and results are recorded in `verification.txt`. Tests cover weighted error aggregation, partial-run detection, Unicode normalization, missing relevant documents and candidate recall invariance, plus existing ASR/audio/grounding and local provider regressions. The final run passed 46 tests and skipped one PostgreSQL integration test because an isolated knowledge database was not configured. Lint, formatting and compilation checks passed.

## Reproduction and files

From the repository root, use the pinned images and existing permission-reviewed `.local/step15-apptek` inputs. Download receipts pin the four new repositories. Scripts deliberately reject existing result paths: preserve this evidence and choose a fresh output location before repeating. `asr-execution.json` records exact Docker arguments, timestamps and exit codes.

- `scripts/download_upgrade_models.py`: range-validated resumable downloads, SHA-256 verification and model receipts.
- `scripts/benchmark_upgrade_asr.py` and `scripts/run_upgrade_asr_benchmarks.ps1`: matched audio, timed generation, word/character errors, memory sampling and serial jobs.
- `scripts/benchmark_upgrade_llm_quality.py`: fixed local model requests, typed schema validation and labeled resolution checks.
- `scripts/benchmark_upgrade_retrieval.py`: frozen synthetic corpus, existing embedding adapter and top-five cross-encoder comparison.
- `scripts/summarize_upgrade_benchmarks.py` and this report generator: weighted aggregation, completeness checks and measured tables.
- Two benchmark Dockerfiles isolate the new Transformers and CUDA 12 runtime. Tests live in `tests/unit/test_upgrade_benchmark_protocol.py`.

New runtime imports are NumPy/SoundFile/SciPy for mono/resampling, RapidFuzz for Levenshtein distance, Torch/Transformers for local inference, faster-whisper/CTranslate2 for Whisper, qwen-asr for Qwen, and HTTPX for local Ollama and downloads. The download helper uses Hugging Face Hub metadata; hashes, JSON, timing, threads and subprocess sampling use the Python standard library. Versions are recorded in receipts; application dependencies remain unchanged.

## Limits and recommendation

Parakeet offers the strongest measured English speed/accuracy tradeoff: 23.59% WER versus Qwen 1.7B's 23.41%, about 9.8 times faster and 1,501 MiB versus 4,751 MiB sampled GPU peak. Qwen 1.7B has the lowest observed error count, but its advantage over Parakeet is only four words per pass. Treat Parakeet as an English evaluation candidate, not an automatic multilingual replacement. Keep the current 7B LLM unless memory savings justify 4B. Consider a bounded context configuration before increasing LLM size. Enable reranking only after it helps a larger reviewed policy-query set enough to justify the measured extra latency. The reranker gave no measured accuracy gain here and increased median query latency about sevenfold.

No Darija, Arabic or French speech accuracy was established here. Synthetic French/Arabic text cases do not establish speech quality. Parakeet's listed languages exclude Arabic, so it cannot replace the full Moroccan ASR path. Larger reviewed corpora, noisy telephony, real QA factuality labels, concurrent load and longer contexts remain separate acceptance work. The small fixed-order sample has no defensible general performance confidence interval. GPU selection is serialized; end-to-end multi-call throughput and streaming latency were not measured. No frontend changes or screenshots apply.

## Primary sources

- [AppTek corpus](https://huggingface.co/datasets/apptek-com/apptek_callcenter_dialogues)
- [Whisper Turbo conversion, MIT](https://huggingface.co/dropbox-dash/faster-whisper-large-v3-turbo)
- [Qwen3-ASR 1.7B, Apache-2.0](https://huggingface.co/Qwen/Qwen3-ASR-1.7B)
- [Qwen3.5 4B](https://huggingface.co/Qwen/Qwen3.5-4B)
- [BGE reranker, Apache-2.0](https://huggingface.co/BAAI/bge-reranker-v2-m3)
- [Parakeet TDT v3, CC BY 4.0](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3)

[Machine-readable summary](evidence/upgrade-20261029/summary.json). No commits, pushes, training or application-default changes were made.
