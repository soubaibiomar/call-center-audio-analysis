"""Transaction-bound human review with conservative dual-review training eligibility."""

import hashlib
from typing import Any, cast
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from ml.emotion.contracts import EmotionLabel, EmotionSignal
from services.api.auth import Principal
from services.api.db.models import Call, EmotionItem, EmotionPartitionKey, EmotionVote
from services.reviews.contracts import Enrollment, ItemView, ReviewStatus, VoteInput, VoteView
from src.database.models import CallRecord
from src.security.pii_redactor import redact_pii


def require_reviewer(identity: Principal) -> None:
    if identity.role not in {"supervisor", "admin"}:
        raise HTTPException(403)


def get_item(
    session: Session, identity: Principal, item_id: str, *, lock: bool = False
) -> EmotionItem:
    require_reviewer(identity)
    query = (
        select(EmotionItem)
        .join(Call, (Call.id == EmotionItem.call_id) & (Call.tenant_id == EmotionItem.tenant_id))
        .where(
            EmotionItem.id == item_id,
            EmotionItem.tenant_id == identity.tenant_id,
            Call.expires_at > func.now(),
        )
    )
    if lock:
        query = query.with_for_update(of=EmotionItem)
    item = session.scalar(query)
    if item is None or item.partition == "evaluation" and identity.role != "admin":
        raise HTTPException(404)
    return item


def view(session: Session, item: EmotionItem) -> ItemView:
    votes = list(
        session.scalars(
            select(EmotionVote)
            .where(EmotionVote.tenant_id == item.tenant_id, EmotionVote.item_id == item.id)
            .order_by(EmotionVote.reviewer_id)
        )
    )
    labels = {v.label for v in votes}
    status: ReviewStatus = "pending"
    correction = None
    if len(votes) >= 2:
        if len(labels) > 1:
            status = "disagreement"
        elif "Unknown" in labels:
            status = "uncertain"
        else:
            status = "verified"
            correction = next(iter(labels))
    if item.adjudicated_label is not None:
        correction = item.adjudicated_label
        status = "uncertain" if correction == "Unknown" else "adjudicated"
    eligible = (
        item.partition == "train" and item.consent_to_train and correction not in {None, "Unknown"}
    )
    return ItemView(
        id=UUID(item.id),
        call_id=UUID(item.call_id),
        source_audio_sha256=item.source_digest,
        prediction=EmotionSignal.model_validate(item.prediction),
        partition=item.partition,
        consent_to_train=item.consent_to_train,
        revision=item.revision,
        status=status,
        corrected_label=cast(EmotionLabel | None, correction),
        votes=[
            VoteView(reviewer_id=v.reviewer_id, label=v.label, notes=v.notes, version=v.version)
            for v in votes
        ],
        adjudication_note=item.adjudication_note,
        eligible_for_training=eligible,
    )


def enroll(session: Session, identity: Principal, call_id: str, data: Enrollment) -> ItemView:
    if identity.role != "admin":
        raise HTTPException(403)
    call = session.scalar(
        select(Call).where(
            Call.id == call_id, Call.tenant_id == identity.tenant_id, Call.expires_at > func.now()
        )
    )
    if call is None:
        raise HTTPException(404)
    report = session.scalar(select(CallRecord).where(CallRecord.call_id == call.legacy_call_id))
    try:
        import json

        if report is None or report.report_json is None:
            raise ValueError("Missing source report")
        original = json.loads(report.report_json)["acoustic_emotion"]["signals"][data.segment_index]
        signal = EmotionSignal.model_validate(original)
    except (AttributeError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise HTTPException(422) from exc
    if data.partition == "evaluation" and data.consent_to_train:
        raise HTTPException(422)
    keys = [
        f"audio:{data.audio_sha256}",
        f"conversation:{data.conversation_key}",
        *(f"speaker:{s}" for s in data.speaker_keys),
    ]
    digests = sorted({hashlib.sha256(k.encode()).hexdigest() for k in keys})
    for digest in digests:
        session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"),
            {"key": identity.tenant_id + digest},
        )
        existing = session.get(EmotionPartitionKey, (identity.tenant_id, digest))
        if existing and existing.partition != data.partition:
            raise HTTPException(409)
        if existing is None:
            session.add(
                EmotionPartitionKey(
                    tenant_id=identity.tenant_id, key_digest=digest, partition=data.partition
                )
            )
            session.flush()
    if session.scalar(
        select(EmotionItem.id).where(
            EmotionItem.tenant_id == identity.tenant_id,
            EmotionItem.call_id == call_id,
            EmotionItem.segment_index == data.segment_index,
        )
    ):
        raise HTTPException(409)
    item = EmotionItem(
        tenant_id=identity.tenant_id,
        call_id=call_id,
        segment_index=data.segment_index,
        prediction=signal.model_dump(mode="json"),
        partition=data.partition,
        source_digest=data.audio_sha256,
        group_keys=digests,
        consent_to_train=data.consent_to_train,
        consent_evidence=data.consent_evidence,
    )
    session.add(item)
    session.flush()
    return view(session, item)


def invalidate(item: EmotionItem) -> None:
    item.adjudicated_label = None
    item.adjudicator_id = None
    item.adjudication_note = None
    item.revision += 1


def vote(session: Session, identity: Principal, item_id: str, data: VoteInput) -> ItemView:
    item = get_item(session, identity, item_id, lock=True)
    if item.revision != data.expected_revision:
        raise HTTPException(409)
    existing = session.scalar(
        select(EmotionVote).where(
            EmotionVote.tenant_id == identity.tenant_id,
            EmotionVote.item_id == item_id,
            EmotionVote.reviewer_id == identity.user_id,
        )
    )
    if existing is None:
        existing = EmotionVote(
            tenant_id=identity.tenant_id,
            item_id=item_id,
            reviewer_id=identity.user_id,
            label=data.label,
            notes="",
            confirmed=True,
        )
        session.add(existing)
    else:
        existing.version += 1
    existing.label = data.label
    existing.notes = redact_pii(data.notes).redacted_text
    invalidate(item)
    session.flush()
    return view(session, item)


def revoke_vote(session: Session, identity: Principal, item_id: str) -> ItemView:
    item = get_item(session, identity, item_id, lock=True)
    session.execute(
        delete(EmotionVote).where(
            EmotionVote.tenant_id == identity.tenant_id,
            EmotionVote.item_id == item_id,
            EmotionVote.reviewer_id == identity.user_id,
        )
    )
    invalidate(item)
    session.flush()
    return view(session, item)


def dataset(session: Session, identity: Principal) -> list[dict[str, Any]]:
    if identity.role != "admin":
        raise HTTPException(403)
    items = session.scalars(
        select(EmotionItem)
        .join(Call, (Call.id == EmotionItem.call_id) & (Call.tenant_id == EmotionItem.tenant_id))
        .where(
            EmotionItem.tenant_id == identity.tenant_id,
            EmotionItem.partition == "train",
            EmotionItem.consent_to_train.is_(True),
            Call.expires_at > func.now(),
        )
        .order_by(EmotionItem.id)
        .limit(1001)
        .with_for_update(of=EmotionItem)
    )
    rows = []
    for index, item in enumerate(items):
        if index >= 1000:
            raise HTTPException(413)
        current = view(session, item)
        if current.eligible_for_training:
            rows.append(
                dict(
                    item_id=item.id,
                    call_id=item.call_id,
                    revision=item.revision,
                    label=current.corrected_label,
                    source_audio_sha256=item.source_digest,
                    prediction_model_revision=current.prediction.model_revision,
                    start=current.prediction.start,
                    end=current.prediction.end,
                    reviewer_ids=[v.reviewer_id for v in current.votes],
                    adjudicator_id=item.adjudicator_id,
                )
            )
    return rows


def agreement(session: Session, identity: Principal) -> dict[str, Any]:
    require_reviewer(identity)
    query = select(EmotionItem.id).where(EmotionItem.tenant_id == identity.tenant_id)
    if identity.role != "admin":
        query = query.where(EmotionItem.partition == "train")
    pairs = agreed = corrected = 0
    for index, item_id in enumerate(session.scalars(query.limit(1001))):
        if index >= 1000:
            raise HTTPException(413)
        try:
            current = view(session, get_item(session, identity, item_id))
        except HTTPException as exc:
            if exc.status_code == 404:
                continue
            raise
        corrected += int(current.corrected_label not in {None, "Unknown"})
        if len(current.votes) == 2:
            pairs += 1
            agreed += int(current.votes[0].label == current.votes[1].label)
    return dict(
        corrected_segments=corrected,
        audit_pairs=pairs,
        agreeing_pairs=agreed,
        exact_label_agreement=agreed / pairs if pairs else None,
        note="Current paired reviews, including Unknown; not population reliability or kappa",
    )
