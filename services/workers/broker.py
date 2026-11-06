"""Redis delivery, with PostgreSQL outbox/redelivery as the recovery authority."""

from collections.abc import Callable
from datetime import timedelta
from typing import cast

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import Retries
from sqlalchemy import or_, select
from sqlalchemy.engine import Engine

from services.api.db.models import AnalysisJob
from services.workers.jobs import now
from services.workers.runner import JobRunner
from services.workers.settings import QueueSettings
from src.database.connection import session_scope


class QueueBroker:
    def __init__(self, settings: QueueSettings, runner: JobRunner) -> None:
        self.settings, self.runner = settings, runner
        constructor = cast(Callable[..., RedisBroker], RedisBroker)
        self.broker = constructor(
            url=settings.redis_url,
            namespace=settings.namespace,
            heartbeat_timeout=15000,
            middleware=[Retries(max_retries=0)],
        )
        # Application attempt budget/backoff is persisted in PG; do not multiply it
        # by Dramatiq inference retries. PG outbox also recovers delivery failures.
        self.actor = dramatiq.actor(
            broker=self.broker,
            actor_name=f"analyze_{runner.queue}",
            queue_name=f"analysis_{runner.queue}",
            max_retries=0,
        )(runner.run)

    def dispatch(self, engine: Engine) -> int:
        sent = 0
        for tenant in self.settings.tenants:
            with session_scope(engine, tenant_id=tenant) as session:
                jobs = session.scalars(
                    select(AnalysisJob)
                    .where(
                        AnalysisJob.tenant_id == tenant,
                        AnalysisJob.queue == self.runner.queue,
                        AnalysisJob.status.in_({"queued", "retrying", "running", "cancelling"}),
                        AnalysisJob.next_attempt_at <= now(),
                        or_(
                            AnalysisJob.last_published_at.is_(None),
                            AnalysisJob.last_published_at
                            < now() - timedelta(seconds=self.settings.republish_seconds),
                        ),
                    )
                    .order_by(AnalysisJob.created_at)
                    .limit(20)
                    .with_for_update(skip_locked=True)
                )
                for job in jobs:
                    self.actor.send(tenant, job.id)
                    job.last_published_at = now()
                    sent += 1
        return sent
