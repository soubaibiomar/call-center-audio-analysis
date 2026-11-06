# STEP_19 — Integrate acoustic emotion classification baseline

**Status: DONE — PASS WITH LIMITATIONS**, for an optional local acoustic baseline. Owner: ML / Codex. Date: 2026-10-29, Africa/Casablanca. Windows 11, PowerShell, uv-managed Python 3.12, local CPU inference; RTX 4060 not used by this stage. Branch `feature/project28-foundation`; HEAD `a37e4634af1d2947fc3c548d54e62bda0b0daf89`; pinned upstream `fed4b610742c1337147281fcec8f2cdcc0a79be5`. Changes remain uncommitted; no push or production deployment.

## 1. Goal and completed work

Added an optional acoustic classification stage alongside text analysis. It classifies bounded mono, diarization-aligned audio spans using a pinned local Wav2Vec2 checkpoint. It returns all four probabilities, timestamps, speaker identity, label or Unknown, checkpoint revision and an uncertainty disclaimer. It never asserts true feelings or automatically changes QA/HR scores.

The master instructions, STEP_INDEX, full STEP_19 prompt/template, latest STEP_18 handoff and current limitations were read. STEP_18's internal extractive prototype supplies no emotion functionality and introduces no prerequisite blocker for this independent acoustic baseline. Its production identity, retrieval and evaluation limitations remain. The user explicitly authorized this checkpoint download; no new dataset was downloaded. No training ran.

The stage runs in the batch graph when a local `EmotionService` is injected; otherwise it records disabled and performs no audio/model work. Standard application startup remains disabled until explicitly configured. This is not an enabled production rollout.

## 2. Upstream versus upgraded implementation

`git ls-tree -r --name-only fed4b610742c1337147281fcec8f2cdcc0a79be5 -- ml/emotion services/audio src/agents` verified the original agent paths and absence of an acoustic emotion package. Original summarization has text sentiment; it is not Wav2Vec2 acoustic inference.

| Area | Before | Actual upgraded path/symbol | Compatibility |
|---|---|---|---|
| Acoustic model | No upstream emotion model | `ml/emotion/model.py:Wav2VecEmotion` | Optional local runtime; no import-time loading |
| Turn inference | Existing ASR/diarization-aligned segments | `ml/emotion/service.py:EmotionService` | Uses accepted audio and preserves uncertain spans |
| Typed output | Text sentiment only | `ml/emotion/contracts.py` | Explicit distributions, timestamps, Unknown, calibrated=false |
| Graph | PII redaction followed by evidence collection | `emotion_step`, `emotion_node` | Optional stage between redaction and evidence collection |
| Reports/API | No acoustic output | `CallReport.acoustic_emotion`, regenerated OpenAPI | Optional additive field; old records remain valid |
| QA scores | Existing weighted rubric | No emotion input to scoring | Scores unchanged in enabled/disabled integration test |

Whole-workspace tracked diff: **40 files, 1062 insertions, 369 deletions** at capture. These totals include prior steps and exclude untracked additions; they are not STEP_19-only counts. Saved `working-tree-stat.txt`, `working-tree-names.txt` and `new-files.txt` distinguish accumulated changes and new files. Proposed `services/audio/` was not created: existing decoder utilities are reused instead of duplicated.

## 3. File inventory and interfaces

| File | Change | Purpose, inputs and outputs |
|---|---|---|
| `ml/__init__.py`, `ml/emotion/__init__.py` | Created | Explicit package boundaries for optional ML code |
| `ml/emotion/contracts.py` | Created | Validated turn timestamps, typed signal/result and caution text |
| `ml/emotion/model.py` | Created | Absolute provisioned directory to pinned CPU predictor; mono float waveform to probabilities |
| `ml/emotion/service.py` | Created | Bounded audio bytes/turns to cautious observations; no result cache |
| `src/graph/workflow.py` | Modified | Optional service construction parameter, stage execution and both report paths |
| `src/graph/state.py` | Modified | Optional acoustic result in state/report contract |
| `tests/emotion/test_baseline.py` | Created | Positive, abstention, bounds, integrity and error-path tests |
| `tests/integration/test_pipeline_end_to_end.py` | Modified | Enabled/disabled graph, report propagation and unchanged QA scores |
| `docs/api/openapi.json` | Regenerated | Actual additive report schema |
| `docs/development/emotion-local.md` | Created | Setup, usage, cache policy, bounds and limitations |
| This report, progress and limitations trackers | Created/updated | Durable status and STEP_20 handoff |
| `evidence/step19-20261029/` | Created | Real model smoke/resource JSON, runnable script, pinned model card/config, Git and test evidence |

The downloaded 378 MB weights remain ignored under `.local/`; no model binaries, audio data or credentials are added to Git. No root dependency pin, production image or migration was changed.

## 4. Code explanation and algorithm

`EmotionTurn` validates finite, ordered, nonnegative timestamps and retains nullable speaker ID plus overlap. `EmotionSignal` adds the full distribution, nullable confidence, label/Unknown, reason, model lineage and calibrated=false. `EmotionResult` distinguishes disabled, completed and unavailable, carries the disclaimer and declares the no-result-cache policy.

`Wav2VecEmotion.__init__` accepts an absolute pre-provisioned directory, streams SHA-256 over the checkpoint before loading optional libraries, loads a concrete Wav2Vec2 feature extractor/classifier with local-files-only and weights-only loading, selects CPU/eval mode and verifies the source label order. No remote custom model implementation is requested. Configuration/tokenizer files come from the pinned revision; runtime hashing specifically verifies weights, not every configuration byte.

`predict` requires a finite one-dimensional 16 kHz array of 0.5–10 seconds. The feature extractor normalizes as specified in its saved configuration; inference_mode disables gradient tracking. The classifier returns logits; softmax converts these into a four-class distribution in source order. The service validates that the keys, finite range and sum are correct before exposing them.

`EmotionService.analyze` rejects more than 120 input turns, serializes calls through an instance lock and invokes the existing ten-minute bounded decoder. Mono channels are preserved; stereo is not silently downmixed. Each source span is retained. Explicit overlap or overlapping spans with distinct IDs, absent speaker ID, invalid/out-of-audio timestamps, unsupported duration, stereo or low energy yields Unknown without invoking the classifier for that span. RMS below 1e-4 is an engineering silence gate, not a validated speech detector.

Eligible spans are sliced using original absolute timestamps at 16000 samples/second. Full probabilities and max probability remain visible even when the label abstains. Pilot label thresholds require max probability >=0.7, top-two margin >=0.15 and independently configured English. Unknown or other languages abstain while retaining probabilities. These thresholds are not calibrated. Long turns are retained as Unknown rather than silently truncated; turn splitting and representative multilingual operation remain future work.

The graph constructs EmotionTurns from existing transcription segments and their diarization attribution. It does not rerun diarization or invent roles. Without a service, the node returns disabled before opening audio. With a service, accepted intake audio is analyzed and results attach to ordinary/supervisor reports. Runtime failures return a content-free unavailable reason, preserving baseline analysis. The result is never included in summary/QA prompts, scoring weights or compliance decisions.

## 5. Every new import and dependency

| Imports | Origin / version | Purpose and rationale |
|---|---|---|
| `typing.Literal`, `typing.cast` | Python stdlib | Allowed output states/classes and narrowing after runtime taxonomy validation |
| `collections.abc.Callable` | stdlib | Injectable typed predictor; unit tests do not need torch |
| `hashlib`, `pathlib.Path` | stdlib | Streamed checkpoint integrity and trusted local file paths |
| `importlib` | stdlib | Lazy optional neural-library imports; disabled path avoids torch |
| `math` | stdlib | Finite/range/sum probability checks |
| `threading` | stdlib | One inference request per service instance |
| `pydantic.BaseModel, Field, model_validator` | Existing 2.11.3 main; 2.14.1 optional runtime | Typed contracts and timestamp bounds; no new install |
| `numpy`, `numpy.typing.NDArray` | Existing; optional runtime 2.5.4 | Float waveform slicing, energy and finite checks |
| Dynamic `torch` | Existing optional runtime 2.14.1 | CPU eval, inference_mode and softmax; no gradient training |
| Dynamic `transformers` | Existing optional runtime 4.57.6 | Wav2Vec2FeatureExtractor and Wav2Vec2ForSequenceClassification |
| Local emotion contracts/model/service | New project modules | Separate schema, optional runtime and graph/service orchestration |
| Local `SAMPLE_RATE`, `decode_resample` | Existing audio preprocessing; optional runtime PyAV 19.0.2 | Reuse bounded validated local decode rather than introduce another parser |
| Test `io`, `wave`, `Mock`, NumPy, pytest | stdlib/existing test libraries | Generate deterministic tone/silence/stereo fixtures and observe inference calls |
| Smoke `json`, `sys`, `time`, `Path`, wave/io | stdlib | Evidence serialization, local runtime composition and timing |
| Smoke `psutil` | Existing optional runtime 7.2.2 | OS-reported working set and peak working set; not Python-only allocation tracking |

Wav2Vec2 was chosen over another HuBERT runtime because the available concrete classifier has a small, documented four-label baseline and works in the existing local torch/transformers environment. No new package was installed. The experimental smoke appends primary site-packages for missing application dependencies; this is not a hash-locked production runtime. Provisioning uses existing requests/Hugging Face metadata, not hosted inference.

## 6. Concepts from first principles

Wav2Vec2 learns representations from audio; a classification head maps them into four real-valued logits. Softmax exponentiates and normalizes logits into numbers that sum to one. These are relative model scores: a 0.94 prediction does not establish a 94% chance that a caller truly feels that emotion.

Calibration asks whether predictions with a given probability agree with observed labels at that frequency on representative data. No such calibration was performed. An acoustic taxonomy is a dataset's chosen class vocabulary; this baseline has neutral/happy/angry/sad and cannot represent all human affect. Unknown is our abstention result, not a fifth learned class.

Segmenting by speaker attribution reduces mixing voices. Overlap cannot safely be assigned to a single speaker here, so the source interval remains visible as Unknown. A two-second mono span with known speaker identity can yield probabilities and an experimental label; an otherwise identical overlapping span never reaches the classifier.

## 7. Model, data, security and privacy

Selected [superb/wav2vec2-base-superb-er](https://huggingface.co/superb/wav2vec2-base-superb-er), revision `441a7599c3b22107314dcbd9166621c5c83f2cc5`. The model card labels the checkpoint **English, Apache-2.0**, describes 16 kHz input and IEMOCAP-derived four-class training. Verified config mapping: neu, hap, ang, sad. Source weight size **378,361,105 bytes**, SHA-256 `dac0f46128deec048751ce33eb1a9caecb570904d3d6cf732d6ec345cd6c2e1b`. Source card/config are archived with evidence. Model-card permissions do not independently grant rights to download or train on IEMOCAP recordings. No IEMOCAP or new human audio was obtained.

A generated tone is the only real-model smoke input. It has no true emotion label and establishes no language/accent accuracy. Test fixtures are synthetic. No training, fine-tuning, human labeling or held-out accuracy benchmark occurred. Macro F1 is deferred to STEP_20 rather than invented.

Only weights live in process; there is no application audio/prediction cache. The ordinary authorized report persists observations, so existing report access and retention policies still matter. The optional stage processes raw acoustic data, which cannot be made non-identifying by transcript redaction. No raw audio or exception content is logged by this implementation. Existing native decoder/metadata isolation gaps remain. CPU-first avoids GPU contention but does not enforce an OS process memory limit or a hard total inference deadline. The per-instance lock does not coordinate separate processes or impose a bounded request queue.

Unknown malicious/malformed audio and non-speech/noise can still receive confident model output. The real tone smoke demonstrates that limitation directly. This implementation is not a mental-health assessment, reliable emotion truth detector or suitable basis for adverse employment scoring.

## 8. Actual verification and commands

- `.venv/Scripts/python.exe -m pytest tests/emotion -q --tb=short`: initial **13 passed in 1.84s**; a subsequent integrity test was included in the final suite.
- Emotion + graph + schema focused run: **17 passed, 1 warning in 2.46s**, before the final integrity test.
- Full isolated-service command: `python -m pytest tests/unit tests/security tests/api tests/integration tests/workers tests/llm tests/datasets tests/rag tests/emotion -q --tb=short` with existing ignored PostgreSQL URL files: **417 passed, 1 warning in 56.23s**, no skips or failures; exit 0. See `regression.txt`.
- Ruff on ML/graph/changed integration/emotion tests: passed; nine files already formatted on final check.
- Mypy on `ml/emotion`, graph workflow and state: six source files passed.
- `scripts/export_api_schema.py`: regenerated actual OpenAPI; schema equality check passed in full suite.
- `git diff --check` on changed tracked source/test paths: passed.
- `.local/step13-asr-venv/Scripts/python.exe .local/step19-smoke.py` with HF offline/telemetry disabled and repository PYTHONPATH: actual pinned CPU inference completed, distribution asserted. Archived script at `evidence/step19-20261029/model-smoke.py`.

Test coverage includes enabled/disabled graph execution, exact score invariance for a high-angry fixture, timestamp/distribution retention, unknown language/low confidence, overlap, uncertain speaker, stereo, silence, out-of-bounds/short turns, malformed audio, invalid probabilities, budget exhaustion and modified checkpoint refusal before loading torch. Existing pipeline integration mocks ASR/summary/QA, while the neural smoke uses the actual emotion model. Neither is represented as a fully real multi-model call-center session.

Problems corrected during implementation: mypy initially found an ambiguous namespace package, resolved by explicit `ml/__init__.py`; label narrowing was made explicit after runtime validation. Initial lint issues were resolved by import sorting/formatting. Old checkpoint configuration emits a Transformers gradient_checkpointing deprecation warning; no gradient operation was performed. Existing pytest-asyncio and Starlette/AnyIO warnings remain documented. No failed check was counted as passed.

## 9. Analytics, formulas and interpretation

Raw evidence: [model-smoke.json](evidence/step19-20261029/model-smoke.json).

| Metric | Actual | Conditions and limit |
|---|---|---|
| Model load and weight verification | **14.8874795 seconds** | Single CPU cold construction, includes hashing/import/loading |
| One stage latency | **0.2820366 seconds** | Two-second generated tone, one known-ID mono span; excludes model load |
| Process working set / peak working set | **875,503,616 bytes** (about 835 MiB) | OS process measure including runtime/dependencies/model; not incremental model allocation |
| Unknown/abstain rate | **0/1 = 0%** | One synthetic tone; not speech-population abstention rate |
| Output distribution | neutral 0.94450736, happy 0.03782801, angry 0.01661465, sad 0.00105 | Uncalibrated classifier response to non-speech; not ground truth |
| Macro F1 baseline | **Not measured** | No licensed labeled held-out emotion set used |
| Representative call latency, throughput, p50/p95 | **Not measured** | One synthetic span is not a call benchmark |
| GPU peak VRAM | **Not measured** | CPU selected; no GPU measurement performed |
| Upstream performance baseline | **Not measured** | No upstream acoustic stage exists |

Unknown rate = number of Unknown signals / emitted signals. Macro F1 would average per-class F1 over defined classes using reviewed ground truth; it cannot be derived from this synthetic tone. There is no accuracy/speedup or calibration improvement claim.

Resource/cache decision: leave disabled by default, instantiate one CPU model/service per explicitly enabled worker, serialize inference and cap inputs. A rollout requires sustained-load and representative quality evaluation; the single smoke does not establish service capacity.

## 10. Technical questions and answers

1. **Why not call the result true feelings?** The model learned dataset patterns influenced by speaker, dialect, noise and recording conditions. A tone received a high neutral probability, illustrating why confidence is not psychological truth.
2. **Why separate speakers and preserve overlap?** A mixture can be assigned to the wrong person. Here overlap, missing identity and stereo ambiguity produce Unknown while retaining original timing.
3. **What is calibration?** Agreement between probability bins and real labeled frequencies on representative data. Thresholds here are pilot engineering settings; calibrated remains false.
4. **Can it affect HR scores?** The code has no path from acoustic output into scoring prompts/weights. Enabled/disabled integration returns identical overall and compliance scores. This prevents automatic score changes in this implementation; future consumers must retain that boundary.
5. **How can it be disabled?** Omit the `emotion` argument from `compile_workflow`. The node returns disabled before reading audio or constructing a model.
6. **Why CPU and no audio cache?** CPU avoids concurrent 8 GB GPU pressure. No acoustic/result cache reduces sensitive derived-data persistence; model weights alone remain reusable in memory.
7. **What if a turn is long or the model fails?** Long/short unsupported turns stay Unknown. Decode/inference failures produce unavailable with a content-free reason, preserving the baseline pipeline rather than guessing.
8. **What proves completion and what remains?** Real pinned inference, resource evidence, typed integration and passing tests satisfy this baseline step. Accuracy, calibration, bias, transfer and operational capacity require STEP_20 and later deployment validation.

## 11. Decisions, limitations and risk register

- **High: domain/language transfer.** English/IEMOCAP-derived training is not representative Darija/French/contact-center validation. Owner ML; STEP_20 must measure permitted reviewed data by language/accent.
- **High: attribution errors and non-speech confidence.** IDs depend on preceding diarization; overlap/stereo abstain but this does not guarantee correct identity. No robust OOD/speech detector exists.
- **High: privacy and deployment.** Raw waveform processing and existing native decode boundaries remain. Cache policy is local, not an erasure implementation for report persistence. Owner Platform.
- **Medium: scale/runtime.** CPU resources measured on one tone; per-instance locking, 120 turns, ten-minute decode and 0.5–10-second supported spans restrict coverage. No global deadline/queue cap or production image packaging.
- **Medium: lineage.** Pinned weight hash verified; configuration bytes/local environment remain trusted and are not a complete reproducible deployment lock.
- **Evaluation limits.** No macro F1, calibration, representative abstention/latency or GPU memory benchmark. No automatic HR score change. No synthetic fixture is presented as a human emotion label.

Inherited audio, OIDC, retention, RAG and production limitations remain in the tracker. No request to remove all platform limitations is implied or declared complete by this baseline.

## 12. Deliverables, acceptance and next handoff

All STEP_19 baseline gates pass within the documented optional internal scope: stage runs and can be disabled; probabilities/Unknown retain uncertainty; labels do not automatically change scores. **Decision: PASS WITH LIMITATIONS.** STEP_20 is next eligible, subject to its reviewed-data prerequisites; it was not executed.

Next safe command: `Get-Content prompts/STEP_20_benchmark_emotion_model_and_assess_transfer_bias_PROMPT.md`. Review permissions and labels before acquiring/evaluating human audio. Assess per-class and per-language performance, calibration and abstention instead of assuming checkpoint model-card results transfer.

- [x] Full prompt and preceding state reviewed; prior work preserved.
- [x] Checkpoint language/license/taxonomy and weight checksum verified.
- [x] Actual local inference and resource/cache decision recorded.
- [x] Typed graph/report/API integration and disabled behavior tested.
- [x] Full service-configured regression, lint/type/format checks passed.
- [x] Synthetic metrics labeled; no human emotional ground truth or learning improvement invented.
- [x] Documentation, evidence and limitations saved; no commit, push or public deployment.

## 13. Approved ERP UI design / visual contract verification

No rendered frontend changed. `design/UI_DESIGN_SYSTEM.md` and UI acceptance checklist were reviewed; visual screenshot comparison, responsive behavior and accessibility are **Not applicable** to this backend-only change. Existing Gradio is preserved. No Emotion Analytics screen or screenshot is claimed.

The additive report/OpenAPI field `acoustic_emotion` carries model identity/revision, timestamped probabilities, confidence, label/Unknown, reason, status and disclaimer for the future approved green-neutral panel. It must display the uncertainty notice, distinguish disabled/unavailable from a measured result, avoid interpreting Unknown as neutral and keep these signals separate from employee scores. Real UI work still requires reference comparison, actual desktop/mobile screenshots and accessibility checks.
