"""Role-scoped transcript/QA corrections, audited decisions and candidate export."""

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.engine import Engine

from services.api.auth import Principal
from services.api.db.models import CallAnnotation, CallAnnotationEvent
from services.api.routes.jobs import get_identity
from services.reviews import call_service as service
from services.reviews.call_contracts import (
    AnnotationDataset,
    CallEnrollment,
    CallReviewView,
    CorrectionInput,
    DecisionInput,
    ReviewEventView,
)
from services.reviews.contracts import ConsentInput
from services.reviews.service import require_reviewer
from src.database.connection import session_scope
from src.security.pii_redactor import redact_pii

Identity = Annotated[Principal, Depends(get_identity)]


def call_reviews_router(engine: Callable[[], Engine]) -> APIRouter:
    router = APIRouter()

    @router.post("/calls/{call_id}/reviews", response_model=CallReviewView, status_code=201)
    def enroll(call_id: UUID, data: CallEnrollment, identity: Identity) -> CallReviewView:
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            return service.enroll(session, identity, str(call_id), data)

    @router.get("/calls/{call_id}/review", response_model=CallReviewView)
    def by_call(call_id: UUID, identity: Identity) -> CallReviewView:
        require_reviewer(identity)
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            review_id = session.scalar(
                select(CallAnnotation.id).where(
                    CallAnnotation.call_id == str(call_id),
                    CallAnnotation.tenant_id == identity.tenant_id,
                )
            )
            if review_id is None:
                raise HTTPException(404)
            return service.view(service.get_review(session, identity, review_id))

    @router.patch("/call-reviews/{review_id}", response_model=CallReviewView)
    def edit(review_id: UUID, data: CorrectionInput, identity: Identity) -> CallReviewView:
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            return service.edit(session, identity, str(review_id), data)

    @router.post("/call-reviews/{review_id}/decisions", response_model=CallReviewView)
    def decide(review_id: UUID, data: DecisionInput, identity: Identity) -> CallReviewView:
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            return service.decide(session, identity, str(review_id), data)

    @router.patch("/call-reviews/{review_id}/consent", response_model=CallReviewView)
    def consent(review_id: UUID, data: ConsentInput, identity: Identity) -> CallReviewView:
        if identity.role != "admin":
            raise HTTPException(403)
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            row = service.get_review(session, identity, str(review_id), lock=True)
            service.check_revision(row, data.expected_revision)
            if row.partition == "evaluation" and data.consent_to_train:
                raise HTTPException(422)
            row.consent_to_train = data.consent_to_train
            row.consent_evidence = redact_pii(data.consent_evidence).redacted_text[:300]
            row.revision += 1
            service.event(session, row, identity, "consent_changed")
            return service.view(row)

    @router.get("/call-reviews/{review_id}/history", response_model=list[ReviewEventView])
    def history(
        review_id: UUID, identity: Identity, limit: Annotated[int, Query(ge=1, le=100)] = 20
    ) -> list[ReviewEventView]:
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            row = service.get_review(session, identity, str(review_id))
            events = session.scalars(
                select(CallAnnotationEvent)
                .where(
                    CallAnnotationEvent.tenant_id == identity.tenant_id,
                    CallAnnotationEvent.annotation_id == row.id,
                )
                .order_by(CallAnnotationEvent.revision.desc())
                .limit(limit)
            )
            return [
                ReviewEventView(
                    id=UUID(e.id),
                    actor_id=e.actor_id,
                    action=e.action,
                    revision=e.revision,
                    payload_sha256=e.payload_digest,
                    created_at=e.created_at,
                )
                for e in events
            ]

    @router.get("/call-review-dataset", response_model=AnnotationDataset)
    def dataset(identity: Identity) -> AnnotationDataset:
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            return service.dataset(session, identity)

    @router.delete("/call-reviews/{review_id}", status_code=204)
    def erase(
        review_id: UUID, identity: Identity, expected_revision: Annotated[int, Query(ge=1)]
    ) -> Response:
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            service.erase(session, identity, str(review_id), expected_revision)
        return Response(status_code=204)

    return router
