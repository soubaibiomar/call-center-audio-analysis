from __future__ import annotations

import hashlib
import importlib
import logging
import os
import re
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

from faster_whisper import WhisperModel
from sqlalchemy.engine import Engine

from src.agents.diarization import Role, align_turn, load_community
from src.graph.state import (
    IntakeResult,
    TranscriptionResult,
    TranscriptionSegment,
)
from src.utils.audio_preprocessing import (
    MAX_PREPROCESS_SECONDS,
    contextual_windows,
    decode_resample,
    has_severe_phase_cancellation,
    iter_resampled_windows,
    speech_chunks,
)
from src.utils.audio_reconciliation import owned_segment

if TYPE_CHECKING:
    from faster_whisper import Segment

logger = logging.getLogger(__name__)

# Module-level singleton — load model ONCE
_model: WhisperModel | None = None
_model_size: str | None = None


def _detect_device() -> tuple[str, str]:
    """Auto-detect best available device and compute type."""
    forced = os.getenv("WHISPER_DEVICE")
    if forced in {"cpu", "cuda"}:
        return forced, "int8" if forced == "cpu" else "float16"
    try:
        torch = importlib.import_module("torch")

        if torch.cuda.is_available():
            return "cuda", "float16"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            # MPS doesn't work with CTranslate2, fall back to CPU
            return "cpu", "int8"
    except ImportError:
        pass
    return "cpu", "int8"


def _get_whisper_model(model_size: str = "base") -> WhisperModel:
    global _model, _model_size
    if _model is None or _model_size != model_size:
        device, compute_type = _detect_device()
        logger.info(f"Loading Whisper '{model_size}' on {device} ({compute_type})")
        _model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )
        _model_size = model_size
    return _model


# Patterns that strongly indicate agent speech (first speaker)
_AGENT_PATTERNS = re.compile(
    r"(?i)(thank you for calling|how (?:can|may) I (?:help|assist)|"
    r"my name is|this call (?:may|will) be|for quality (?:and|assurance)|"
    r"is there anything else|have a (?:great|good|wonderful) day)"
)
# Patterns that strongly indicate customer speech
_CUSTOMER_PATTERNS = re.compile(
    r"(?i)(I(?:'m| am) calling (?:about|because|to)|I (?:need|want|have a)|"
    r"my account|my order|my bill|can you help|I was charged)"
)


class SpeakerSegment(TypedDict):
    text: str
    start: float
    end: float
    confidence: float


class SpeakerDiarizer:
    """Heuristic speaker detection using gaps, questions, and content patterns."""

    def assign_speakers(self, segments: list[SpeakerSegment]) -> list[str]:
        labels = ["Agent", "Customer"]
        assignments: list[str] = []
        current = 0  # 0 = Agent, 1 = Customer

        for i, seg in enumerate(segments):
            text = seg.get("text", "").strip()

            if i == 0:
                # First segment: check if it sounds like an agent greeting
                if _AGENT_PATTERNS.search(text):
                    current = 0
                elif _CUSTOMER_PATTERNS.search(text):
                    current = 1
                # else default to Agent (call center convention)
            else:
                gap = seg["start"] - segments[i - 1]["end"]
                prev_text = segments[i - 1].get("text", "").strip()

                # Content-based: strong signal overrides gap heuristic
                if _AGENT_PATTERNS.search(text) and current != 0:
                    current = 0
                elif _CUSTOMER_PATTERNS.search(text) and current != 1:
                    current = 1
                # Gap-based: speaker likely changed
                elif gap > 1.2:
                    current = 1 - current
                # Question followed by answer = speaker change
                elif prev_text.endswith("?"):
                    current = 1 - current
                # Short affirmation after long segment = different speaker
                elif len(text.split()) <= 3 and len(prev_text.split()) > 10:
                    current = 1 - current

            assignments.append(labels[current])
        return assignments


_diarizer = SpeakerDiarizer()


def _get_diarizer() -> SpeakerDiarizer:
    return _diarizer


def _compute_audio_hash(audio_path: str) -> str:
    """Compute SHA-256 hash of an audio file for caching."""
    h = hashlib.sha256()
    with open(audio_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _check_cache(audio_hash: str, engine: Engine | None) -> TranscriptionResult | None:
    """Check if a transcription result exists in cache."""
    if engine is None:
        return None
    try:
        from src.database.connection import get_session
        from src.database.models import TranscriptionCache

        session = get_session(engine)
        try:
            cached = session.query(TranscriptionCache).filter_by(audio_hash=audio_hash).first()
            if cached:
                logger.info(f"Cache hit for audio hash {audio_hash[:12]}...")
                return TranscriptionResult.model_validate_json(cached.transcription_json)
            return None
        finally:
            session.close()
    except Exception:
        return None


def _save_cache(audio_hash: str, result: TranscriptionResult, engine: Engine | None) -> None:
    """Save transcription result to cache."""
    if engine is None:
        return
    try:
        from datetime import datetime

        from src.database.connection import get_session
        from src.database.models import TranscriptionCache

        session = get_session(engine)
        try:
            entry = TranscriptionCache(
                audio_hash=audio_hash,
                transcription_json=result.model_dump_json(),
                created_at=datetime.now(),
            )
            session.add(entry)
            session.commit()
        finally:
            session.close()
    except Exception:
        pass  # Cache save failure is non-critical


# Common Whisper artifacts to clean
_ARTIFACT_PATTERNS = [
    re.compile(r"\[BLANK_AUDIO\]", re.IGNORECASE),
    re.compile(r"\(blank audio\)", re.IGNORECASE),
    re.compile(r"\.{4,}"),  # repeated dots (hallucination)
    re.compile(r"(?i)^(thanks for watching|subscribe|like and subscribe).*$"),  # YouTube artifacts
    re.compile(r"(?i)^(music|applause|laughter)\s*$"),  # non-speech tags
]


def _clean_transcript_text(text: str) -> str:
    """Remove common Whisper artifacts and normalize whitespace."""
    for pattern in _ARTIFACT_PATTERNS:
        text = pattern.sub("", text)
    # Collapse repeated phrases (e.g., "thank you thank you thank you" → "thank you")
    words = text.split()
    if len(words) >= 6:
        # Check if the same 1-3 word phrase repeats 3+ times
        for phrase_len in range(1, 4):
            if len(words) >= phrase_len * 3:
                phrase = " ".join(words[:phrase_len])
                repeats = 0
                for i in range(0, len(words), phrase_len):
                    if " ".join(words[i : i + phrase_len]) == phrase:
                        repeats += 1
                    else:
                        break
                if repeats >= 3:
                    text = phrase
                    break
    return text.strip()


def run_transcription(
    intake: IntakeResult,
    confidence_threshold: float = 0.3,
    halt_ratio: float = 0.8,
    model_size: str = "base",
    db_engine: Engine | None = None,
    *,
    channel_roles: dict[int, Role] | None = None,
) -> TranscriptionResult:
    backend = os.getenv("DIARIZATION_BACKEND", "heuristic").strip().lower()
    requested_segmentation = os.getenv("AUDIO_PREPROCESS_SEGMENTS")
    segment_mode = requested_segmentation is not None and requested_segmentation.lower() == "true"
    if requested_segmentation is None and intake.audio_properties.channels == 2:
        segment_mode = has_severe_phase_cancellation(
            Path(intake.audio_path).read_bytes(), intake.audio_path
        )
    if backend not in {"heuristic", "pyannote"}:
        raise ValueError("Unsupported diarization backend")
    if channel_roles is not None and (
        backend != "pyannote"
        or set(channel_roles) != {0, 1}
        or set(channel_roles.values()) != {"Agent", "Customer"}
    ):
        raise ValueError("Trusted channel roles require neural mode and one role per channel")
    neural_diarizer = (
        load_community(os.getenv("DIARIZATION_MODEL_PATH", "")) if backend == "pyannote" else None
    )
    # Check cache first
    audio_hash = None
    try:
        audio_hash = _compute_audio_hash(intake.audio_path)
        # Existing cache keys do not include a diarization backend/model revision.
        cached = (
            _check_cache(audio_hash, db_engine)
            if backend == "heuristic" and not segment_mode
            else None
        )
        if cached is not None:
            cached.call_id = intake.call_id
            return cached
    except (FileNotFoundError, OSError):
        pass  # File doesn't exist yet or can't be read — skip cache

    model = _get_whisper_model(model_size)

    # faster-whisper handles resampling and mono conversion internally
    # beam_size=1 (greedy) is ~2x faster than beam_size=5 with minimal quality loss
    # word_timestamps=True improves segment boundaries at negligible speed cost
    if segment_mode:
        data = Path(intake.audio_path).read_bytes()
        if intake.audio_properties.duration_seconds >= MAX_PREPROCESS_SECONDS - 0.01:
            windows = contextual_windows(iter_resampled_windows(data, intake.audio_path))
        else:
            windows = iter([(0, decode_resample(data, intake.audio_path))])

        def segments_with_offsets() -> Iterator[tuple[Segment, float, float]]:
            for offset, prepared in windows:
                for chunk in speech_chunks(prepared):
                    mono = prepared.samples[
                        chunk.channel or 0, chunk.start_sample : chunk.end_sample
                    ]
                    raw, _info = model.transcribe(
                        mono,
                        beam_size=1,
                        language="en",
                        vad_filter=False,
                        word_timestamps=True,
                        condition_on_previous_text=False,
                    )
                    for segment in raw:
                        reconciled = owned_segment(segment, chunk)
                        if reconciled is None:
                            continue
                        segment = reconciled
                        if segment.end < segment.start:
                            raise ValueError("Transcription segment ends before it starts")
                        yield (
                            segment,
                            offset / prepared.sample_rate + chunk.absolute_seconds(segment.start),
                            offset / prepared.sample_rate + chunk.absolute_seconds(segment.end),
                        )

        timed_segments = segments_with_offsets()
    else:
        raw_segments, _info = model.transcribe(
            intake.audio_path,
            beam_size=1,
            language="en",
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
            word_timestamps=True,
            condition_on_previous_text=False,
        )
        timed_segments = ((segment, segment.start, segment.end) for segment in raw_segments)

    # Collect segments with improved confidence and text cleanup
    seg_list: list[SpeakerSegment] = []
    full_text_parts = []
    # Channel-specific streams can overlap; chronological order is required by
    # the legacy gap-based speaker heuristic and downstream transcript display.
    if segment_mode:
        timed_segments = iter(sorted(timed_segments, key=lambda item: (item[1], item[2])))
    for seg, start_time, end_time in timed_segments:
        text = _clean_transcript_text(seg.text.strip())
        if not text:
            continue  # skip empty/artifact segments

        # Better confidence: combine avg_logprob and no_speech_prob
        # avg_logprob ranges ~[-1, 0], no_speech_prob ranges [0, 1]
        logprob_conf = max(0.0, min(1.0, 1.0 + seg.avg_logprob))
        speech_conf = 1.0 - seg.no_speech_prob
        conf = round(logprob_conf * 0.7 + speech_conf * 0.3, 4)

        seg_list.append(
            {
                "text": text,
                "start": start_time,
                "end": end_time,
                "confidence": conf,
            }
        )
        full_text_parts.append(text)

    # Assign speakers
    if backend == "heuristic":
        speakers = _get_diarizer().assign_speakers(seg_list)
        attributions = None
    else:
        if neural_diarizer is None:
            raise RuntimeError("Neural diarization is not available")
        turns = (
            neural_diarizer.channel_turns(intake.audio_path)
            if channel_roles is not None
            else neural_diarizer.turns(intake.audio_path)
        )
        attributions = [align_turn(s["start"], s["end"], turns, channel_roles) for s in seg_list]
        speakers = [a.role for a in attributions]

    # Build typed segments
    segments: list[TranscriptionSegment] = []
    for i, s in enumerate(seg_list):
        segments.append(
            TranscriptionSegment(
                text=s["text"],
                start_time=s["start"],
                end_time=s["end"],
                speaker=(speakers[i] if i < len(speakers) else "Unknown"),
                confidence=s["confidence"],
                low_confidence=s["confidence"] < confidence_threshold,
                speaker_id=attributions[i].speaker_id if attributions else None,
                speaker_role=attributions[i].role if attributions else None,
                speaker_overlap=attributions[i].overlap if attributions else False,
            )
        )

    low_count = sum(1 for s in segments if s.low_confidence)
    total = len(segments) if segments else 1
    overall_conf = sum(s.confidence for s in segments) / total if segments else 0.0
    flagged = (low_count / total) > halt_ratio

    result = TranscriptionResult(
        call_id=intake.call_id,
        full_text=" ".join(full_text_parts),
        segments=segments,
        overall_confidence=round(overall_conf, 4),
        flagged_for_review=flagged,
    )

    # Save to cache for future identical audio
    if audio_hash and backend == "heuristic" and not segment_mode:
        _save_cache(audio_hash, result, db_engine)

    return result
