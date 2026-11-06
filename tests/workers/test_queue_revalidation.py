"""Real PostgreSQL/S3 reproductions for STEP10 queue review findings."""

import time
from dataclasses import replace

import pytest

from services.workers.jobs import owned_job
from services.workers.runner import JobRunner
from tests.workers.test_durable_jobs import create, factory


def test_valid_compact_tenant_allowlist_does_not_strand_job(jobs):
    engine, store, settings, identity = jobs
    settings = replace(settings, tenants=(identity.tenant_id.replace("-", "").upper(),))
    item = create(jobs)
    service, workflow = factory(engine)
    JobRunner(engine, store, settings, "cpu", service).run(identity.tenant_id, str(item.id))
    assert owned_job(engine, identity, str(item.id)).status == "finished"
    assert workflow.calls == 1


@pytest.mark.parametrize("failures", [0, 1])
def test_completed_job_keeps_current_attempt_metrics(jobs, failures):
    engine, store, settings, identity = jobs
    item = create(jobs)
    service, _ = factory(engine, fails=failures)
    runner = JobRunner(engine, store, settings, "cpu", service)
    runner.run(identity.tenant_id, str(item.id))
    if failures:
        assert owned_job(engine, identity, str(item.id)).status == "retrying"
        time.sleep(0.03)
        runner.run(identity.tenant_id, str(item.id))
    finished = owned_job(engine, identity, str(item.id))
    assert finished.status == "finished"
    assert finished.metrics.get("attempts") == failures + 1
    assert finished.metrics.get("retries") == failures
    assert finished.metrics.get("last_attempt_ms") == finished.metrics["execution_ms"]
