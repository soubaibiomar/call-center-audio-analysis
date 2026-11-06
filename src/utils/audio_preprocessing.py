"""Bounded, local audio decoding and sample-accurate speech chunk coordinates.

This optional path never changes the original recording or the default ASR path.
"""

from __future__ import annotations

import importlib
import io
import math
from collections.abc import Iterator
from dataclasses import dataclass

import av
import numpy as np
from numpy.typing import NDArray

from src.utils.audio import (
    MAX_DURATION_SECONDS,
    AudioValidationError,
    detect_audio_format,
    extract_audio_properties,
    validate_audio_file,
)

SAMPLE_RATE = 16000
# The optional in-memory path is intentionally smaller than the intake limit.
MAX_PREPROCESS_SECONDS = 600


@dataclass(frozen=True)
class PreparedAudio:
    samples: NDArray[np.float32]  # channels, samples; original channel order
    sample_rate: int
    original_channels: int
    source_format: str
    core_start: int = 0
    core_end: int | None = None


@dataclass(frozen=True)
class AudioChunk:
    start_sample: int
    end_sample: int
    sample_rate: int = SAMPLE_RATE
    channel: int | None = None
    core_start: int | None = None
    core_end: int | None = None

    @property
    def start_seconds(self) -> float:
        return self.start_sample / self.sample_rate

    @property
    def end_seconds(self) -> float:
        return self.end_sample / self.sample_rate

    def absolute_seconds(self, relative_seconds: float) -> float:
        if (
            not math.isfinite(relative_seconds)
            or not 0 <= relative_seconds <= (self.end_sample - self.start_sample) / self.sample_rate
        ):
            raise ValueError("Timestamp is outside chunk")
        return self.start_seconds + relative_seconds


def decode_resample(data: bytes, filename: str) -> PreparedAudio:
    """Decode using FFmpeg libraries via PyAV, preserving mono/stereo order."""
    validation = validate_audio_file(data, filename)
    if not validation.is_valid:
        raise AudioValidationError(validation.error or "Invalid audio")
    fmt = detect_audio_format(data)
    if fmt is None:
        raise AudioValidationError("Unsupported audio format")
    container_format = {"wav": "wav", "mp3": "mp3", "flac": "flac", "m4a": "mov"}[fmt]
    pieces: list[NDArray[np.float32]] = []
    total = 0
    limit = SAMPLE_RATE * MAX_PREPROCESS_SECONDS
    try:
        with av.open(io.BytesIO(data), mode="r", format=container_format) as container:
            if len(container.streams.audio) != 1:
                raise AudioValidationError("Exactly one audio stream is required")
            stream = container.streams.audio[0]
            channels = stream.codec_context.channels
            if channels not in (1, 2):
                raise AudioValidationError("Only mono or stereo audio is supported")
            resampler = av.AudioResampler(
                format="fltp", layout="mono" if channels == 1 else "stereo", rate=SAMPLE_RATE
            )
            for frame in container.decode(stream):
                for converted in resampler.resample(frame):
                    total += converted.samples
                    if total > limit:
                        raise AudioValidationError("Audio exceeds preprocessing duration limit")
                    pieces.append(converted.to_ndarray().astype(np.float32, copy=False))
            for converted in resampler.resample(None):
                total += converted.samples
                if total > limit:
                    raise AudioValidationError("Audio exceeds preprocessing duration limit")
                pieces.append(converted.to_ndarray().astype(np.float32, copy=False))
    except AudioValidationError:
        raise
    except (av.FFmpegError, ValueError, OSError, EOFError) as exc:
        raise AudioValidationError("Audio decoding failed") from exc
    if not pieces:
        raise AudioValidationError("Audio decoder produced no samples")
    # Codec delay and rounded metadata may differ slightly from decoded length.
    # Reject materially short output, which can indicate a truncated stream.
    advertised = extract_audio_properties(data, fmt).duration_seconds
    tolerance = max(0.2, advertised * 0.02)
    if total / SAMPLE_RATE < advertised - tolerance:
        raise AudioValidationError("Decoded audio is shorter than its declared duration")
    samples = np.concatenate(pieces, axis=1).astype(np.float32, copy=False)
    if not np.isfinite(samples).all():
        raise AudioValidationError("Audio contains non-finite samples")
    return PreparedAudio(samples, SAMPLE_RATE, channels, fmt)


def iter_resampled_windows(
    data: bytes, filename: str, *, window_seconds: int = 60
) -> Iterator[tuple[int, PreparedAudio]]:
    """Resample a long input into bounded windows with absolute sample offsets."""
    if window_seconds < 1 or window_seconds > MAX_PREPROCESS_SECONDS:
        raise ValueError("Invalid audio window duration")
    validation = validate_audio_file(data, filename)
    if not validation.is_valid:
        raise AudioValidationError(validation.error or "Invalid audio")
    fmt = detect_audio_format(data)
    if fmt is None:
        raise AudioValidationError("Unsupported audio format")
    container_format = {"wav": "wav", "mp3": "mp3", "flac": "flac", "m4a": "mov"}[fmt]
    window_size = SAMPLE_RATE * window_seconds
    total = emitted = 0
    pending: list[NDArray[np.float32]] = []
    pending_samples = 0
    try:
        with av.open(io.BytesIO(data), mode="r", format=container_format) as container:
            if len(container.streams.audio) != 1:
                raise AudioValidationError("Exactly one audio stream is required")
            stream = container.streams.audio[0]
            channels = stream.codec_context.channels
            if channels not in (1, 2):
                raise AudioValidationError("Only mono or stereo audio is supported")
            resampler = av.AudioResampler(
                format="fltp", layout="mono" if channels == 1 else "stereo", rate=SAMPLE_RATE
            )

            def converted_frames() -> Iterator[av.AudioFrame]:
                for frame in container.decode(stream):
                    yield from resampler.resample(frame)
                yield from resampler.resample(None)

            for frame in converted_frames():
                samples = frame.to_ndarray().astype(np.float32, copy=False)
                if not np.isfinite(samples).all():
                    raise AudioValidationError("Audio contains non-finite samples")
                total += samples.shape[1]
                if total > SAMPLE_RATE * MAX_DURATION_SECONDS:
                    raise AudioValidationError("Audio exceeds preprocessing duration limit")
                position = 0
                while position < samples.shape[1]:
                    take = min(window_size - pending_samples, samples.shape[1] - position)
                    pending.append(samples[:, position : position + take])
                    pending_samples += take
                    position += take
                    if pending_samples == window_size:
                        yield (
                            emitted,
                            PreparedAudio(
                                np.concatenate(pending, axis=1), SAMPLE_RATE, channels, fmt
                            ),
                        )
                        emitted += pending_samples
                        pending = []
                        pending_samples = 0
            if pending_samples:
                yield (
                    emitted,
                    PreparedAudio(np.concatenate(pending, axis=1), SAMPLE_RATE, channels, fmt),
                )
    except AudioValidationError:
        raise
    except (av.FFmpegError, ValueError, OSError, EOFError) as exc:
        raise AudioValidationError("Audio decoding failed") from exc
    if total == 0:
        raise AudioValidationError("Audio decoder produced no samples")
    advertised = extract_audio_properties(data, fmt).duration_seconds
    if total / SAMPLE_RATE < advertised - max(0.2, advertised * 0.02):
        raise AudioValidationError("Decoded audio is shorter than its declared duration")


def contextual_windows(
    windows: Iterator[tuple[int, PreparedAudio]], *, context_samples: int = SAMPLE_RATE
) -> Iterator[tuple[int, PreparedAudio]]:
    """Add adjacent audio context while retaining disjoint timestamp ownership."""
    if context_samples < 0:
        raise ValueError("Invalid context size")
    previous_tail = None
    current = next(windows, None)
    while current is not None:
        following = next(windows, None)
        offset, audio = current
        parts = []
        prefix = 0
        if previous_tail is not None:
            parts.append(previous_tail)
            prefix = previous_tail.shape[1]
        parts.append(audio.samples)
        if following is not None:
            if following[0] != offset + audio.samples.shape[1]:
                raise AudioValidationError("Audio windows are not contiguous")
            parts.append(following[1].samples[:, :context_samples])
        yield (
            offset - prefix,
            PreparedAudio(
                np.concatenate(parts, axis=1),
                audio.sample_rate,
                audio.original_channels,
                audio.source_format,
                prefix,
                prefix + audio.samples.shape[1],
            ),
        )
        previous_tail = audio.samples[:, -context_samples:].copy() if context_samples else None
        current = following


def has_severe_phase_cancellation(data: bytes, filename: str) -> bool:
    """Detect severe cancellation in any audible one-second stereo window."""
    detected = False
    for _, audio in iter_resampled_windows(data, filename, window_seconds=1):
        if audio.original_channels != 2:
            return False
        left, right = audio.samples
        left64, right64 = left.astype(np.float64), right.astype(np.float64)
        channel_energy = float(np.dot(left64, left64) + np.dot(right64, right64))
        mixed = (left64 + right64) * 0.5
        mixed_energy = float(np.dot(mixed, mixed))
        if channel_energy > len(left64) * 1e-8 and mixed_energy / channel_energy < 0.005:
            detected = True
    return detected


def speech_chunks(audio: PreparedAudio, *, max_chunk_seconds: float = 30.0) -> list[AudioChunk]:
    """Run VAD separately on distinct channels without phase-cancelling speech."""
    vad = importlib.import_module("faster_whisper.vad")

    if audio.sample_rate != SAMPLE_RATE or not math.isfinite(max_chunk_seconds):
        raise ValueError("Invalid sample rate or chunk duration")
    maximum = round(max_chunk_seconds * SAMPLE_RATE)
    if maximum < 1:
        raise ValueError("Chunk duration must be positive")
    chunks = []
    # Identical or exact inverse channels contain the same signal; process once.
    duplicate = audio.samples.shape[0] == 2 and (
        np.array_equal(audio.samples[0], audio.samples[1])
        or np.array_equal(audio.samples[0], -audio.samples[1])
    )
    for channel in range(1 if duplicate else audio.samples.shape[0]):
        samples = audio.samples[channel]
        spans = vad.get_speech_timestamps(samples, vad.VadOptions(), sampling_rate=SAMPLE_RATE)
        for span in spans:
            start, end = int(span["start"]), int(span["end"])
            if not 0 <= start < end <= samples.size:
                raise AudioValidationError("VAD returned an invalid speech interval")
            while start < end:
                stop = min(start + maximum, end)
                core_start = max(start, audio.core_start)
                core_end = min(stop, audio.core_end if audio.core_end is not None else samples.size)
                if core_start < core_end:
                    # Keep adjacent speech around hard chunk boundaries; emitted
                    # words are owned only by the original, disjoint interval.
                    left = max(int(span["start"]), start - SAMPLE_RATE)
                    right = min(int(span["end"]), stop + SAMPLE_RATE)
                    chunks.append(
                        AudioChunk(
                            left, right, channel=channel, core_start=core_start, core_end=core_end
                        )
                    )
                start = stop
    return sorted(chunks, key=lambda chunk: (chunk.start_sample, chunk.channel or 0))
