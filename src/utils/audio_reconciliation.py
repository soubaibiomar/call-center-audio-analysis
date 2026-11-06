"""Assign overlapping ASR context words to one original sample interval."""

from types import SimpleNamespace
from typing import Any

from src.utils.audio_preprocessing import AudioChunk


def owned_segment(segment: Any, chunk: AudioChunk) -> Any | None:
    """Retain words whose midpoint belongs to the core, preserving original text."""
    if chunk.core_start is None or chunk.core_end is None:
        return segment
    left = (chunk.core_start - chunk.start_sample) / chunk.sample_rate
    right = (chunk.core_end - chunk.start_sample) / chunk.sample_rate
    words = getattr(segment, "words", None)
    if words is None:
        if left > 0 or chunk.core_end < chunk.end_sample:
            raise ValueError("Word timestamps required for overlapping chunk reconciliation")
        return segment
    retained = [word for word in words if left <= (word.start + word.end) / 2 < right]
    if not retained:
        return None
    return SimpleNamespace(
        text="".join(word.word for word in retained),
        start=retained[0].start,
        end=retained[-1].end,
        avg_logprob=segment.avg_logprob,
        no_speech_prob=segment.no_speech_prob,
        words=retained,
    )
