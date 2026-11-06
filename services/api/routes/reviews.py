"""Authenticated emotion annotation and revocable dataset membership."""

import hashlib
import json
from collections.abc import Callable
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.engine import Engine

from services.api.auth import Principal
from services.api.db.models import EmotionItem
from services.api.routes.jobs import get_identity
from services.reviews import service
from services.reviews.contracts import Adjudication, ConsentInput, Enrollment, ItemView, VoteInput
from src.database.connection import session_scope
from src.security.pii_redactor import redact_pii

Identity = Annotated[Principal, Depends(get_identity)]


def reviews_router(engine: Callable[[], Engine]) -> APIRouter:
    router = APIRouter()

    @router.post("/calls/{call_id}/emotion-review-items", response_model=ItemView, status_code=201)
    def enroll(call_id: UUID, data: Enrollment, identity: Identity) -> ItemView:
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            return service.enroll(session, identity, str(call_id), data)

    @router.get("/emotion-reviews", response_model=list[ItemView])
    def listing(identity: Identity) -> list[ItemView]:
        service.require_reviewer(identity)
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            query = select(EmotionItem.id).where(EmotionItem.tenant_id == identity.tenant_id)
            if identity.role != "admin":
                query = query.where(EmotionItem.partition == "train")
            result = []
            for item_id in session.scalars(
                query.order_by(EmotionItem.created_at.desc()).limit(100)
            ):
                try:
                    result.append(
                        service.view(session, service.get_item(session, identity, item_id))
                    )
                except HTTPException as exc:
                    if exc.status_code != 404:
                        raise
            return result

    @router.post("/emotion-reviews/{item_id}/votes", response_model=ItemView)
    def vote(item_id: UUID, data: VoteInput, identity: Identity) -> ItemView:
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            return service.vote(session, identity, str(item_id), data)

    @router.delete("/emotion-reviews/{item_id}/votes/me", response_model=ItemView)
    def revoke(item_id: UUID, identity: Identity) -> ItemView:
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            return service.revoke_vote(session, identity, str(item_id))

    @router.post("/emotion-reviews/{item_id}/adjudicate", response_model=ItemView)
    def adjudicate(item_id: UUID, data: Adjudication, identity: Identity) -> ItemView:
        if identity.role != "admin":
            raise HTTPException(403)
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            item = service.get_item(session, identity, str(item_id), lock=True)
            current = service.view(session, item)
            if item.revision != data.expected_revision or current.status != "disagreement":
                raise HTTPException(409)
            if any(v.reviewer_id == identity.user_id for v in current.votes):
                raise HTTPException(403)
            item.adjudicated_label = data.label
            item.adjudicator_id = identity.user_id
            item.adjudication_note = redact_pii(data.notes).redacted_text
            item.revision += 1
            session.flush()
            return service.view(session, item)

    @router.patch("/emotion-reviews/{item_id}/consent", response_model=ItemView)
    def consent(item_id: UUID, data: ConsentInput, identity: Identity) -> ItemView:
        if identity.role != "admin":
            raise HTTPException(403)
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            item = service.get_item(session, identity, str(item_id), lock=True)
            if item.revision != data.expected_revision:
                raise HTTPException(409)
            if item.partition == "evaluation" and data.consent_to_train:
                raise HTTPException(422)
            item.consent_to_train = data.consent_to_train
            item.consent_evidence = data.consent_evidence
            item.revision += 1
            session.flush()
            return service.view(session, item)

    @router.delete("/emotion-reviews/{item_id}", status_code=204)
    def erase(item_id: UUID, identity: Identity) -> None:
        if identity.role != "admin":
            raise HTTPException(403)
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            item = session.scalar(
                select(EmotionItem)
                .where(EmotionItem.id == str(item_id), EmotionItem.tenant_id == identity.tenant_id)
                .with_for_update()
            )
            if item is None:
                raise HTTPException(404)
            session.delete(item)

    @router.get("/emotion-training-dataset")
    def dataset(identity: Identity) -> dict[str, Any]:
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            records = service.dataset(session, identity)
            fingerprint = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
            return {
                "records": records,
                "fingerprint": fingerprint,
                "notice": (
                    "Live revocable manifest; not an immutable test set or training permission"
                ),
            }

    @router.get("/emotion-review-metrics")
    def metrics(identity: Identity) -> dict[str, Any]:
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            return service.agreement(session, identity)

    return router
