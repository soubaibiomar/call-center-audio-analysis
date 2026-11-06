"""HTTP contracts omit internal file paths and reuse the validated analysis schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ml.emotion.contracts import EmotionResult
from src.graph.state import CallReport, QAScoreResult, SummaryResult, TranscriptionResult
from src.services.model_runs import ModelRun


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: UUID
    retryable: bool


class ErrorResponse(BaseModel):
    error: ErrorBody


class Health(BaseModel):
    status: Literal["ok", "ready"]


class Identity(BaseModel):
    tenant_id: UUID
    user_id: UUID
    role: Literal["agent", "supervisor", "admin"]


class CallItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: str
    processed_at: datetime
    qa_score: float | None = Field(ge=0, le=5)
    language: str | None = None


class CallPage(BaseModel):
    items: list[CallItem]
    total: int = Field(ge=0)
    limit: int
    offset: int


class Dashboard(BaseModel):
    total_calls: int
    completed: int
    failed: int
    flagged_for_review: int
    average_qa_score: float | None
    scope: Literal["owned_calls", "tenant"]


class ActivityDay(BaseModel):
    date: str
    calls: int = Field(ge=0)


class LanguageCount(BaseModel):
    language: str
    calls: int = Field(ge=0)


class Activity(BaseModel):
    days: list[ActivityDay]
    languages: list[LanguageCount]
    window_days: int
    timezone: Literal["UTC"] = "UTC"
    scope: Literal["owned_calls", "tenant"]


class WorkspaceContext(BaseModel):
    data_kind: Literal["stored_records", "synthetic_validation"]
    live_transport: Literal["not_available", "webrtc_direct_demo"] = "not_available"
    training_controls: Literal["not_available"] = "not_available"


class ModelVersionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    family: str
    version: str
    status: str
    created_at: datetime


class ModelVersionPage(BaseModel):
    items: list[ModelVersionItem]
    limit: int
    offset: int


class Report(BaseModel):
    acoustic_emotion: EmotionResult | None = None
    duration_seconds: float | None = Field(default=None, ge=0)
    model_runs: list[ModelRun] = Field(default_factory=list)
    call_id: UUID
    status: Literal["completed", "failed", "flagged_for_review"]
    processed_at: datetime
    transcription: TranscriptionResult
    summary: SummaryResult
    qa_scores: QAScoreResult

    @classmethod
    def from_report(
        cls, report: CallReport, *, include_synthetic_emotion: bool = False
    ) -> "Report":
        data = {
            **report.model_dump(),
            "duration_seconds": report.intake.audio_properties.duration_seconds,
        }
        if not include_synthetic_emotion:
            data["acoustic_emotion"] = None
        return cls.model_validate(data)


class JobStatus(BaseModel):
    id: UUID
    call_id: UUID | None
    status: str
    attempts: int = Field(ge=0)
    error_code: str | None = None
    queue: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    metrics: dict[str, float] = Field(default_factory=dict)
    # Phase transitions are real; percentage is unmeasured.
    progress: float | None = Field(default=None, ge=0, le=1)
