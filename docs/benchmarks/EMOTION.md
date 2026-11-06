# Emotion benchmark protocol and UI exposure decision — STEP_20

Protocol fixed before local model scoring, 2026-10-29. No thresholds are fitted on this evaluation set.

- Keep acted English CREMA-D and spontaneous Darija media MDER-MA separate. Neither is a Moroccan telephone benchmark. Evaluate four source-provided classes only; label scope is explicit, not psychological truth.
- A deterministic bounded subset selects four records per class per source using metadata before prediction, preferring distinct published speaker keys within each class. Exclude adult-age metadata below 18 from MDER-MA. No speaker re-identification or demographic/accent inference.
- Score normalized 16 kHz mono waveforms, with an explicitly disclosed stereo average for the offline MDER transfer probe. This differs from the runtime's stereo abstention. Also score a reproducible Gaussian-noise variant at 20 dB SNR with a fixed per-record seed. Preserve the shared original record ID; variants are correlated.
- Report fixed four-class macro F1, precision/recall/support and raw confusion. Separately report operational Unknown/coverage, five-label confusion, operational macro F1 and selective accuracy. Unknown contributes false negatives; do not drop rejected examples to inflate quality.
- ECE uses ten equal-width confidence bins and every raw prediction. Confidence=1 belongs in the final bin; empty bins contribute nothing. No calibration fitting; low sample sizes make this descriptive only.
- Language/accent/noise slices include counts. An absent second eligible slice or unverified accent yields null, not zero disparity. Cross-domain performance differences are confounded by source/recording/labels and are not a causal language-bias estimate.

## Prospective go/no-go criteria

Current decision: **NO-GO for emotion labels in production UI or employment decisions**. A research-only display may show probabilities with explicit uncertainty, access controls and human review; this document does not authorize rollout.

Before considering a production pilot: independently reviewed, purpose-permitted real telephone data for each supported language (Darija and French included); at least 20 independent speakers and 50 utterances per class per target language as minimum planning floors, not statistical guarantees; speaker/conversation-disjoint holdout separated from calibration and tuning; no test contamination; documented agreement and class distribution; language/accent/noise slices with confidence intervals; calibration on a separate calibration set; held-out macro-F1 lower confidence bound >=0.60, ECE upper bound <=0.10, per-class recall >=0.50, and supported slice F1 gap <=0.10 as provisional review thresholds. These thresholds require stakeholder review and must be frozen before future evaluation.

Also required: low-confidence, unsupported-language, overlap and unsafe-input abstention tests; disabled/unavailable/Unknown states; privacy/retention enforcement; UI that describes acoustic classifications rather than true mental state; approved green-neutral visual and accessibility review; no automatic HR/QA score changes and no punitive use. No automatic promotion follows from metric thresholds.

Actual measurements and sources will be linked after execution. The benchmark is evaluation-only: no training, no calibration fit and no redistribution of source audio.

## Actual local execution — 2026-10-29

Pinned SUPERB Wav2Vec2 evaluated 32 original clips / 64 clean-and-noisy observations on CPU, without fitting any weights or thresholds. There were 16 clips per source, four per class. Noise variants share recordings and are not independent samples. Runtime calibration status remains false.

| Source/domain | Condition | Original observations in condition | Raw macro F1 | ECE (10 bins) | Operational coverage |
|---|---|---:|---:|---:|---:|
| CREMA-D, acted English | clean | 16 | 0.267857 | 0.592812 | 0.8125 |
| CREMA-D, acted English | seeded Gaussian 20 dB | 16 | 0.260504 | 0.511103 | 0.75 |
| MDER-MA, spontaneous Darija media | clean, offline stereo average | 16 | 0.335852 | 0.434244 | 0 |
| MDER-MA, spontaneous Darija media | seeded Gaussian 20 dB | 16 | 0.553030 | 0.240770 | 0 |

The noisy Darija improvement is a small, correlated observation and not a demonstrated robustness benefit. The stereo average is an offline counterfactual transfer probe; deployed runtime still abstains on uncertain stereo and non-English language. No raw Darija label is approved for UI exposure by this experiment.

Observed within-domain clean/noisy raw-F1 gaps: 0.007353 acted, 0.217179 media. Language and accent gaps within domain are null because there are no two eligible verified slices. Comparing English acted with Darija media confounds language, corpus, recording and annotation. No causal accent/language fairness conclusion follows. Sample class counts are balanced by selection (imbalance ratio 1), unlike a natural call population.

Descriptive uniform and constant-neutral baselines yield raw macro F1 0.10 on each balanced four-class source. Uniform scores have ECE 0 despite poor discrimination; calibration must be read alongside accuracy/F1, not treated as proof of utility. Full per-class precision/recall, raw and operational confusion matrices, reliability bins, coverage and support are in [benchmark evidence](../implementation/evidence/step20-20261029/benchmark.json), [rescored metrics and baselines](../implementation/evidence/step20-20261029/rescored.json) and the STEP_20 report.

**Decision remains NO-GO for production emotion labels and punitive use.** There is no real Moroccan telephone or French evaluation, independent calibration set, verified accent breakdown, confidence-interval-powered representative sample or promotion holdout. Source review: [EMOTION_SOURCE_REVIEW.md](../data/EMOTION_SOURCE_REVIEW.md).

## Reproduce on the laptop

Install optional metrics with `uv pip install --python .venv/Scripts/python.exe -r requirements.emotion-evaluation.txt`. From repository root with PYTHONPATH set, `scripts/score_emotion_predictions.py <benchmark.json> <new-output.json>` reruns validated metrics without audio/model loading. `scripts/benchmark_emotion.py --manifest .local/step20-corpora/manifest.json --model .local/step19-emotion-model --output <new-output.json>` reruns local neural scoring in an environment with model/application dependencies; output is exclusively created. Both validate rather than overwrite evidence. Intake has a fixed bounded local destination and refuses an existing completed snapshot. See source review before using it.
