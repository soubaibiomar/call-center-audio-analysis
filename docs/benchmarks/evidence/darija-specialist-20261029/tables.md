| Model | Word error | Character error | Median clip seconds | RTF | Peak GPU MiB |
|---|---:|---:|---:|---:|---:|
| Whisper Small base | 99.50% | 54.82% | 0.227 | 0.0617 | 960 |
| Whisper Small / DVoice Darija | 94.33% | 55.62% | 0.210 | 0.0547 | 960 |
| Whisper Turbo base | 100.35% | 55.96% | 0.328 | 0.0841 | 2364 |
| Qwen3-ASR 1.7B base BF16 | 86.25% | 39.64% | 0.859 | 0.2290 | 4735 |
| MoulSot v0.3 BF16 | 53.93% | 20.89% | 0.934 | 0.2505 | 4562 |

Candidate-minus-baseline word error differences; negative favors the candidate.

| Comparison | Difference, percentage points | Conditional paired 95% interval |
|---|---:|---:|
| small-darija_vs_small-base | -5.17 | [-19.67, 6.11] |
| moulsot_vs_qwen-base | -32.32 | [-35.59, -29.20] |
| moulsot_vs_turbo-base | -46.42 | [-82.05, -28.83] |
