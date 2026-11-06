"""At-least-once delivery with one logical committed result per durable job."""

from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from services.api.analysis import analyze_call
from services.api.db.models import AnalysisJob, User
from services.workers.jobs import TERMINAL, lock_key, now, record_failure
from services.workers.settings import QueueSettings
from services.workers.storage import AudioStore, IntegrityError
from src.database.connection import session_scope
from src.database.scope import database_identity
from src.graph.state import CallReport
from src.services.contracts import AnalysisPort, AnalysisRequest
from src.services.job_execution import JobExecution, job_execution
from src.utils.audio_workspace import audio_workspace


class JobCancelledError(RuntimeError):
    pass


class JobRunner:
    def __init__(
        self,
        engine: Engine,
        storage: AudioStore,
        settings: QueueSettings,
        queue: str,
        factory: Callable[[], AnalysisPort],
    ) -> None:
        self.engine, self.storage, self.settings = engine, storage, settings
        self.queue, self.factory = queue, factory
        self.service: AnalysisPort | None = None

    def run(self, tenant: str, job_id: str) -> None:
        tenant, job_id = str(UUID(tenant)), str(UUID(job_id))
        if tenant not in self.settings.tenants:
            return
        # A dedicated session-level advisory lock survives short transaction commits.
        # Process death releases it; duplicates cannot execute concurrently.
        with self.engine.connect() as lock_connection:
            key = lock_key("execute:" + tenant + ":" + job_id)
            acquired = lock_connection.scalar(
                text("SELECT pg_try_advisory_lock(:key)"), {"key": key}
            )
            lock_connection.commit()
            if not acquired:
                return
            try:
                self._run_locked(tenant, job_id)
            finally:
                lock_connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})
                lock_connection.commit()

    def _run_locked(self, tenant: str, job_id: str) -> None:
        with session_scope(self.engine, tenant_id=tenant) as session:
            job = session.scalar(
                select(AnalysisJob).where(AnalysisJob.id == job_id).with_for_update()
            )
            if job is None or job.queue != self.queue or job.status in TERMINAL:
                return
            if job.status == "cancelling":
                job.status, job.finished_at = "cancelled", now()
                return
            if job.next_attempt_at > now():
                return
            if job.attempts >= job.max_attempts:
                job.status, job.error_code, job.finished_at = "failed", "attempts_exhausted", now()
                return
            user = session.scalar(select(User).where(User.id == job.owner_user_id))
            if (
                user is None
                or not user.enabled
                or user.role not in {"agent", "supervisor", "admin"}
            ):
                job.status, job.error_code, job.finished_at = "failed", "owner_disabled", now()
                return
            job.status, job.started_at = "running", now()
            job.attempts += 1
            owner, digest, size = job.owner_user_id, job.audio_sha256, job.audio_size
            caller, department = job.caller_id, job.department
            wait_ms = (now() - job.created_at).total_seconds() * 1000
            wait_ms = job.metrics.get("queue_wait_ms", wait_ms)
            job.metrics = {
                **job.metrics,
                "queue_wait_ms": wait_ms,
                "attempts": float(job.attempts),
                "retries": float(max(0, job.attempts - 1)),
            }
        start = perf_counter()

        def commit(session: Session, report: CallReport) -> None:
            job = session.scalar(
                select(AnalysisJob)
                .where(AnalysisJob.id == job_id, AnalysisJob.tenant_id == tenant)
                .with_for_update()
            )
            if job is None or job.status != "running":
                raise JobCancelledError("Job was cancelled before report commit")
            if str(report.call_id) != job_id:
                raise ValueError("Analysis returned an unexpected result identity")
            job.call_id, job.status, job.finished_at, job.error_code = (
                job_id,
                "finished",
                now(),
                None,
            )
            elapsed_ms = (perf_counter() - start) * 1000
            job.metrics = {
                **job.metrics,
                "queue_wait_ms": wait_ms,
                "execution_ms": elapsed_ms,
                "last_attempt_ms": elapsed_ms,
            }

        try:
            data = self.storage.get(tenant, job_id, digest, size)
            with (
                TemporaryDirectory(prefix="project28-worker-") as folder,
                database_identity(tenant, owner),
                audio_workspace(Path(folder)),
                job_execution(JobExecution(UUID(job_id), commit)),
            ):
                path = Path(folder) / "audio"
                path.write_bytes(data)
                if self.service is None:
                    self.service = self.factory()
                analyze_call(
                    self.service, AnalysisRequest(path, caller, department, downloads=False)
                )
            # A transport/service that omits persistence must never fake completion.
            with session_scope(self.engine, tenant_id=tenant) as session:
                state = session.scalar(select(AnalysisJob.status).where(AnalysisJob.id == job_id))
            if state != "finished":
                record_failure(self.engine, tenant, job_id, "report_not_committed", self.settings)
        except IntegrityError:
            record_failure(
                self.engine, tenant, job_id, "audio_integrity_failed", self.settings, permanent=True
            )
        except Exception:
            # Never store exception strings, SQL URLs, provider responses or transcript content.
            # If commit succeeded before an audit/response failure, terminal state wins.
            record_failure(self.engine, tenant, job_id, "analysis_failed", self.settings)
