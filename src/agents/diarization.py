"""Local neural speaker turns and conservative transcription alignment."""

from __future__ import annotations

import importlib
import math
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

Role = Literal["Agent", "Customer", "Unknown"]


@dataclass(frozen=True)
class SpeakerTurn:
    start: float
    end: float
    speaker_id: str
    channel: int | None = None

    def __post_init__(self) -> None:
        if not math.isfinite(self.start) or not math.isfinite(self.end):
            raise ValueError("Turn timestamps must be finite")
        if self.start < 0 or self.end <= self.start or not self.speaker_id:
            raise ValueError("Invalid speaker turn")
        if self.channel is not None and self.channel < 0:
            raise ValueError("Invalid channel")


@dataclass(frozen=True)
class Attribution:
    speaker_id: str | None
    role: Role
    overlap: bool


def align_turn(
    start: float,
    end: float,
    turns: list[SpeakerTurn],
    channel_roles: dict[int, Role] | None = None,
) -> Attribution:
    """Choose a uniquely dominant speaker by overlap; ties remain unknown."""
    if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start:
        return Attribution(None, "Unknown", False)
    intervals: dict[str, list[tuple[float, float]]] = {}
    channels: dict[str, set[int | None]] = {}
    for turn in turns:
        left, right = max(start, turn.start), min(end, turn.end)
        if right > left:
            intervals.setdefault(turn.speaker_id, []).append((left, right))
            channels.setdefault(turn.speaker_id, set()).add(turn.channel)
    if not intervals:
        return Attribution(None, "Unknown", False)
    overlaps: dict[str, float] = {}
    for speaker, spans in intervals.items():
        merged: list[tuple[float, float]] = []
        for left, right in sorted(spans):
            if merged and left <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(right, merged[-1][1]))
            else:
                merged.append((left, right))
        intervals[speaker] = merged
        overlaps[speaker] = sum(right - left for left, right in merged)
    ranked = sorted(overlaps.items(), key=lambda item: (-item[1], item[0]))
    speakers = list(intervals)
    overlap = any(
        max(a, c) < min(b, d)
        for index, speaker in enumerate(speakers)
        for other in speakers[index + 1 :]
        for a, b in intervals[speaker]
        for c, d in intervals[other]
    )
    if len(ranked) > 1 and math.isclose(ranked[0][1], ranked[1][1], abs_tol=1e-9):
        return Attribution(None, "Unknown", overlap)
    speaker = ranked[0][0]
    known_channels = channels[speaker]
    role: Role = "Unknown"
    if channel_roles and len(known_channels) == 1:
        channel = next(iter(known_channels))
        if channel is not None:
            role = channel_roles.get(channel, "Unknown")
    return Attribution(speaker, role, overlap)


class CommunityDiarizer:
    """Adapt a locally loaded Community-1 pipeline without identifying people."""

    def __init__(self, pipeline: Any) -> None:
        self.pipeline = pipeline
        self._lock = threading.Lock()

    def turns(self, audio_path: str) -> list[SpeakerTurn]:
        with self._lock:
            result = self.pipeline(audio_path)
        annotation = result.speaker_diarization
        return [
            SpeakerTurn(float(turn.start), float(turn.end), str(speaker))
            for turn, _track, speaker in annotation.itertracks(yield_label=True)
        ]

    def channel_turns(self, audio_path: str) -> list[SpeakerTurn]:
        """Diarize each channel separately when trusted channel roles are supplied.

        Labels are scoped to a channel; they do not identify a real person.
        """
        soundfile = importlib.import_module("soundfile")
        torch = importlib.import_module("torch")
        samples, sample_rate = soundfile.read(audio_path, dtype="float32", always_2d=True)
        if samples.shape[1] != 2:
            raise ValueError("Channel role attribution requires exactly two audio channels")
        turns = []
        for channel in range(2):
            waveform = torch.from_numpy(samples[:, channel].copy()).unsqueeze(0)
            with self._lock:
                result = self.pipeline({"waveform": waveform, "sample_rate": sample_rate})
            for turn, _track, speaker in result.speaker_diarization.itertracks(yield_label=True):
                turns.append(
                    SpeakerTurn(
                        float(turn.start), float(turn.end), f"ch{channel}:{speaker}", channel
                    )
                )
        return turns


@lru_cache(maxsize=1)
def load_community(model_path: str) -> CommunityDiarizer:
    """Load only an explicitly provisioned local pipeline; never request a repo ID."""
    path = Path(model_path)
    if not path.is_absolute() or not path.is_dir():
        raise ValueError("A local Community-1 model directory is required")
    try:
        module = importlib.import_module("pyannote.audio")
    except ImportError:
        raise RuntimeError("Optional pyannote.audio runtime is not installed") from None
    pipeline = module.Pipeline.from_pretrained(str(path))
    if pipeline is None:
        raise RuntimeError("Community-1 model could not be loaded")
    return CommunityDiarizer(pipeline)
