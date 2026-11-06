# ruff: noqa: E402
"""Local synthetic smoke and resource measurement; not an emotion accuracy test."""

import io
import json
import sys
import time
import wave
from pathlib import Path

sys.path.append(str(Path(".venv/Lib/site-packages").resolve()))
import numpy as np
import psutil

from ml.emotion.contracts import EmotionTurn
from ml.emotion.model import Wav2VecEmotion
from ml.emotion.service import EmotionService

start = time.perf_counter()
model = Wav2VecEmotion(Path(".local/step19-emotion-model").resolve())
load_seconds = time.perf_counter() - start
samples = 0.1 * np.sin(np.arange(32000) * 2 * np.pi * 220 / 16000)
buf = io.BytesIO()
with wave.open(buf, "wb") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(16000)
    f.writeframes((samples * 32767).astype("<i2").tobytes())
service = EmotionService(model.predict, language="en")
start = time.perf_counter()
result = service.analyze(
    buf.getvalue(), "synthetic.wav", [EmotionTurn(start=0, end=2, speaker_id="fixture")]
)
elapsed = time.perf_counter() - start
assert result.status == "completed" and len(result.signals[0].probabilities) == 4
assert abs(sum(result.signals[0].probabilities.values()) - 1) < 1e-5
memory = psutil.Process().memory_info()
evidence = {
    "fixture": "2 seconds generated 220Hz tone; no human emotion ground truth",
    "load_seconds": load_seconds,
    "call_latency_seconds": elapsed,
    "device": "cpu",
    "process_working_set_bytes": memory.rss,
    "peak_process_working_set_bytes": getattr(memory, "peak_wset", None),
    "gpu_peak_vram_bytes": None,
    "macro_f1": None,
    "unknown_rate": int(result.signals[0].label == "Unknown"),
    "sample_size_calls": 1,
    "result": result.model_dump(mode="json"),
}
Path("docs/implementation/evidence/step19-20261029/model-smoke.json").write_text(
    json.dumps(evidence, indent=2)
)
print(json.dumps(evidence, indent=2))
