"""Normalized PostgreSQL models plus tenant-scoped legacy compatibility tables."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.database.models import Base as LegacyBase


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = (CheckConstraint("retention_days > 0", name="ck_tenant_retention"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200))
    retention_days: Mapped[int] = mapped_column(Integer, default=90)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class OwnedRecord(Base):
    __abstract__ = True
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)


class User(OwnedRecord):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_user_tenant_id"),
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
        CheckConstraint("role IN ('agent','supervisor','admin','service')", name="ck_user_role"),
    )
    email: Mapped[str | None] = mapped_column(String(320))
    display_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20), default="agent")
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    password_hash: Mapped[str | None] = mapped_column(Text)


class ExternalIdentity(OwnedRecord):
    __tablename__ = "external_identities"
    __table_args__ = (
        UniqueConstraint("tenant_id", "issuer", "subject", name="uq_external_identity"),
        ForeignKeyConstraint(["tenant_id", "user_id"], ["users.tenant_id", "users.id"]),
    )
    issuer: Mapped[str] = mapped_column(String(512))
    subject: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[str] = mapped_column(String(36), index=True)


class ModelVersion(OwnedRecord):
    __tablename__ = "model_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_model_tenant_id"),
        UniqueConstraint("tenant_id", "family", "version", name="uq_model_version"),
    )
    family: Mapped[str] = mapped_column(String(40))
    version: Mapped[str] = mapped_column(String(100))
    artifact_uri: Mapped[str | None] = mapped_column(Text)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30), default="candidate")
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Call(OwnedRecord):
    __tablename__ = "calls"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_call_tenant_id"),
        ForeignKeyConstraint(["tenant_id", "owner_user_id"], ["users.tenant_id", "users.id"]),
        ForeignKeyConstraint(
            ["tenant_id", "model_version_id"], ["model_versions.tenant_id", "model_versions.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "legacy_call_id"],
            ["call_records.tenant_id", "call_records.call_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("qa_score IS NULL OR (qa_score >= 0 AND qa_score <= 5)", name="ck_call_qa"),
        Index("ix_calls_tenant_processed", "tenant_id", "processed_at"),
        Index("ix_calls_tenant_status", "tenant_id", "status"),
    )
    owner_user_id: Mapped[str] = mapped_column(String(36))
    model_version_id: Mapped[str | None] = mapped_column(String(36))
    legacy_call_id: Mapped[str] = mapped_column(String(36), unique=True)
    status: Mapped[str] = mapped_column(String(30))
    audio_filename: Mapped[str] = mapped_column(String(255))
    audio_object_key: Mapped[str | None] = mapped_column(Text)
    caller_id: Mapped[str | None] = mapped_column(String(255))
    department: Mapped[str | None] = mapped_column(String(255))
    language: Mapped[str | None] = mapped_column(String(30))
    qa_score: Mapped[float | None] = mapped_column(Float)
    resolution_status: Mapped[str | None] = mapped_column(String(30))
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    legal_hold: Mapped[bool] = mapped_column(Boolean, default=False)


class Segment(OwnedRecord):
    __tablename__ = "segments"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "call_id"], ["calls.tenant_id", "calls.id"], ondelete="CASCADE"
        ),
        UniqueConstraint("tenant_id", "call_id", "position", name="uq_segment_position"),
        CheckConstraint(
            "start_seconds >= 0 AND end_seconds >= start_seconds", name="ck_segment_times"
        ),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_segment_confidence"),
    )
    call_id: Mapped[str] = mapped_column(String(36))
    position: Mapped[int] = mapped_column(Integer)
    start_seconds: Mapped[float] = mapped_column(Float)
    end_seconds: Mapped[float] = mapped_column(Float)
    speaker: Mapped[str] = mapped_column(String(100))
    text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)


class Job(OwnedRecord):
    __tablename__ = "jobs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "call_id"], ["calls.tenant_id", "calls.id"], ondelete="CASCADE"
        ),
        Index("ix_jobs_tenant_status", "tenant_id", "status"),
        CheckConstraint("attempts >= 0", name="ck_job_attempts"),
    )
    call_id: Mapped[str] = mapped_column(String(36))
    status: Mapped[str] = mapped_column(String(30), default="queued")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AnalysisJob(OwnedRecord):
    __tablename__ = "analysis_jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "owner_user_id", "idempotency_key", name="uq_job_request"),
        ForeignKeyConstraint(["tenant_id", "owner_user_id"], ["users.tenant_id", "users.id"]),
        ForeignKeyConstraint(
            ["tenant_id", "call_id"], ["calls.tenant_id", "calls.id"], ondelete="CASCADE"
        ),
        CheckConstraint("queue IN ('cpu','gpu')", name="ck_analysis_queue"),
        CheckConstraint(
            "status IN ('queued','running','retrying','cancelling',"
            "'finished','failed','cancelled')",
            name="ck_analysis_status",
        ),
        CheckConstraint(
            "attempts >= 0 AND max_attempts BETWEEN 1 AND 5", name="ck_analysis_attempts"
        ),
        Index("ix_analysis_dispatch", "tenant_id", "queue", "status", "next_attempt_at"),
    )
    owner_user_id: Mapped[str] = mapped_column(String(36))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    fingerprint: Mapped[str] = mapped_column(String(64))
    audio_sha256: Mapped[str] = mapped_column(String(64))
    audio_size: Mapped[int] = mapped_column(Integer)
    queue: Mapped[str] = mapped_column(String(8), default="cpu")
    status: Mapped[str] = mapped_column(String(20), default="queued")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    caller_id: Mapped[str | None] = mapped_column(String(255))
    department: Mapped[str | None] = mapped_column(String(255))
    call_id: Mapped[str | None] = mapped_column(String(36))
    error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class Review(OwnedRecord):
    __tablename__ = "reviews"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "call_id"], ["calls.tenant_id", "calls.id"], ondelete="CASCADE"
        ),
        ForeignKeyConstraint(["tenant_id", "reviewer_user_id"], ["users.tenant_id", "users.id"]),
        UniqueConstraint("tenant_id", "call_id", "version", name="uq_review_version"),
        CheckConstraint("version > 0", name="ck_review_version"),
    )
    call_id: Mapped[str] = mapped_column(String(36))
    reviewer_user_id: Mapped[str] = mapped_column(String(36))
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    corrections: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    approved_for_training: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TrainingRun(OwnedRecord):
    __tablename__ = "training_runs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "model_version_id"], ["model_versions.tenant_id", "model_versions.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "requested_by_user_id"], ["users.tenant_id", "users.id"]
        ),
    )
    model_version_id: Mapped[str] = mapped_column(String(36))
    requested_by_user_id: Mapped[str] = mapped_column(String(36))
    dataset_version: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="planned")
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LegacyImport(OwnedRecord):
    __tablename__ = "legacy_imports"
    __table_args__ = (UniqueConstraint("tenant_id", "source_sha256", name="uq_import_source"),)
    source_sha256: Mapped[str] = mapped_column(String(64))
    row_counts: Mapped[dict[str, int]] = mapped_column(JSONB)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# PostgreSQL adds tenant ownership without changing the original SQLite mappings.
for source_table in LegacyBase.metadata.sorted_tables:
    table = source_table.to_metadata(Base.metadata)
    table.append_column(
        Column(
            "tenant_id",
            String(36),
            ForeignKey("tenants.id"),
            nullable=False,
            server_default=text("NULLIF(current_setting('app.tenant_id', true), '')"),
        )
    )
    Index(f"ix_{table.name}_tenant", table.c.tenant_id)
    if table.name == "call_records":
        table.append_constraint(
            UniqueConstraint("tenant_id", "call_id", name="uq_legacy_tenant_call")
        )
    if table.name == "transcription_cache":
        for index in list(table.indexes):
            if index.unique:
                table.indexes.remove(index)
        Index("uq_cache_tenant_hash", table.c.tenant_id, table.c.audio_hash, unique=True)


class EmotionItem(OwnedRecord):
    __tablename__ = "emotion_items"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_emotion_item_tenant"),
        UniqueConstraint("tenant_id", "call_id", "segment_index", name="uq_emotion_segment"),
        ForeignKeyConstraint(
            ["tenant_id", "call_id"], ["calls.tenant_id", "calls.id"], ondelete="CASCADE"
        ),
        CheckConstraint("partition IN ('train','evaluation')", name="ck_emotion_partition"),
        CheckConstraint("partition='train' OR NOT consent_to_train", name="ck_emotion_consent"),
        CheckConstraint("revision>0 AND segment_index>=0", name="ck_emotion_bounds"),
    )
    call_id: Mapped[str] = mapped_column(String(36))
    segment_index: Mapped[int] = mapped_column(Integer)
    prediction: Mapped[dict[str, Any]] = mapped_column(JSONB)
    partition: Mapped[str] = mapped_column(String(12))
    source_digest: Mapped[str] = mapped_column(String(64))
    group_keys: Mapped[list[str]] = mapped_column(JSONB)
    consent_to_train: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_evidence: Mapped[str] = mapped_column(String(300))
    revision: Mapped[int] = mapped_column(Integer, default=1)
    adjudicated_label: Mapped[str | None] = mapped_column(String(20))
    adjudicator_id: Mapped[str | None] = mapped_column(String(36))
    adjudication_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EmotionPartitionKey(Base):
    __tablename__ = "emotion_partition_keys"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), primary_key=True)
    key_digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    partition: Mapped[str] = mapped_column(String(12))


class EmotionVote(OwnedRecord):
    __tablename__ = "emotion_votes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "item_id"],
            ["emotion_items.tenant_id", "emotion_items.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(["tenant_id", "reviewer_id"], ["users.tenant_id", "users.id"]),
        UniqueConstraint("tenant_id", "item_id", "reviewer_id", name="uq_emotion_reviewer"),
        CheckConstraint(
            "label IN ('neutral','happy','angry','sad','Unknown')", name="ck_emotion_vote_label"
        ),
    )
    item_id: Mapped[str] = mapped_column(String(36))
    reviewer_id: Mapped[str] = mapped_column(String(36))
    label: Mapped[str] = mapped_column(String(20))
    notes: Mapped[str] = mapped_column(Text)
    confirmed: Mapped[bool] = mapped_column(Boolean)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CallAnnotation(OwnedRecord):
    __tablename__ = "call_annotations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_call_annotation_tenant"),
        UniqueConstraint("tenant_id", "call_id", name="uq_call_annotation_source"),
        ForeignKeyConstraint(
            ["tenant_id", "call_id"], ["calls.tenant_id", "calls.id"], ondelete="CASCADE"
        ),
        ForeignKeyConstraint(["tenant_id", "author_id"], ["users.tenant_id", "users.id"]),
        ForeignKeyConstraint(["tenant_id", "submitter_id"], ["users.tenant_id", "users.id"]),
        ForeignKeyConstraint(["tenant_id", "approver_id"], ["users.tenant_id", "users.id"]),
        CheckConstraint("partition IN ('train','evaluation')", name="ck_call_annotation_partition"),
        CheckConstraint(
            "partition='train' OR NOT consent_to_train", name="ck_call_annotation_consent"
        ),
        CheckConstraint(
            "revision>0 AND state IN ('draft','submitted','approved','rejected')",
            name="ck_call_annotation_state",
        ),
        CheckConstraint(
            "state<>'approved' OR (approver_id IS NOT NULL AND author_id IS NOT NULL "
            "AND submitter_id IS NOT NULL AND approver_id<>author_id "
            "AND approver_id<>submitter_id)",
            name="ck_call_annotation_independence",
        ),
    )
    call_id: Mapped[str] = mapped_column(String(36))
    original: Mapped[dict[str, Any]] = mapped_column(JSONB)
    original_digest: Mapped[str] = mapped_column(String(64))
    source_digest: Mapped[str] = mapped_column(String(64))
    source_attestation: Mapped[str] = mapped_column(String(500))
    group_keys: Mapped[list[str]] = mapped_column(JSONB)
    partition: Mapped[str] = mapped_column(String(12))
    consent_to_train: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_evidence: Mapped[str] = mapped_column(String(300))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    state: Mapped[str] = mapped_column(String(16), default="draft")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    author_id: Mapped[str | None] = mapped_column(String(36))
    submitter_id: Mapped[str | None] = mapped_column(String(36))
    approver_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CallAnnotationEvent(OwnedRecord):
    __tablename__ = "call_annotation_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "annotation_id"],
            ["call_annotations.tenant_id", "call_annotations.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(["tenant_id", "actor_id"], ["users.tenant_id", "users.id"]),
        UniqueConstraint(
            "tenant_id", "annotation_id", "revision", name="uq_call_annotation_event_revision"
        ),
    )
    annotation_id: Mapped[str] = mapped_column(String(36))
    actor_id: Mapped[str] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(24))
    revision: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    payload_digest: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
