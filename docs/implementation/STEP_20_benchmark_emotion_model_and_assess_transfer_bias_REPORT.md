# STEP_20 — Benchmark emotion model and assess transfer bias

**Status: DONE — PASS WITH LIMITATIONS for research benchmarking; NO-GO for production emotion exposure.** Owner ML / Codex. Executed 2026-10-29 (Africa/Casablanca), Windows 11, PowerShell, uv Python 3.12. Neural inference ran locally on CPU. Branch `feature/project28-foundation`, working HEAD `a37e4634af1d2947fc3c548d54e62bda0b0daf89`; original upstream `fed4b610742c1337147281fcec8f2cdcc0a79be5`. No training, calibration fit, commit, push or public deployment.

## 1. Goal and completed work

Built reproducible four-class emotion scoring, per-class precision/recall/support, raw and operational confusion matrices, expected calibration error (ECE), class counts, abstention/coverage, selective accuracy and language/accent/noise slices. Ran the actual STEP_19 Wav2Vec2 checkpoint on 32 public-source clips and seeded noisy variants: 64 predictions. Kept acted English and spontaneous Darija media results separate. Established explicit NO-GO criteria for production emotion labels and punitive decisions.

Reviewed the master/index, full STEP_20 prompt and report template, STEP_19 source/report, working Git state and saved limitations. STEP_19's pinned model and optional runtime were available. No labeled Moroccan customer-call corpus was local; the user requested web research. Research identified MDER-MA and MORAD, but did not establish an accessible reviewed Moroccan telephone corpus. A source-reviewed bounded media transfer probe was completed instead of presenting acted or media speech as real calls. Real-call/French/verified-accent evaluation remains Not measured.

## 2. Actual upstream versus upgraded implementation

| Capability | Upstream / prior actual behavior | Changed path and outcome |
|---|---|---|
| Emotion evaluation | No `ml/evaluation/emotion.py` upstream; STEP_19 only tone execution smoke | New typed offline evaluator with scikit-learn metrics and manual ECE |
| Uncertainty policy | STEP_19 confidence/margin/English checks embedded in service | `operational_label` extracted unchanged into contracts; evaluator reuses it |
| Reproducible data | No emotion benchmark manifest | Bounded source intake, pinned revisions, source checksums, rights/label provenance, retention |
| Bias reporting | No measured transfer slices | Separate acted/media domains, explicit unknown accents, noise slices and null unavailable gaps |
| Benchmark runner | No real emotion scoring runner | Local CPU inference and validated prediction-only rescoring |
| Packaging | Setuptools included `src` and `services`, omitted new ML package | `ml` and `ml.*` included; built wheel verified |
| UI decision | No evidence-based emotion exposure decision | Written prospective criteria and actual NO-GO; no UI rollout |

The accumulated tracked diff captured **40 files, 1063 insertions, 369 deletions**; it includes prior steps and excludes new untracked files. `working-tree-stat.txt`, `working-tree-names.txt` and `new-files.txt` record the distinction. Ordinary diff cannot describe untracked additions. Existing ASR, weighted QA, RAG, authentication and report behavior were preserved; policy extraction was a behavior-preserving refactor, not a threshold change.

## 3. Created and modified files

| File | Change and purpose |
|---|---|
| `ml/evaluation/__init__.py`, `ml/evaluation/emotion.py` | New evaluation package; validated prediction rows to domain-separated metrics |
| `scripts/intake_emotion_candidates.py` | New bounded metadata-first public subset intake; refuses existing completed snapshot |
| `scripts/benchmark_emotion.py` | New manifest validation and actual local model scoring; outputs immutable-by-convention exclusive JSON |
| `scripts/score_emotion_predictions.py` | New metrics-only reproduction and descriptive baselines without model/audio loading |
| `ml/emotion/contracts.py`, `ml/emotion/service.py` | Share the existing pilot label policy, preserving probabilities and abstention semantics |
| `pyproject.toml` | Optional pinned evaluation dependency and explicit ML packaging |
| `requirements.emotion-evaluation.txt` | uv-friendly optional scikit-learn installation pin |
| `tests/emotion/test_evaluation.py`, `test_benchmark_manifest.py` | Hand-computed metric oracles and provenance/path/retention validation |
| `docs/benchmarks/EMOTION.md` | Frozen-before-scoring protocol, numeric results and exposure criteria |
| `docs/data/EMOTION_SOURCE_REVIEW.md`, `DATASET_CATALOG.md` | Source/license/label review, limits and acquisition scope |
| Report, progress, current limitations, `evidence/step20-20261029/` | Executed outcomes, reproducibility, wheel and version evidence |

Source audio, source CSV text and the detailed input manifest stay in ignored `.local/step20-corpora`. Public artifacts contain pseudonymous/hashes, probabilities and metrics, not source audio or transcripts. No production API route/frontend component was created.

## 4. Important components and algorithms

`EvaluationRow` requires a known domain (acted/media/real_call), four-class truth, source revision, record/speaker keys and slice metadata. Pydantic rejects extra fields and malformed distributions. Probabilities must contain exactly the four labels, be finite and bounded, and sum to one. The scorer rejects empty evaluations and duplicate record/condition pairs.

`metrics` computes raw argmax predictions in fixed label order. scikit-learn `precision_recall_fscore_support` produces precision/recall/F1/support with all four classes and zero_division=0. Raw macro F1 averages those four F1 values. Operational metrics use the emitted label, including Unknown: rejected examples become false negatives rather than being silently dropped. The operational confusion matrix has five axes (four classes plus Unknown); its Unknown truth row is zero because no Unknown truth class is evaluated. Raw confusion is four-by-four. Coverage is accepted/total; selective accuracy is correct/accepted and null when no example is accepted.

ECE uses ten equal-width confidence bins. Each raw prediction contributes its top-class probability and correctness. `min(int(confidence*bins), bins-1)` places confidence=1 in the final bin. For each nonempty bin, ECE adds its sample fraction multiplied by the absolute difference between average confidence and accuracy. Reliability records preserve counts and means. It describes current scores; it does not fit a calibrator. ECE is not computed only on conveniently accepted predictions.

`evaluate` never pools acted/media/real-call domains into a headline score. Each domain has language, accent and noise slices. A worst-gap value requires at least two eligible slices with >=4 observations; unknown/unverified attributes do not count as validated comparisons. Missing comparisons are null. Missing classes are listed; imbalance ratio compares nonzero class counts and must be read alongside that list.

Intake selects four examples per source/class before model prediction, preferring distinct published speaker keys within each class. It pins source revisions and checks source LFS hashes. A 40 MiB total and 3 MiB per-response budget prevent full-corpus acquisition. Only adult-age-metadata MDER examples within the declared 0.5–10-second range are eligible. These are source metadata checks, not independent identity verification. The completed snapshot is preserved on rerun.

`validate_manifest` checks evaluation-only purpose, permission/label/license notes, review date, record bounds and uniqueness, local path containment including resolved paths, per-file bounds and SHA-256 before constructing the neural model. This enforces the local declared contract, not independent proof of consent or an immutable governance record.

`benchmark_emotion` decodes/resamples locally to 16 kHz. An offline stereo average for MDER probes transfer counterfactually; production runtime still abstains on uncertain stereo. No source clip is truncated to fit. Each eligible source produces clean and target-20-dB Gaussian-noise predictions. The seed comes from the source hash, and noise standard deviation is clean RMS/10. Realized SNR was independently checked: **19.9495–20.0709 dB**. No denoising or physical telephone-channel simulation is claimed. Noise variants are correlated with their source.

The shared `operational_label` retains STEP_19's English-only, confidence >=0.7 and top-two margin >=0.15 pilot rules. Unsupported Darija produces Unknown even when raw probabilities exist. `score_emotion_predictions` validates saved rows and reproduces metrics without loading weights or audio. Uniform and constant-neutral descriptive baselines use the same fixed taxonomy; they are not trained/promoted models.

## 5. Imports, versions and dependencies

| Import/module | Origin and reason |
|---|---|
| `importlib` | Standard library; loads optional scikit-learn metrics only when evaluation runs |
| `math`, `collections.Counter` | Standard library; finite/sum checks and class counts |
| `typing.Any`, `Literal`, `cast` | Typed heterogeneous metric JSON, explicit domains and narrowed labels; source validation remains explicit |
| Pydantic `BaseModel`, `ConfigDict`, `Field`, `model_validator` | Existing main 2.11.3; schema, nonempty provenance and probability checks |
| Local `LABELS`, `EmotionLabel`, `operational_label` | One taxonomy and unchanged runtime decision policy shared with evaluation |
| Dynamic `sklearn.metrics` | New optional **scikit-learn 1.9.1**; precision_recall_fscore_support and confusion_matrix |
| `argparse`, `json`, `hashlib`, `pathlib.Path` | CLI parsing, safe data formats, checksums and contained local paths |
| `datetime.UTC/date/datetime`, `time` | Retention check and observed inference timing |
| `numpy` | Existing 2.5.4 at evaluation; averaging/slicing and seeded Gaussian perturbation |
| `requests`, `csv`, `io`, `huggingface_hub.HfApi` | Existing acquisition runtime; bounded HTTPS transfer, metadata parsing and pinned file hash discovery |
| Local `Wav2VecEmotion`, `decode_resample`, `EvaluationRow/evaluate/metrics` | Existing model/decoder and new reusable evaluation interfaces |
| pytest, ValidationError, synthetic fixture helpers | Existing test tools; exact oracles and refused-input coverage |

Installed optional metrics through `uv pip install --python .venv/Scripts/python.exe -r requirements.emotion-evaluation.txt`. Observed evaluation versions: scikit-learn 1.9.1, NumPy 2.5.4, SciPy 1.18.1, Pydantic 2.11.3. No new neural model or torch install was needed. Transitive metrics dependencies were installed by uv; default runtime dependencies do not require this extra. The optional requirement is pinned but not a complete hash-locked cross-platform environment. Direct scikit-learn metric reuse avoids duplicating confusion/F1 logic; manual ECE makes the binning convention explicit and testable.

## 6. Concepts from first principles

Precision measures how often a predicted class is correct; recall measures how many examples of a true class were found. Their harmonic mean is F1. Macro F1 averages equally across classes, so a common neutral class cannot hide failures on less common classes. A confusion matrix counts which true classes become which predictions; its label order must be explicit.

Class imbalance means class frequencies differ. Our balanced sampling makes sample imbalance ratio 1; it says nothing about real call frequencies. Calibration compares probabilities with empirical correctness. A uniform four-class predictor can have ECE zero on a balanced subset while achieving only raw macro F1 0.10; calibration alone is not utility.

A slice is a documented subgroup or condition. A difference between acted English and Darija media confounds language with source, recording and annotation; it does not isolate an accent effect. Adding noise to the same recording tests a paired transformation, not a new independent speaker or a real telephone call.

## 7. Data/model lineage, rights and leakage

Model: STEP_19 pinned `superb/wav2vec2-base-superb-er`, revision `441a7599c3b22107314dcbd9166621c5c83f2cc5`; its loader verifies the previously recorded checkpoint SHA-256. Model and application execute locally; no waveform was sent to hosted inference. Runtime warning about the old gradient_checkpointing configuration does not mean training ran.

Source review: [EMOTION_SOURCE_REVIEW.md](../data/EMOTION_SOURCE_REVIEW.md). CREMA-D author repository at `1658cd342dff90010aa843eaeebd53610a08b1dc` supplies acted English and audio-majority human-perception labels; ODbL/DbCL source terms are recorded. MDER-MA original [v1](https://data.mendeley.com/datasets/yzsw3ff6rn/1) explicitly lists CC BY 4.0. Its [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12433488/) describes Darija media sources and native human annotation. A [mirror](https://huggingface.co/datasets/FatimahEmadEldin/Moroccan-Arabic-Multimodal-Emotion-Recognition) at `4a9e6b02b78516ac50109cc2816386ac699aff95` provided bounded files. Mirror license uncertainty was checked against the original record; no independent guarantee of all underlying media/privacy rights is asserted. MORAD requires case-by-case access and was not acquired.

Selected **16 original clips per source**, four per class; **5 English and 15 Darija published speaker keys** occur, not independently verified identities. Source majority labels are subjective perception, not true feelings or independent project relabeling. No emotion labels were inferred from transcripts. All four source classes map explicitly to the model's neutral/happy/angry/sad vocabulary; other CREMA classes are excluded before prediction.

The MDER mirror test metadata did not provide an adult neutral example within the chosen bounds. Selection therefore used full metadata.csv and records that it is not mirror-test-only. No project model training or tuning used these data, but model/vendor pretraining overlap and cross-source speaker independence are unknown. This evaluated snapshot must not be reused as an untouched promotion holdout. Calibration and threshold optimization were not fitted here.

The successful acquisition downloaded **19,870,333 bytes** including source metadata; selected audio totals **19,175,202 bytes**. The local manifest records purpose, revision, hashes, label provenance and the existing project review deadline **2026-11-28**. Retention is manual. Public results hash record/speaker keys and omit transcript/audio; hashing is not a guarantee of anonymity. No private customer data or source demographics are published. Evaluation predictions are intentionally retained as benchmark evidence; they are not used as a runtime prediction cache.

## 8. Tests, failures and actual execution

Executed local neural command in the existing optional runtime with application site-packages appended and HF offline/telemetry disabled:

```powershell
$env:PYTHONPATH=(Get-Location).Path
$env:HF_HUB_OFFLINE='1'
$env:HF_HUB_DISABLE_TELEMETRY='1'
# In the provisioned model/application runtime:
python scripts/benchmark_emotion.py --manifest .local/step20-corpora/manifest.json --model .local/step19-emotion-model --output <new-result.json>
# Metrics only, primary environment:
.venv/Scripts/python.exe scripts/score_emotion_predictions.py docs/implementation/evidence/step20-20261029/benchmark.json <new-rescored.json>
```

The real scoring run completed **64 predictions**, **10.9873417 seconds** cumulative inference excluding load/decode. Dataset acquisition and scoring returned exit 0. Repeated metric evaluation over identical saved predictions was exactly equal; this is metrics reproducibility, not a bitwise-neural portability claim. Prediction SHA-256: `8b700d980eb43b0ed6219b6e30159d266aec8e35413edd7a30f6bbea2df672f7`.

Focused emotion suite: **24 passed in 3.71s**, no skips. Oracles cover perfect predictions/ECE 0.3, an always-neutral classifier with raw macro F1 0.10 and ECE 0.75, all-Unknown operational errors, confidence=1 final bin, known 0.9 slice gap, domain separation, missing slices, malformed probabilities, duplicates/empty inputs, checksum alteration, wrong purpose, expired review and path escape. STEP_19's low-confidence and unsupported-language abstention tests still pass.

Ruff lint and formatting passed for changed ML/evaluation/scripts/tests. Mypy passed **eight source files** (evaluation, model/service/contracts and scoring scripts). `uv build --wheel --out-dir .local/step20-dist` succeeded; actual wheel inspection confirmed both evaluation and emotion modules, with no audio/model-weight/environment file entries. This corrected the real prior package omission of `ml.*` rather than only testing source-checkout imports. No installed production environment was replaced.

Initial full service-configured run: **425 passed, 2 failed, 1 warning in 82.75s**. Both failures were connection timeouts to the stopped isolated knowledge-test container, not emotion assertions. Restarted only `project28-knowledge-test` and reran the same full command; final outcome: **427 passed, 1 warning in 61.74s**, exit 0, no skips. See `regression-final.txt`. No failure or skip is counted as a pass.

Other implementation failures corrected: intake codec spelling `utf8-sig` to `utf-8-sig`; explicit metric Counter/baseline annotations for strict mypy; lint/format issues. Direct local Mendeley access encountered certificate failure; no TLS bypass was introduced, and the pinned mirror supplied audio after the original license was checked through web access. Existing pytest-asyncio and Starlette/AnyIO deprecation warnings remain.

## 9. Analytics, baselines and interpretation

[Raw benchmark](evidence/step20-20261029/benchmark.json), [recomputed metrics/baselines](evidence/step20-20261029/rescored.json), [reproducibility](evidence/step20-20261029/reproducibility.json), [realized noise](evidence/step20-20261029/noise-check.json).

| Domain / condition | n | Raw macro F1 | ECE, ten bins | Operational coverage |
|---|---:|---:|---:|---:|
| Acted English, clean | 16 | **0.267857** | **0.592812** | **81.25%** |
| Acted English, target 20 dB Gaussian | 16 | **0.260504** | **0.511103** | **75%** |
| Darija media, clean offline mono average | 16 | **0.335852** | **0.434244** | **0%** |
| Darija media, target 20 dB Gaussian | 16 | **0.553030** | **0.240770** | **0%** |

These are 32 original clips, not 64 independent recordings. Pooled within-source raw macro F1 across conditions: acted **0.264069**, media **0.447917**. Pooled operational macro F1: acted **0.183386**, media **0**. Acted accepted-only accuracy was **0.36** across conditions; Darija selective accuracy is null because all abstained. Raw Darija scores are counterfactual research probes, not operational approved labels. Runtime also rejects ambiguous stereo; the offline averaging step does not alter that policy.

Per-class raw precision/recall/support and both confusion matrices are stored in JSON. Across both conditions, acted neutral/happy recall was zero, angry recall 1 and sad recall 0.5; media neutral recall was zero, happy 0.625, angry 0.875 and sad 0.5. Counts are eight per class because variants repeat four originals. Small source selection and subjective labels preclude broad quality claims.

Uniform and constant-neutral baselines both score raw macro F1 **0.10** per balanced domain. Uniform ECE is 0; constant-neutral ECE is 0.75. These are descriptive, not trained alternatives or evidence of readiness. Macro F1 = mean over the fixed four per-class F1 values, including zero values. ECE = sum over confidence bins of bin fraction times absolute calibration gap. Worst observed clean/noisy raw-F1 gap was **0.007353** for acted and **0.217179** for media. The apparent Darija noise improvement is a small correlated result, not established robustness benefit.

Verified accent/language gaps within source: **Not measured / null** (no two eligible verified slices). Real telephone/Darija/French population performance, inter-annotator agreement independently checked by this project, calibrated deployment performance, statistical confidence intervals, representative end-to-end latency/throughput and GPU VRAM: **Not measured**. No production bias reduction or neural improvement is claimed.

## 10. Questions with answers

1. **Why macro F1?** It weighs each class equally. A frequent neutral class cannot hide zero recall on rare emotions; we retain fixed labels even when a slice lacks a class and disclose missing support.
2. **Is CREMA-D proof on phone calls?** No. It is acted English. MDER is spontaneous Darija media, also not a telephone/customer-call benchmark. Neither licenses a general real-call accuracy claim.
3. **Why human review?** Dataset emotion labels are perceptions, not direct measurements of feelings. Review is required before displaying consequential suggestions; automatic punitive scoring remains prohibited.
4. **Does ECE zero mean useful predictions?** No. Uniform probabilities can be calibrated to a balanced label frequency while failing discrimination. Read F1, class recall, coverage and calibration together.
5. **Why include Unknown in scoring?** Dropping abstentions inflates apparent performance. Operational macro F1 counts missed true classes; selective accuracy is reported separately with coverage.
6. **Why not infer accent from a speaker's name/region?** Identity or region is not reliable acoustic accent ground truth. Unverified metadata remains unverified, and absent comparison groups yield null rather than a fabricated zero gap.
7. **Can this benchmark tune thresholds?** No thresholds were fitted. Future calibration/tuning needs separate data; this explored snapshot cannot then be called an untouched final promotion test.
8. **Why did noisy media score better?** This small paired sample shows an observation, not a causal explanation or general benefit. Source labels, preprocessing and sample variance can affect it; independent larger validation is needed.

## 11. Decisions, risks and limitations

**Production UI emotion labels: NO-GO.** The prospective protocol in `docs/benchmarks/EMOTION.md` was written before scoring. Planning floors include reviewed permitted real telephone speech for every supported language, independent speakers and class support, speaker/conversation-disjoint holdout, separate calibration set, uncertainty intervals, per-class/slice thresholds and human stakeholder review. Provisional metric thresholds are planning criteria, not a statistical guarantee or authorization to deploy.

This experiment fails target-domain coverage and provides weak raw discrimination/calibration. It cannot assess verified accents or real French/Moroccan calls. Keep the feature disabled by default; research-only probability inspection requires cautious wording and access controls. Do not equate acoustic classes with mental state, hide abstentions or use them to alter employment/QA scores.

Remaining risks: small label-balanced source sampling, media rights/annotation assumptions, unverified speaker keys and pretraining overlap, no independent untouched promotion test, synthetic-noise-only coverage, no confidence intervals and no fitted calibration. Source and split provenance are disclosed instead of silently describing all data as a test partition. Retention and local manifest trust remain manual; prior platform/audio/RAG/privacy limitations persist.

## 12. Completion decision, evidence checklist and handoff

**PASS WITH LIMITATIONS for the research evaluation step**, with an explicit production **NO-GO**. Done gates: reproducible benchmark and scorer executed; source/domain/slice limits disclosed without overgeneralizing; low-confidence/unsupported cases abstain through the unchanged runtime policy and passing tests. This is not completion of real-call validation or a claim that every intended bias slice was measurable.

Next eligible numbered step: **STEP_21 — collect reviewed emotion labels**, subject to permissions and reviewer workflow prerequisites. It was not executed. It should help address actual label/domain coverage before re-evaluating exposure. Do not automatically advance or enable a production emotion panel.

- [x] Actual local checkpoint predictions and typed metric output saved.
- [x] Source rights/label review, revisions, checksums and sample selection documented.
- [x] Acted/media domains separated; missing real-call/French/accent data explicit.
- [x] Hand-computed metric, abstention and provenance tests executed.
- [x] Packaging, dependency, lint/type/format checks executed.
- [x] Failed service run preserved and corrected rerun distinguished.
- [x] UI decision and future gates written; no training, push or customer-data use.

## 13. Approved ERP UI design / visual contract verification

No frontend screen or HTTP route was changed, so screenshots, responsive behavior and visual/accessibility acceptance are **Not applicable**. Existing Gradio and the STEP_19 report schema remain. Offline metric JSON provides domain labels, per-class support, confusion axes, reliability bins, coverage and null missing-slice results for future green-neutral evaluation panels.

Future UI must display source/domain/sample size, uncalibrated status, Unknown/disabled/unavailable states, class counts and uncertainty. It must not display unsupported emotion suggestion cards or convert these observations into punitive decisions. The approved Commercially reference and real screenshots remain mandatory when that frontend is implemented; no visual compliance is inferred from these backend files.
