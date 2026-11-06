"""Reviewer input is separate from immutable machine inference and training permission."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from ml.emotion.contracts import EmotionLabel, EmotionSignal


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Enrollment(Strict):
    segment_index: int = Field(ge=0)
    partition: Literal["train", "evaluation"]
    audio_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    conversation_key: str = Field(min_length=1, max_length=128)
    speaker_keys: list[Annotated[str, StringConstraints(min_length=1, max_length=128)]] = Field(
        min_length=1, max_length=20
    )
    consent_to_train: bool = False
    consent_evidence: str = Field(min_length=1, max_length=300)


class VoteInput(Strict):
    label: EmotionLabel
    notes: str = Field(default="", max_length=2000)
    confirmed: Literal[True]
    expected_revision: int = Field(ge=1)


class Adjudication(VoteInput):
    notes: str = Field(min_length=10, max_length=2000)


class ConsentInput(Strict):
    consent_to_train: bool
    consent_evidence: str = Field(min_length=1, max_length=300)
    expected_revision: int = Field(ge=1)


class VoteView(BaseModel):
    reviewer_id: str
    label: str
    notes: str
    version: int


ReviewStatus = Literal["pending", "uncertain", "disagreement", "verified", "adjudicated"]


class ItemView(BaseModel):
    id: UUID
    call_id: UUID
    source_audio_sha256: str
    prediction: EmotionSignal
    partition: str
    consent_to_train: bool
    revision: int
    status: Literal["pending", "uncertain", "disagreement", "verified", "adjudicated"]
    corrected_label: EmotionLabel | None
    votes: list[VoteView]
    adjudication_note: str | None
    eligible_for_training: bool
