"""Transaction-bound normalized persistence; callers must establish tenant identity."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import case, delete, func, select
from sqlalchemy.orm import Session

from services.api.db.contracts import TenantMetrics
from services.api.db.models import Base, Call, Segment, Tenant
from services.api.db.settings import LEGACY_TENANT_ID, LEGACY_USER_ID
from src.database.models import CallRecord
from src.graph.state import CallReport


def store_report(
    session: Session,
    report: CallReport,
    tenant_id: str = LEGACY_TENANT_ID,
    owner_user_id: str = LEGACY_USER_ID,
) -> Call:
    """Add normalized rows to the same transaction as the compatibility record."""
    tenant = session.get(Tenant, tenant_id)
    if tenant is None:
        raise ValueError("Tenant has not been provisioned")
    timestamp = report.processed_at
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    call = Call(
        id=str(report.call_id),
        tenant_id=tenant_id,
        owner_user_id=owner_user_id,
        legacy_call_id=str(report.call_id),
        status=report.status,
        audio_filename=report.intake.audio_path.replace("\\", "/").rsplit("/", 1)[-1],
        qa_score=report.qa_scores.overall_score,
        resolution_status=report.summary.resolution_status.value,
        processed_at=timestamp,
        expires_at=timestamp + timedelta(days=tenant.retention_days),
    )
    session.add(call)
    session.flush()
    session.add_all(
        [
            Segment(
                tenant_id=tenant_id,
                call_id=call.id,
                position=index,
                start_seconds=segment.start_time,
                end_seconds=segment.end_time,
                speaker=segment.speaker,
                text=segment.text,
                confidence=segment.confidence,
            )
            for index, segment in enumerate(report.transcription.segments)
        ]
    )
    return call


def scoped_calls(
    session: Session,
    tenant_id: str,
    *,
    owner_user_id: str | None = None,
    status: str | None = None,
    limit: int = 200,
) -> list[Call]:
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between1 and1000")
    query = select(Call).where(Call.tenant_id == tenant_id)
    if owner_user_id:
        query = query.where(Call.owner_user_id == owner_user_id)
    if status:
        query = query.where(Call.status == status)
    return list(session.scalars(query.order_by(Call.processed_at.desc(), Call.id).limit(limit)))


def expire_calls(
    session: Session, tenant_id: str, *, before: datetime, apply: bool = False
) -> list[str]:
    """Explicit retention action; dry-run by default; never delete held calls/audit."""
    if before.tzinfo is None:
        raise ValueError("Retention cutoff must include a timezone")
    ids = list(
        session.scalars(
            select(Call.legacy_call_id).where(
                Call.tenant_id == tenant_id, Call.expires_at < before, Call.legal_hold.is_(False)
            )
        )
    )
    if apply and ids:
        # Database FK cascades remove only the linked normalized call/segments/jobs/reviews.
        session.execute(delete(CallRecord).where(CallRecord.call_id.in_(ids)))
    return ids


def expire_cache(
    session: Session, tenant_id: str, *, before: datetime, apply: bool = False
) -> list[int]:
    """Purge ephemeral raw cache separately; legal-hold call records remain intact."""
    if before.tzinfo is None:
        raise ValueError("Retention cutoff must include a timezone")
    table = Base.metadata.tables["transcription_cache"]
    cutoff = before.astimezone(UTC).replace(tzinfo=None)
    ids = list(
        session.scalars(
            select(table.c.id).where(table.c.tenant_id == tenant_id, table.c.created_at < cutoff)
        )
    )
    if apply and ids:
        session.execute(delete(table).where(table.c.tenant_id == tenant_id, table.c.id.in_(ids)))
    return ids


def tenant_metrics(session: Session, tenant_id: str) -> TenantMetrics:
    row = session.execute(
        select(
            func.count(Call.id),
            func.sum(case((Call.status == "completed", 1), else_=0)),
            func.sum(case((Call.status == "failed", 1), else_=0)),
            func.sum(case((Call.status == "flagged_for_review", 1), else_=0)),
            func.avg(Call.qa_score),
        ).where(Call.tenant_id == tenant_id)
    ).one()
    return TenantMetrics(
        total_calls=row[0],
        completed=row[1] or 0,
        failed=row[2] or 0,
        flagged_for_review=row[3] or 0,
        average_qa_score=float(row[4]) if row[4] is not None else None,
    )
