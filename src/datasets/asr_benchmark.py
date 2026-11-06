"""Offline ASR comparison primitives; no deployment routing or model downloads."""

from __future__ import annotations

import math
import time
import unicodedata
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class Transcript(BaseModel):
    """Backend-independent output; no fabricated timing or confidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    text: str
    language: str | None = None


class Transcriber(Protocol):
    def transcribe(self, audio: Path) -> Transcript: ...


class WhisperAdapter:
    """Wrap an already loaded faster-whisper model; do not implicitly download."""

    def __init__(self, model: Any) -> None:
        self.model = model

    def transcribe(self, audio: Path) -> Transcript:
        segments, info = self.model.transcribe(str(audio), beam_size=1, language=None)
        return Transcript(
            text=" ".join(segment.text.strip() for segment in segments), language=info.language
        )


class QwenAdapter:
    """Wrap an already loaded Qwen3ASRModel; never initiate loading here."""

    def __init__(self, model: Any) -> None:
        self.model = model

    def transcribe(self, audio: Path) -> Transcript:
        result = self.model.transcribe(audio=str(audio), language=None)
        if len(result) != 1:
            raise ValueError("Expected one transcription")
        return Transcript(text=result[0].text, language=result[0].language or None)


def normalize(text: str) -> str:
    """Fixed NFC/casefold/whitespace policy; punctuation and accents retained."""
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def edit_distance(reference: Sequence[str], hypothesis: Sequence[str]) -> int:
    """Levenshtein distance with a single row of memory."""
    previous = list(range(len(hypothesis) + 1))
    for i, left in enumerate(reference, 1):
        current = [i]
        for j, right in enumerate(hypothesis, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (left != right)))
        previous = current
    return previous[-1]


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    language: str
    audio_seconds: float = Field(gt=0, allow_inf_nan=False)
    latency_seconds: float = Field(ge=0, allow_inf_nan=False)
    word_errors: int = Field(ge=0)
    reference_words: int = Field(gt=0)
    char_errors: int = Field(ge=0)
    reference_chars: int = Field(gt=0)


def observe(
    adapter: Transcriber, audio: Path, reference: str, language: str, duration: float
) -> Observation:
    expected = normalize(reference)
    if not expected:
        raise ValueError("Empty references are excluded")
    start = time.perf_counter()
    transcript = adapter.transcribe(audio)
    elapsed = time.perf_counter() - start
    actual = normalize(transcript.text)
    return Observation(
        language=language,
        audio_seconds=duration,
        latency_seconds=elapsed,
        word_errors=edit_distance(expected.split(), actual.split()),
        reference_words=len(expected.split()),
        char_errors=edit_distance(list(expected), list(actual)),
        reference_chars=len(expected),
    )


def summarize(observations: Sequence[Observation], attempted: int) -> dict[str, object]:
    if attempted < len(observations) or attempted < 1:
        raise ValueError("Invalid attempt count")
    if not observations:
        return {"attempted": attempted, "failed": attempted, "failure_rate": 1.0, "metrics": None}
    latency = sorted(o.latency_seconds for o in observations)

    def quantile(q: float) -> float:
        return latency[max(0, math.ceil(q * len(latency)) - 1)]

    languages = {}
    for language in sorted({o.language for o in observations}):
        group = [o for o in observations if o.language == language]
        languages[language] = {
            "count": len(group),
            "wer": sum(o.word_errors for o in group) / sum(o.reference_words for o in group),
            "cer": sum(o.char_errors for o in group) / sum(o.reference_chars for o in group),
        }
    return {
        "attempted": attempted,
        "failed": attempted - len(observations),
        "failure_rate": (attempted - len(observations)) / attempted,
        "metrics": {
            "languages": languages,
            "latency_p50_seconds": quantile(0.50),
            "latency_p95_seconds": quantile(0.95),
            "real_time_factor": sum(o.latency_seconds for o in observations)
            / sum(o.audio_seconds for o in observations),
            "peak_gpu_memory_bytes": None,
        },
    }
