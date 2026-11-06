"""Pinned Wav2Vec2 CPU inference; optional torch imports occur only on construction."""

import hashlib
import importlib
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from ml.emotion.contracts import LABELS

WEIGHTS_SHA256 = "dac0f46128deec048751ce33eb1a9caecb570904d3d6cf732d6ec345cd6c2e1b"


class Wav2VecEmotion:
    def __init__(self, path: Path) -> None:
        if not path.is_absolute() or not path.is_dir():
            raise ValueError("An absolute pre-provisioned model directory is required")
        with (path / "pytorch_model.bin").open("rb") as f:
            if hashlib.file_digest(f, "sha256").hexdigest() != WEIGHTS_SHA256:
                raise ValueError("Emotion checkpoint integrity mismatch")
        self.torch = importlib.import_module("torch")
        transformers = importlib.import_module("transformers")
        self.extractor = transformers.Wav2Vec2FeatureExtractor.from_pretrained(
            str(path), local_files_only=True
        )
        self.model = (
            transformers.Wav2Vec2ForSequenceClassification.from_pretrained(
                str(path), local_files_only=True, weights_only=True
            )
            .cpu()
            .eval()
        )
        if self.model.config.id2label != {0: "neu", 1: "hap", 2: "ang", 3: "sad"}:
            raise ValueError("Unexpected emotion label taxonomy")

    def predict(self, samples: NDArray[np.float32]) -> dict[str, float]:
        if samples.ndim != 1 or not 8000 <= samples.size <= 160000:
            raise ValueError("Expected a mono 16 kHz window of 0.5–10 seconds")
        if not np.isfinite(samples).all():
            raise ValueError("Invalid waveform")
        inputs = self.extractor(samples, sampling_rate=16000, return_tensors="pt")
        with self.torch.inference_mode():
            probabilities = self.model(**inputs).logits.softmax(dim=-1)[0].tolist()
        return dict(zip(LABELS, probabilities, strict=True))
