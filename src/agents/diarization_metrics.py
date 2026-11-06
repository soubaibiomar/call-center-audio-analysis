"""Evaluate reviewed diarization turns using an optional pyannote.metrics runtime."""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass

from src.agents.diarization import Role, SpeakerTurn


@dataclass(frozen=True)
class DiarizationMetrics:
    der: float
    reference_speaker_seconds: float
    overlap_reference_seconds: float
    overlap_missed_seconds: float
    overlap_false_alarm_seconds: float
    role_reference_seconds: float
    role_covered_seconds: float
    role_correct_seconds: float

    @property
    def role_accuracy(self) -> float | None:
        return (
            self.role_correct_seconds / self.role_reference_seconds
            if self.role_reference_seconds
            else None
        )

    @property
    def role_coverage(self) -> float | None:
        return (
            self.role_covered_seconds / self.role_reference_seconds
            if self.role_reference_seconds
            else None
        )


def evaluate_turns(
    reference: list[SpeakerTurn],
    hypothesis: list[SpeakerTurn],
    *,
    duration: float,
    reference_roles: dict[str, Role] | None = None,
    hypothesis_roles: dict[str, Role] | None = None,
    collar: float = 0.0,
    skip_overlap: bool = False,
) -> DiarizationMetrics:
    """Score against reference turns; role/overlap durations cover the full region.

    DER respects collar and skip_overlap. Role and overlap diagnostics intentionally
    use the full region and should not be compared to collar-filtered DER counts.
    """
    if not math.isfinite(duration) or duration <= 0 or not math.isfinite(collar) or collar < 0:
        raise ValueError("Invalid scoring region or collar")
    if not reference or any(turn.end > duration for turn in reference + hypothesis):
        raise ValueError("Reference required and all turns must fit the scoring region")
    try:
        core = importlib.import_module("pyannote.core")
        diarization = importlib.import_module("pyannote.metrics.diarization")
    except ImportError:
        raise RuntimeError("Optional pyannote.metrics runtime is not installed") from None
    annotations = []
    for turns in (reference, hypothesis):
        annotation = core.Annotation()
        for index, turn in enumerate(turns):
            annotation[core.Segment(turn.start, turn.end), index] = turn.speaker_id
        annotations.append(annotation)
    metric = diarization.DiarizationErrorRate(collar=collar, skip_overlap=skip_overlap)
    region = core.Timeline(segments=[core.Segment(0.0, duration)])
    details = metric(annotations[0], annotations[1], uem=region, detailed=True)
    reference_time = float(details["total"])
    if reference_time <= 0:
        raise ValueError("Scoring region has no reference speech after filtering")
    boundaries = sorted(
        {0.0, duration} | {x for t in reference + hypothesis for x in (t.start, t.end)}
    )
    overlap_ref = overlap_miss = overlap_false = role_ref = role_cover = role_correct = 0.0
    for start, end in zip(boundaries, boundaries[1:]):
        mid = (start + end) / 2
        span = end - start
        actual = {t.speaker_id for t in reference if t.start <= mid < t.end}
        predicted = {t.speaker_id for t in hypothesis if t.start <= mid < t.end}
        if len(actual) >= 2:
            overlap_ref += span
            if len(predicted) < 2:
                overlap_miss += span
        elif len(predicted) >= 2:
            overlap_false += span
        if len(actual) != 1 or reference_roles is None:
            continue
        ref_role = reference_roles.get(next(iter(actual)), "Unknown")
        if ref_role == "Unknown":
            continue
        role_ref += span
        pred_role = (
            (hypothesis_roles or {}).get(next(iter(predicted)), "Unknown")
            if len(predicted) == 1
            else "Unknown"
        )
        if pred_role != "Unknown":
            role_cover += span
            if pred_role == ref_role:
                role_correct += span
    return DiarizationMetrics(
        der=float(details["diarization error rate"]),
        reference_speaker_seconds=reference_time,
        overlap_reference_seconds=overlap_ref,
        overlap_missed_seconds=overlap_miss,
        overlap_false_alarm_seconds=overlap_false,
        role_reference_seconds=role_ref,
        role_covered_seconds=role_cover,
        role_correct_seconds=role_correct,
    )
