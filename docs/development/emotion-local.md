# Local acoustic emotion baseline (STEP_19)

The optional emotion stage is disabled by default. It never changes QA scores, compliance flags or HR decisions. Outputs describe experimental acoustic pattern classifications, not true feelings; probabilities are uncalibrated. The selected checkpoint is English-only; other or unknown languages retain probabilities but use `Unknown` labels.

## Provisioning and local batch invocation

Use `superb/wav2vec2-base-superb-er` revision `441a7599c3b22107314dcbd9166621c5c83f2cc5`, an Apache-2.0 checkpoint with IEMOCAP-derived neutral/happy/angry/sad classes. It expects 16 kHz speech. The model-weight SHA-256 is `dac0f46128deec048751ce33eb1a9caecb570904d3d6cf732d6ec345cd6c2e1b`. Source dataset terms are independent of the model card; no IEMOCAP audio was downloaded. Deployment rights and representative transfer accuracy need their own review.

Provision weights, config and preprocessor into an absolute local directory. Use a uv-managed environment containing torch, transformers and application dependencies. Runtime only loads local files and verifies the pinned checkpoint; no hosted inference or automatic download occurs. The local smoke used `.local/step13-asr-venv/Scripts/python.exe`; its runner appends the primary environment's site-packages for missing application dependencies. This is a local experimental runtime, not a deployment lock.

```python
from pathlib import Path
from ml.emotion.model import Wav2VecEmotion
from ml.emotion.service import EmotionService
from src.graph.workflow import compile_workflow

model = Wav2VecEmotion(Path(".local/step19-emotion-model").resolve())
emotion = EmotionService(model.predict, language="en")  # only if language is independently known
workflow = compile_workflow(config, emotion=emotion)
# Invoke with normal accepted AudioInput; the graph supplies accepted recording/turns.
```

Omit `emotion` to disable it. No model loads on import. Only one service request infers at a time using a lock. Keep one service/model per worker and destroy the worker to release weights. CPU-first execution avoids competing with ASR on 8 GB VRAM. No audio, predictions or transcript data is cached by this stage; outputs persist only with the ordinary authorized report. The feature is not wired to an unprotected API switch.

## Bounds and abstention

Up to 120 transcription/diarization-aligned turns; mono audio; at most ten minutes decoded by the existing bounded decoder; classified windows 0.5–10 seconds. Longer turns remain Unknown rather than truncating them. Stereo requires independently verified channel isolation and currently abstains. No inferred role from channel position. Turns with absent speaker IDs, overlap, invalid duration or insufficient energy remain in output as Unknown. Probabilities are retained for low-confidence/unsupported-language inferences. Pilot label gates require confidence >=0.7 and margin >=0.15; neither threshold is calibrated.

Failures return `unavailable` and a content-free reason rather than interrupting the call workflow. The decoder inherits the current project's end-to-end media isolation limitations. There is no hard total inference deadline; caps bound input size but do not constitute OS isolation. Unknown patterns of non-speech/noise can still receive confident probabilities; no robust speech detector or out-of-distribution detector is claimed.

## Validation and handoff

See the STEP_19 report and `docs/implementation/evidence/step19-20261029/`. The generated-tone run validates local execution and resource use only; macro F1 and representative call latency are unmeasured. STEP_20 must evaluate labeled, permissioned speech, calibration, abstention and language/accent transfer before any deployment accuracy claim. No current output should be used for adverse employment decisions.

STEP_20 provides metrics-only tooling and a local source-reviewed acted/media benchmark. Install `requirements.emotion-evaluation.txt` or the `emotion-evaluation` project extra with uv. It does not approve production labels; see `docs/benchmarks/EMOTION.md` and the STEP_20 report for the measured limitations and NO-GO decision. The STEP_19 confidence/language policy is now shared as `operational_label` without changing thresholds.
