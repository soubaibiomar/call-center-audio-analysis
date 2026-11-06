"""Conservative, typed evidence contracts for graph analysis."""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from src.graph.state import TranscriptionResult


class Evidence(BaseModel):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)
    text: str


class AnalysisReview(BaseModel):
    intent: Literal["billing", "technical_support", "cancellation", "unknown"] = "unknown"
    resolution: Literal["resolved", "unresolved", "escalated", "unknown"] = "unknown"
    intent_evidence: list[int] = Field(default_factory=list)
    resolution_evidence: list[int] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    needs_human_review: bool = False
    reasons: list[str] = Field(default_factory=list)


def collect_review(transcript: TranscriptionResult) -> AnalysisReview:
    """Collect only valid redacted source segments; never infer unsupported claims."""
    evidence = []
    reasons = []
    for segment in transcript.segments:
        if (
            not math.isfinite(segment.start_time)
            or not math.isfinite(segment.end_time)
            or segment.start_time < 0
            or segment.end_time <= segment.start_time
        ):
            reasons.append("invalid_timestamp")
            continue
        evidence.append(
            Evidence(
                start_seconds=segment.start_time, end_seconds=segment.end_time, text=segment.text
            )
        )
    if transcript.flagged_for_review:
        reasons.append("low_confidence")
    if not evidence:
        reasons.append("missing_evidence")
    return AnalysisReview(evidence=evidence, needs_human_review=bool(reasons), reasons=reasons)


def classify_intent(review: AnalysisReview) -> AnalysisReview:
    matches: dict[str, list[int]] = {}
    patterns = {
        "billing": r"\b(billing|invoice|charged|refund)\b",
        "technical_support": r"\b(technical support|connection problem|cannot log in)\b",
        "cancellation": r"\b(cancel my|cancel the|close my account)\b",
    }
    for intent, pattern in patterns.items():
        indices = [
            i for i, item in enumerate(review.evidence) if re.search(pattern, item.text, re.I)
        ]
        if indices:
            matches[intent] = indices
    result = review.model_copy(deep=True)
    if len(matches) == 1:
        intent, indices = next(iter(matches.items()))
        result = AnalysisReview.model_validate(
            {**result.model_dump(), "intent": intent, "intent_evidence": indices}
        )
    return result


def classify_resolution(review: AnalysisReview) -> AnalysisReview:
    matches: dict[str, list[int]] = {}
    patterns = {
        "resolved": r"\b(issue is resolved|problem is fixed|that solved my problem)\b",
        "unresolved": r"\b(still not working|not resolved|problem remains)\b",
        "escalated": r"\b(transferring you|escalated to|transfer you to)\b",
    }
    for label, pattern in patterns.items():
        indices = [
            i for i, item in enumerate(review.evidence) if re.search(pattern, item.text, re.I)
        ]
        if indices:
            matches[label] = indices
    result = review.model_copy(deep=True)
    if len(matches) == 1:
        label, indices = next(iter(matches.items()))
        result = AnalysisReview.model_validate(
            {**result.model_dump(), "resolution": label, "resolution_evidence": indices}
        )
    return result


def decide_review(
    review: AnalysisReview, summary_resolution: str, critical: bool
) -> AnalysisReview:
    result = review.model_copy(deep=True)
    if result.resolution == "unknown" or result.resolution != summary_resolution:
        result.reasons.append("unsupported_resolution")
    if critical:
        result.reasons.append("critical_compliance")
    result.reasons = sorted(set(result.reasons))
    result.needs_human_review = bool(result.reasons)
    return result
