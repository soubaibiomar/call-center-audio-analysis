"""Transactional call corrections; independent approval, source gates and live export."""

import hashlib
import json
import math
from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from services.api.auth import Principal
from services.api.db.models import Call, CallAnnotation, CallAnnotationEvent, EmotionPartitionKey
from services.reviews.call_contracts import (
    AnnotationDataset,
    AnnotationExportItem,
    CallEnrollment,
    CallReviewView,
    CorrectionInput,
    CorrectionPayload,
    DecisionInput,
    ReviewSnapshot,
    SegmentCorrection,
)
from services.reviews.service import require_reviewer
from src.database.models import AuditLogEntry, CallRecord
from src.graph.state import CallReport
from src.security.pii_redactor import redact_pii


def fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def get_review(
    session: Session,
    identity: Principal,
    review_id: str,
    *,
    lock: bool = False,
    allow_expired: bool = False,
) -> CallAnnotation:
    require_reviewer(identity)
    query = (
        select(CallAnnotation)
        .join(
            Call, (Call.id == CallAnnotation.call_id) & (Call.tenant_id == CallAnnotation.tenant_id)
        )
        .where(
            CallAnnotation.tenant_id == identity.tenant_id,
            CallAnnotation.id == review_id,
        )
    )
    if not allow_expired:
        query = query.where(Call.expires_at > func.now())
    if lock:
        query = query.with_for_update(of=CallAnnotation)
    row = session.scalar(query)
    if row is None or row.partition == "evaluation" and identity.role != "admin":
        raise HTTPException(404)
    return row


def eligible(row: CallAnnotation) -> bool:
    payload = CorrectionPayload.model_validate(row.payload)
    return (
        row.state == "approved"
        and row.partition == "train"
        and row.consent_to_train
        and all(not s.uncertain and s.speaker_role != "Unknown" for s in payload.segments)
    )


def view(row: CallAnnotation) -> CallReviewView:
    return CallReviewView(
        id=UUID(row.id),
        call_id=UUID(row.call_id),
        original=ReviewSnapshot.model_validate(row.original),
        original_sha256=row.original_digest,
        source_audio_sha256=row.source_digest,
        source_attestation=row.source_attestation,
        partition="train" if row.partition == "train" else "evaluation",
        consent_to_train=row.consent_to_train,
        revision=row.revision,
        state=cast(Literal["draft", "submitted", "approved", "rejected"], row.state),
        payload=CorrectionPayload.model_validate(row.payload),
        author_id=row.author_id,
        submitter_id=row.submitter_id,
        approver_id=row.approver_id,
        eligible_for_training=eligible(row),
        updated_at=row.updated_at,
    )


def event(
    session: Session,
    row: CallAnnotation,
    identity: Principal,
    action: str,
    reason: str = "",
    evidence: dict[str, Any] | None = None,
) -> None:
    row.updated_at = datetime.now(UTC)
    snapshot = {
        "correction": row.payload,
        "state": row.state,
        "consent_to_train": row.consent_to_train,
        "consent_evidence": row.consent_evidence,
        "author_id": row.author_id,
        "submitter_id": row.submitter_id,
        "approver_id": row.approver_id,
        "rationale": redact_pii(reason).redacted_text,
        "actor_role": identity.role,
        "source_audio_sha256": row.source_digest,
        "playback_attestation": evidence,
    }
    session.add(
        CallAnnotationEvent(
            tenant_id=row.tenant_id,
            annotation_id=row.id,
            actor_id=identity.user_id,
            action=action,
            revision=row.revision,
            payload=snapshot,
            payload_digest=fingerprint(snapshot),
        )
    )
    session.flush()


def enroll(
    session: Session, identity: Principal, call_id: str, data: CallEnrollment
) -> CallReviewView:
    if identity.role != "admin":
        raise HTTPException(403)
    call = session.scalar(
        select(Call)
        .where(
            Call.id == call_id, Call.tenant_id == identity.tenant_id, Call.expires_at > func.now()
        )
        .with_for_update()
    )
    if call is None:
        raise HTTPException(404)
    if session.scalar(
        select(CallAnnotation.id).where(
            CallAnnotation.tenant_id == identity.tenant_id, CallAnnotation.call_id == call_id
        )
    ):
        raise HTTPException(409)
    original = session.scalar(select(CallRecord).where(CallRecord.call_id == call.legacy_call_id))
    try:
        if original is None or original.report_json is None:
            raise ValueError("Missing report")
        report = CallReport.model_validate_json(original.report_json)
        snapshot = ReviewSnapshot(
            transcription=report.transcription,
            qa_scores=report.qa_scores,
            duration_seconds=report.intake.audio_properties.duration_seconds,
            model_runs=report.model_runs,
        )
        if not 1 <= len(snapshot.transcription.segments) <= 500:
            raise ValueError("Unsupported segment count")
        if any(
            not math.isfinite(s.start_time)
            or not math.isfinite(s.end_time)
            or not 0 <= s.start_time < s.end_time <= snapshot.duration_seconds
            for s in snapshot.transcription.segments
        ):
            raise ValueError("Invalid source timing")
    except (ValueError, TypeError) as exc:
        raise HTTPException(422) from exc
    if data.partition == "evaluation" and data.consent_to_train:
        raise HTTPException(422)
    keys = [
        f"audio:{data.audio_sha256}",
        f"conversation:{data.conversation_key}",
        *(f"speaker:{s}" for s in data.speaker_keys),
    ]
    digests = sorted({hashlib.sha256(key.encode()).hexdigest() for key in keys})
    for digest in digests:
        session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"),
            {"key": identity.tenant_id + digest},
        )
        existing = session.get(EmotionPartitionKey, (identity.tenant_id, digest))
        if existing is not None and existing.partition != data.partition:
            raise HTTPException(409)
        if existing is None:
            session.add(
                EmotionPartitionKey(
                    tenant_id=identity.tenant_id, key_digest=digest, partition=data.partition
                )
            )
            session.flush()
    try:
        payload = CorrectionPayload(
            segments=[
                SegmentCorrection.model_validate(
                    dict(
                        segment_index=i,
                        text=s.text,
                        speaker_role=s.speaker_role
                        or (s.speaker if s.speaker in {"Agent", "Customer"} else "Unknown"),
                        uncertain=s.low_confidence,
                    )
                )
                for i, s in enumerate(snapshot.transcription.segments)
            ]
        )
    except ValueError as exc:
        raise HTTPException(422) from exc
    raw = snapshot.model_dump(mode="json")
    row = CallAnnotation(
        tenant_id=identity.tenant_id,
        call_id=call_id,
        original=raw,
        original_digest=fingerprint(raw),
        source_digest=data.audio_sha256,
        source_attestation=redact_pii(data.source_attestation).redacted_text[:500],
        group_keys=digests,
        partition=data.partition,
        consent_to_train=data.consent_to_train,
        consent_evidence=redact_pii(data.consent_evidence).redacted_text[:300],
        payload=payload.model_dump(mode="json"),
        state="draft",
        revision=1,
    )
    session.add(row)
    session.flush()
    event(session, row, identity, "enrolled")
    return view(row)


def check_revision(row: CallAnnotation, expected: int) -> None:
    if row.revision != expected:
        raise HTTPException(409)


def edit(
    session: Session, identity: Principal, review_id: str, data: CorrectionInput
) -> CallReviewView:
    row = get_review(session, identity, review_id, lock=True)
    check_revision(row, data.expected_revision)
    original = ReviewSnapshot.model_validate(row.original)
    if sorted(s.segment_index for s in data.segments) != list(
        range(len(original.transcription.segments))
    ):
        raise HTTPException(422)
    if data.qa_override is not None and data.qa_override.audio_end > original.duration_seconds:
        raise HTTPException(422)
    if any(redact_pii(s.text).pii_found for s in data.segments):
        raise HTTPException(422)
    payload = CorrectionPayload(
        segments=sorted(data.segments, key=lambda s: s.segment_index), qa_override=data.qa_override
    )
    if payload.qa_override is not None:
        payload.qa_override.rationale = redact_pii(payload.qa_override.rationale).redacted_text[
            :2000
        ]
        if len(payload.qa_override.rationale.strip()) < 10:
            raise HTTPException(422)
    row.payload = payload.model_dump(mode="json")
    row.author_id = identity.user_id
    row.submitter_id = None
    row.approver_id = None
    row.state = "draft"
    row.revision += 1
    event(session, row, identity, "edited")
    return view(row)


def decide(
    session: Session, identity: Principal, review_id: str, data: DecisionInput
) -> CallReviewView:
    row = get_review(session, identity, review_id, lock=True)
    check_revision(row, data.expected_revision)
    original = ReviewSnapshot.model_validate(row.original)
    if (
        data.observed_audio_sha256 != row.source_digest
        or abs(data.observed_duration_seconds - original.duration_seconds) > 0.25
    ):
        raise HTTPException(422)
    if data.action == "submit":
        if row.state != "draft" or row.author_id != identity.user_id:
            raise HTTPException(409)
        row.state = "submitted"
        row.submitter_id = identity.user_id
        row.approver_id = None
    else:
        if row.state != "submitted":
            raise HTTPException(409)
        if identity.user_id in {row.author_id, row.submitter_id}:
            raise HTTPException(403)
        row.state = "approved" if data.action == "approve" else "rejected"
        row.approver_id = identity.user_id if data.action == "approve" else None
    row.revision += 1
    event(
        session,
        row,
        identity,
        data.action,
        data.rationale,
        {
            "listened_to_audio": data.listened_to_audio,
            "observed_audio_sha256": data.observed_audio_sha256,
            "observed_duration_seconds": data.observed_duration_seconds,
        },
    )
    return view(row)


def dataset(session: Session, identity: Principal) -> AnnotationDataset:
    if identity.role != "admin":
        raise HTTPException(403)
    rows = list(
        session.execute(
            select(CallAnnotation, Call.expires_at)
            .join(
                Call,
                (Call.id == CallAnnotation.call_id) & (Call.tenant_id == CallAnnotation.tenant_id),
            )
            .where(
                CallAnnotation.tenant_id == identity.tenant_id,
                CallAnnotation.state == "approved",
                CallAnnotation.partition == "train",
                CallAnnotation.consent_to_train.is_(True),
                Call.expires_at > func.now(),
            )
            .order_by(CallAnnotation.updated_at.desc(), CallAnnotation.id)
            .limit(101)
            .with_for_update(of=CallAnnotation)
        )
    )
    items = []
    for row, expires in rows[:100]:
        if eligible(row) and row.author_id and row.approver_id:
            items.append(
                AnnotationExportItem(
                    review_id=UUID(row.id),
                    call_id=UUID(row.call_id),
                    revision=row.revision,
                    source_audio_sha256=row.source_digest,
                    original_sha256=row.original_digest,
                    source_expires_at=expires,
                    author_id=row.author_id,
                    approver_id=row.approver_id,
                    payload=CorrectionPayload.model_validate(row.payload),
                )
            )
    values = [i.model_dump(mode="json") for i in items]
    return AnnotationDataset(
        items=items,
        approved_segments=sum(len(i.payload.segments) for i in items),
        truncated=len(rows) > 100,
        fingerprint=fingerprint(values),
    )


def erase(session: Session, identity: Principal, review_id: str, expected: int) -> None:
    if identity.role != "admin":
        raise HTTPException(403)
    row = get_review(session, identity, review_id, lock=True, allow_expired=True)
    check_revision(row, expected)
    session.add(
        AuditLogEntry(call_id=row.call_id, action="call_annotation_erased", user=identity.user_id)
    )
    session.delete(row)
    session.flush()
