"""Consumed interface of faster-whisper 1.2.1; no runtime replacement."""

from collections.abc import Iterable
from typing import Any, Protocol

from numpy import ndarray

class Word(Protocol):
    start: float
    end: float
    word: str

class Segment(Protocol):
    text: str
    start: float
    end: float
    avg_logprob: float
    no_speech_prob: float
    words: list[Word] | None

class WhisperModel:
    def __init__(
        self,
        model_size_or_path: str,
        device: str = ...,
        compute_type: str = ...,
        cpu_threads: int = ...,
        num_workers: int = ...,
        local_files_only: bool = ...,
    ) -> None: ...
    def transcribe(
        self, audio: str | ndarray[Any, Any], **kwargs: Any
    ) -> tuple[Iterable[Segment], object]: ...
