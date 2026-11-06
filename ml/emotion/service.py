"""Bounded turn-based acoustic inference. Audio and predictions are never cached."""

import math
import threading
from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray

from ml.emotion.contracts import (
    LABELS,
    EmotionResult,
    EmotionSignal,
    EmotionTurn,
    operational_label,
)
from src.utils.audio_preprocessing import SAMPLE_RATE, decode_resample


class EmotionService:
    def __init__(
        self,
        predict: Callable[[NDArray[np.float32]], dict[str, float]],
        *,
        language: str = "unknown",
    ) -> None:
        self.predict = predict
        self.language = language
        self.lock = threading.Lock()

    def analyze(self, data: bytes, filename: str, turns: list[EmotionTurn]) -> EmotionResult:
        if len(turns) > 120:
            return EmotionResult(
                status="unavailable", reason="Turn budget exceeded", language=self.language
            )
        try:
            with self.lock:
                return self._analyze(data, filename, turns)
        except Exception:
            # Do not leak waveform, path, transcript or runtime exception content.
            return EmotionResult(
                status="unavailable", reason="Emotion processing failed", language=self.language
            )

    def _analyze(self, data: bytes, filename: str, turns: list[EmotionTurn]) -> EmotionResult:
        audio = decode_resample(data, filename)
        duration = audio.samples.shape[1] / SAMPLE_RATE
        signals: list[EmotionSignal] = []
        for turn in turns:
            common = turn.model_dump()
            reason = None
            if turn.end > duration + 1 / SAMPLE_RATE:
                reason = "Turn outside decoded audio"
            elif turn.overlap or any(
                other is not turn
                and other.speaker_id != turn.speaker_id
                and max(turn.start, other.start) < min(turn.end, other.end)
                for other in turns
            ):
                reason = "Overlapping speakers"
            elif not turn.speaker_id:
                reason = "Uncertain speaker identity"
            elif audio.original_channels != 1:
                reason = "Stereo source requires verified channel isolation"
            elif not 0.5 <= turn.end - turn.start <= 10:
                reason = "Turn duration outside 0.5–10 second budget"
            if reason:
                signals.append(EmotionSignal(**common, reason=reason))
                continue
            samples = audio.samples[0, int(turn.start * SAMPLE_RATE) : int(turn.end * SAMPLE_RATE)]
            if float(np.sqrt(np.mean(samples.astype(np.float64) ** 2))) < 1e-4:
                signals.append(EmotionSignal(**common, reason="Insufficient acoustic energy"))
                continue
            scores = self.predict(samples)
            if (
                set(scores) != set(LABELS)
                or any(not math.isfinite(p) or not 0 <= p <= 1 for p in scores.values())
                or not math.isclose(sum(scores.values()), 1, abs_tol=1e-5)
            ):
                raise ValueError("Invalid probability distribution")
            ranked = sorted(scores, key=lambda name: scores[name], reverse=True)
            confidence = scores[ranked[0]]
            # Pilot thresholds, not calibrated against representative calls.
            label = operational_label(scores, self.language)
            unknown = label == "Unknown"
            signals.append(
                EmotionSignal(
                    **common,
                    label=label,
                    probabilities=scores,
                    confidence=confidence,
                    reason="Unvalidated language or uncertain model output" if unknown else None,
                )
            )
        return EmotionResult(status="completed", signals=signals, language=self.language)
