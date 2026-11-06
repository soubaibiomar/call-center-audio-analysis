"""Separate, versioned human corrections and explicit source/permission attestations."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints, model_validator

from services.reviews.contracts import Strict
from src.graph.state import QAScoreResult, TranscriptionResult
from src.services.model_runs import ModelRun

Reason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=2000)]
Digest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class CallEnrollment(Strict):
    partition: Literal["train", "evaluation"]
    audio_sha256: Digest
    conversation_key: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)
    ]
    speaker_keys: list[
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]
    ] = Field(min_length=1, max_length=20)
    consent_to_train: bool = False
    consent_evidence: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)
    ]
    source_attestation: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=10, max_length=500)
    ]
    source_attested: Literal[True]


class SegmentCorrection(Strict):
    segment_index: int = Field(ge=0)
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
    speaker_role: Literal["Agent", "Customer", "Unknown"]
    uncertain: bool


class QAOverride(Strict):
    score: float = Field(ge=1, le=5, allow_inf_nan=False)
    rationale: Reason
    audio_start: float = Field(ge=0, allow_inf_nan=False)
    audio_end: float = Field(gt=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def ordered(self) -> "QAOverride":
        if self.audio_end <= self.audio_start:
            raise ValueError("Supporting audio must have a positive duration")
        return self


class CorrectionPayload(Strict):
    segments: list[SegmentCorrection] = Field(min_length=1, max_length=500)
    qa_override: QAOverride | None = None


class CorrectionInput(CorrectionPayload):
    expected_revision: int = Field(ge=1)


class DecisionInput(Strict):
    action: Literal["submit", "approve", "reject"]
    expected_revision: int = Field(ge=1)
    rationale: Reason
    listened_to_audio: Literal[True]
    observed_audio_sha256: Digest
    observed_duration_seconds: float = Field(gt=0, le=1800, allow_inf_nan=False)


class ReviewSnapshot(Strict):
    transcription: TranscriptionResult
    qa_scores: QAScoreResult
    duration_seconds: float = Field(gt=0, le=1800, allow_inf_nan=False)
    model_runs: list[ModelRun]


class CallReviewView(Strict):
    id: UUID
    call_id: UUID
    original: ReviewSnapshot
    original_sha256: Digest
    source_audio_sha256: Digest
    source_attestation: str
    partition: Literal["train", "evaluation"]
    consent_to_train: bool
    revision: int
    state: Literal["draft", "submitted", "approved", "rejected"]
    payload: CorrectionPayload
    author_id: str | None
    submitter_id: str | None
    approver_id: str | None
    eligible_for_training: bool
    updated_at: datetime


class ReviewEventView(Strict):
    id: UUID
    actor_id: str
    action: str
    revision: int
    payload_sha256: Digest
    created_at: datetime


class AnnotationExportItem(Strict):
    review_id: UUID
    call_id: UUID
    revision: int
    source_audio_sha256: Digest
    original_sha256: Digest
    source_expires_at: datetime
    author_id: str
    approver_id: str
    payload: CorrectionPayload


class AnnotationDataset(Strict):
    schema_version: Literal["call-annotation-v1"] = "call-annotation-v1"
    items: list[AnnotationExportItem]
    approved_segments: int
    candidate_limit: int = 100
    truncated: bool
    fingerprint: Digest
