"""Bounded offline CPU inference adapter; no downloads, cache writes or hosted providers."""

import re
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

import numpy as np
from faster_whisper import WhisperModel

from ml.asr.incremental import Word
from services.streaming.contracts import LiveTranscriptSpan
from src.security.pii_redactor import redact_pii


class ASRPort(Protocol):
    def transcribe(self, pcm: bytes) -> list[LiveTranscriptSpan]: ...


@runtime_checkable
class WordASRPort(Protocol):
    def transcribe_words(self, pcm: bytes) -> list[Word]: ...


def recognize_words(asr: ASRPort, pcm: bytes) -> tuple[list[Word], Literal["word", "interpolated"]]:
    if isinstance(asr, WordASRPort):
        return asr.transcribe_words(pcm), "word"
    # Compatibility for injected segment-only adapters; their timing is explicitly estimated.
    result: list[Word] = []
    for span in asr.transcribe(pcm):
        tokens = re.findall(r"\s*\S+", span.text)
        if not tokens or span.end_seconds <= span.start_seconds:
            continue
        step = (span.end_seconds - span.start_seconds) / len(tokens)
        result.extend(
            Word(span.start_seconds + i * step, span.start_seconds + (i + 1) * step, token)
            for i, token in enumerate(tokens)
        )
    return result, "interpolated"


class LocalWhisper:
    def __init__(self, path: str) -> None:
        self.path = Path(path).resolve()
        if not self.path.is_dir() or not (self.path / "model.bin").is_file():
            raise ValueError("LIVE_ASR_MODEL_PATH must point to an existing local CT2 model")
        self.model: WhisperModel | None = None

    def transcribe(self, pcm: bytes) -> list[LiveTranscriptSpan]:
        if not pcm or len(pcm) > 256000 or len(pcm) % 2:
            raise ValueError("Expected up to eight seconds of 16 kHz mono PCM16LE")
        if self.model is None:
            self.model = WhisperModel(
                str(self.path),
                device="cpu",
                compute_type="int8",
                cpu_threads=4,
                num_workers=1,
                local_files_only=True,
            )
        audio = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
        spans, _ = self.model.transcribe(audio, beam_size=1, vad_filter=False)
        duration = len(audio) / 16000
        result: list[LiveTranscriptSpan] = []
        for span in spans:
            start, end = max(0.0, span.start), min(duration, span.end)
            if end > start and len(result) < 100:
                result.append(
                    LiveTranscriptSpan(
                        start_seconds=start,
                        end_seconds=end,
                        text=redact_pii(span.text.strip()).redacted_text[:4000],
                    )
                )
        return result

    def transcribe_words(self, pcm: bytes) -> list[Word]:
        if not pcm or len(pcm) > 256000 or len(pcm) % 2:
            raise ValueError("Expected up to eight seconds of PCM16LE")
        if self.model is None:
            self.model = WhisperModel(
                str(self.path),
                device="cpu",
                compute_type="int8",
                cpu_threads=4,
                num_workers=1,
                local_files_only=True,
            )
        audio = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
        spans, _ = self.model.transcribe(
            audio,
            beam_size=1,
            vad_filter=False,
            word_timestamps=True,
            condition_on_previous_text=False,
        )
        duration = len(audio) / 16000
        result: list[Word] = []
        for span in spans:
            for word in span.words or []:
                start, end = max(0.0, word.start), min(duration, word.end)
                if end > start and len(result) < 500:
                    result.append(Word(start, end, word.word))
        return result
