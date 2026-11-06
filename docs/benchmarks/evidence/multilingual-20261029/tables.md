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
