"""Authoritative PostgreSQL job lifecycle and admission control."""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.engine import Engine

from services.api.auth import Principal
from services.api.db.models import AnalysisJob
from services.api.schemas import JobStatus
from services.workers.settings import QueueSettings
from services.workers.storage import AudioStore
from src.database.connection import session_scope

TERMINAL = {"finished", "failed", "cancelled"}


def now() -> datetime:
    return datetime.now(UTC)


def lock_key(value: str) -> int:
    return int.from_bytes(hashlib.sha256(value.encode()).digest()[:8], "big", signed=True)


def view(job: AnalysisJob) -> JobStatus:
    return JobStatus.model_validate(job, from_attributes=True)


def owned_job(
    engine: Engine, identity: Principal, job_id: str, *, cancel: bool = False
) -> JobStatus | None:
    with session_scope(engine, tenant_id=identity.tenant_id) as session:
        query = select(AnalysisJob).where(
            AnalysisJob.id == job_id, AnalysisJob.tenant_id == identity.tenant_id
        )
        if identity.owner_filter:
            query = query.where(AnalysisJob.owner_user_id == identity.owner_filter)
        job = session.scalar(query.with_for_update() if cancel else query)
        if job is None:
            return None
        if cancel and job.status not in TERMINAL:
            job.status = "cancelling" if job.status in {"running", "cancelling"} else "cancelled"
            if job.status == "cancelled":
                job.finished_at = now()
        return view(job)


def submit(
    engine: Engine,
    storage: AudioStore,
    settings: QueueSettings,
    identity: Principal,
    data: bytes,
    idempotency_key: str,
    queue: str = "cpu",
    caller_id: str | None = None,
    department: str | None = None,
) -> JobStatus:
    digest = hashlib.sha256(data).hexdigest()
    fingerprint = hashlib.sha256(
        json.dumps([digest, queue, caller_id, department], separators=(",", ":")).encode()
    ).hexdigest()
    with session_scope(engine, tenant_id=identity.tenant_id) as session:
        # Serialize admission per tenant; duplicate keys remain stable at full capacity.
        session.execute(
            text("SELECT pg_advisory_xact_lock(:key)"),
            {"key": lock_key("admission:" + identity.tenant_id)},
        )
        existing = session.scalar(
            select(AnalysisJob).where(
                AnalysisJob.tenant_id == identity.tenant_id,
                AnalysisJob.owner_user_id == identity.user_id,
                AnalysisJob.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            if existing.fingerprint != fingerprint:
                raise HTTPException(409)
            return view(existing)
        pending = (
            session.scalar(
                select(func.count())
                .select_from(AnalysisJob)
                .where(
                    AnalysisJob.tenant_id == identity.tenant_id, AnalysisJob.status.not_in(TERMINAL)
                )
            )
            or 0
        )
        if pending >= settings.capacity:
            raise HTTPException(429)
        job_id = str(uuid4())
        storage.put(identity.tenant_id, job_id, data)
        job = AnalysisJob(
            id=job_id,
            tenant_id=identity.tenant_id,
            owner_user_id=identity.user_id,
            idempotency_key=idempotency_key,
            fingerprint=fingerprint,
            audio_sha256=digest,
            audio_size=len(data),
            queue=queue,
            caller_id=caller_id,
            department=department,
            max_attempts=settings.max_attempts,
        )
        session.add(job)
        session.flush()
        return view(job)


def record_failure(
    engine: Engine,
    tenant: str,
    job_id: str,
    code: str,
    settings: QueueSettings,
    *,
    permanent: bool = False,
) -> None:
    with session_scope(engine, tenant_id=tenant) as session:
        job = session.scalar(select(AnalysisJob).where(AnalysisJob.id == job_id).with_for_update())
        if job is None or job.status in TERMINAL:
            return
        job.metrics = {
            **job.metrics,
            "attempts": float(job.attempts),
            "retries": float(max(0, job.attempts - 1)),
            "last_attempt_ms": max(
                0, (now() - (job.started_at or job.created_at)).total_seconds() * 1000
            ),
        }
        if job.status == "cancelling":
            job.status, job.finished_at = "cancelled", now()
            return
        job.error_code = code
        job.last_published_at = None
        if permanent or job.attempts >= job.max_attempts:
            job.status, job.finished_at = "failed", now()
        else:
            job.status = "retrying"
            job.next_attempt_at = now() + timedelta(
                seconds=min(300, settings.backoff_seconds * 2 ** max(0, job.attempts - 1))
            )
