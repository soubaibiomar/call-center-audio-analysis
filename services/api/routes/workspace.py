"""Read-only workspace projections using the existing verified tenant/owner scope."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import Date, Select, func, select
from sqlalchemy.engine import Engine

from services.api.auth import Principal
from services.api.db.models import Call, ModelVersion
from services.api.schemas import (
    Activity,
    ActivityDay,
    LanguageCount,
    ModelVersionItem,
    ModelVersionPage,
    WorkspaceContext,
)
from src.database.connection import session_scope


def identity(request: Request) -> Principal:
    return cast(Principal, request.state.principal)


Caller = Annotated[Principal, Depends(identity)]


def workspace_router(
    engine: Callable[[], Engine],
    call_query: Callable[[Principal], Select[tuple[Call]]],
    synthetic: bool,
    live_enabled: bool = False,
) -> APIRouter:
    router = APIRouter()

    @router.get("/workspace-context", response_model=WorkspaceContext)
    def context(caller: Caller) -> WorkspaceContext:
        return WorkspaceContext(
            data_kind="synthetic_validation" if synthetic else "stored_records",
            live_transport="webrtc_direct_demo" if live_enabled else "not_available",
        )

    @router.get("/dashboard/activity", response_model=Activity)
    def activity(caller: Caller, days: Annotated[int, Query(ge=1, le=90)] = 30) -> Activity:
        today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        start = today - timedelta(days=days - 1)
        scoped = call_query(caller).with_only_columns(Call.id)
        day = func.timezone("UTC", Call.processed_at).cast(Date)
        language = func.coalesce(func.nullif(func.trim(Call.language), ""), "Unknown")
        constraints = (
            Call.id.in_(scoped),
            Call.processed_at >= start,
            Call.processed_at < today + timedelta(days=1),
        )
        with session_scope(engine(), tenant_id=caller.tenant_id) as session:
            counts = {
                row[0]: row[1]
                for row in session.execute(
                    select(day, func.count()).where(*constraints).group_by(day)
                )
            }
            languages = session.execute(
                select(language, func.count())
                .where(*constraints)
                .group_by(language)
                .order_by(func.count().desc(), language)
            ).all()
        return Activity(
            days=[
                ActivityDay(
                    date=(start + timedelta(days=i)).date().isoformat(),
                    calls=counts.get((start + timedelta(days=i)).date(), 0),
                )
                for i in range(days)
            ],
            languages=[LanguageCount(language=row[0], calls=row[1]) for row in languages],
            window_days=days,
            scope="owned_calls" if caller.owner_filter else "tenant",
        )

    @router.get("/model-versions", response_model=ModelVersionPage)
    def models(
        caller: Caller,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0, le=10000)] = 0,
    ) -> ModelVersionPage:
        if caller.role != "admin":
            raise HTTPException(403)
        with session_scope(engine(), tenant_id=caller.tenant_id) as session:
            rows = session.scalars(
                select(ModelVersion)
                .where(ModelVersion.tenant_id == caller.tenant_id)
                .order_by(ModelVersion.created_at.desc(), ModelVersion.id)
                .limit(limit)
                .offset(offset)
            )
            return ModelVersionPage(
                items=[ModelVersionItem.model_validate(row) for row in rows],
                limit=limit,
                offset=offset,
            )

    return router
