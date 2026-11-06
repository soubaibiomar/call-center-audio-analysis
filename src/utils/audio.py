from __future__ import annotations

import importlib
import io
import wave
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4

from src.graph.state import AudioProperties

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB
MAX_DURATION_SECONDS = 3600  # 60 minutes
SUPPORTED_FORMATS = {"wav", "mp3", "flac", "m4a"}


class AudioValidationError(Exception):
    pass


@dataclass
class ValidationResult:
    is_valid: bool
    error: str | None = None


def detect_audio_format(data: bytes) -> str | None:
    if len(data) < 12:
        return None
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "wav"
    if data[:3] == b"ID3" or (data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        return "mp3"
    if data[:4] == b"fLaC":
        return "flac"
    if data[4:8] == b"ftyp":
        return "m4a"
    return None


def validate_audio_file(data: bytes, filename: str) -> ValidationResult:
    if len(data) == 0:
        return ValidationResult(is_valid=False, error="Empty file")

    if len(data) > MAX_FILE_SIZE_BYTES:
        return ValidationResult(
            is_valid=False,
            error=f"File size {len(data)} bytes exceeds maximum {MAX_FILE_SIZE_BYTES} bytes",
        )

    fmt = detect_audio_format(data)
    if fmt is None or fmt not in SUPPORTED_FORMATS:
        return ValidationResult(
            is_valid=False,
            error=f"Unsupported audio format for file '{filename}'. Supported: {SUPPORTED_FORMATS}",
        )

    if fmt == "wav" and int.from_bytes(data[4:8], "little") + 8 > len(data):
        return ValidationResult(is_valid=False, error="Truncated WAV container")

    try:
        properties = extract_audio_properties(data, fmt)
    except AudioValidationError:
        return ValidationResult(is_valid=False, error="Invalid or corrupt audio container")
    if properties.duration_seconds <= 0 or properties.sample_rate <= 0 or properties.channels <= 0:
        return ValidationResult(is_valid=False, error="Invalid or empty audio stream")
    if properties.duration_seconds > MAX_DURATION_SECONDS:
        return ValidationResult(is_valid=False, error="Audio duration exceeds maximum")

    return ValidationResult(is_valid=True)


def extract_audio_properties(data: bytes, fmt: str) -> AudioProperties:
    try:
        if fmt == "wav":
            if len(data) < 12 or int.from_bytes(data[4:8], "little") + 8 > len(data):
                raise AudioValidationError("Truncated WAV container")
            buf = io.BytesIO(data)
            try:
                with wave.open(buf, "rb") as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    channels = wf.getnchannels()
                    remaining = frames
                    frame_bytes = channels * wf.getsampwidth()
                    while remaining:
                        count = min(remaining, 65536)
                        if len(wf.readframes(count)) != count * frame_bytes:
                            raise AudioValidationError("Truncated WAV audio data")
                        remaining -= count
                    duration = frames / rate
            except wave.Error:
                # The stdlib WAV reader does not support IEEE float WAV.
                sf = importlib.import_module("soundfile")
                info = sf.info(io.BytesIO(data))
                rate, channels, duration = info.samplerate, info.channels, info.duration
            return AudioProperties(
                duration_seconds=round(duration, 2),
                sample_rate=rate,
                channels=channels,
                format=fmt,
                file_size_bytes=len(data),
            )
        # For non-wav formats, use mutagen to extract real properties.
        buf = io.BytesIO(data)
        mutagen_classes: dict[str, Callable[[io.BytesIO], Any]] = {
            "mp3": MP3,
            "flac": FLAC,
            "m4a": MP4,
        }
        parser_cls = mutagen_classes.get(fmt)
        audio = parser_cls(buf) if parser_cls else None
        if audio is not None and audio.info is not None:
            return AudioProperties(
                duration_seconds=round(audio.info.length, 2),
                sample_rate=getattr(audio.info, "sample_rate", 0),
                channels=getattr(audio.info, "channels", 0),
                format=fmt,
                file_size_bytes=len(data),
            )
        # Fallback if mutagen can't parse
        return AudioProperties(
            duration_seconds=0.0,
            sample_rate=0,
            channels=0,
            format=fmt,
            file_size_bytes=len(data),
        )
    except Exception as e:
        raise AudioValidationError(f"Failed to extract audio properties: {e}") from e
