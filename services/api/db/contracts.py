"""Truthful database-backed fields for future ERP history and KPI components."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CallListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tenant_id: str
    owner_user_id: str
    status: str
    audio_filename: str
    department: str | None
    language: str | None
    qa_score: float | None = Field(ge=0, le=5)
    model_version_id: str | None
    resolution_status: str | None
    processed_at: datetime
    expires_at: datetime
    legal_hold: bool


class TenantMetrics(BaseModel):
    total_calls: int = Field(ge=0)
    completed: int = Field(ge=0)
    failed: int = Field(ge=0)
    flagged_for_review: int = Field(ge=0)
    average_qa_score: float | None
    source: Literal["postgresql"] = "postgresql"
