"""Real object checksums, PostgreSQL transitions, Redis delivery and idempotency."""

import time
from concurrent.futures import ThreadPoolExecutor

import dramatiq
import pytest
from botocore.exceptions import ClientError
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from services.api.app import create_app
from services.api.settings import ApiSettings
from services.workers.broker import QueueBroker
from services.workers.jobs import owned_job, submit
from services.workers.runner import JobRunner
from src.agents.intake import run_intake
from src.agents.report import compile_report
from src.database.connection import session_scope
from src.database.models import CallRecord
from src.security.audit import AuditLogger
from src.services.analysis import AnalysisService
from tests.conftest import make_qa_scores, make_summary, make_transcription, make_wav_bytes


def factory(engine, *, fails=0, callback=None):
    class Workflow:
        def __init__(self):
            self.calls = 0

        def invoke(self, input):
            self.calls += 1
            if callback:
                callback()
            if self.calls <= fails:
                raise RuntimeError("synthetic inference failure")
            intake = run_intake(input["audio_input"])
            report = compile_report(
                intake,
                make_transcription(call_id=intake.call_id),
                make_summary(call_id=intake.call_id),
                make_qa_scores(call_id=intake.call_id),
                "synthetic-worker",
            )
            return {"status": "completed", "report": report}

    workflow = Workflow()
    return lambda: AnalysisService(workflow, engine, AuditLogger(engine=engine)), workflow


def create(jobs, key="request", queue="cpu"):
    engine, store, settings, identity = jobs
    return submit(engine, store, settings, identity, make_wav_bytes(0.1), key, queue)


def test_duplicate_and_conflicting_submission_and_admission(jobs):
    engine, store, settings, identity = jobs
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda _: create(jobs), range(3)))
    assert len({item.id for item in results}) == 1
    with pytest.raises(HTTPException) as conflict:
        submit(engine, store, settings, identity, make_wav_bytes(0.2), "request")
    assert conflict.value.status_code == 409
    create(jobs, "two")
    create(jobs, "three")
    assert create(jobs).id == results[0].id
    with pytest.raises(HTTPException) as full:
        create(jobs, "four")
    assert full.value.status_code == 429


def test_retry_then_finish_and_duplicate_delivery_produces_one_report(jobs):
    engine, store, settings, identity = jobs
    item = create(jobs)
    service, workflow = factory(engine, fails=1)
    runner = JobRunner(engine, store, settings, "cpu", service)
    runner.run(identity.tenant_id, str(item.id))
    first = owned_job(engine, identity, str(item.id))
    assert first.status == "retrying" and first.attempts == 1
    assert first.error_code == "analysis_failed" and first.metrics["last_attempt_ms"] >= 0
    time.sleep(0.03)
    runner.run(identity.tenant_id, str(item.id))
    runner.run(identity.tenant_id, str(item.id))
    result = owned_job(engine, identity, str(item.id))
    assert result.status == "finished" and result.attempts == 2
    assert workflow.calls == 2
    with session_scope(engine, tenant_id=identity.tenant_id) as session:
        assert (
            session.scalar(
                select(func.count())
                .select_from(CallRecord)
                .where(CallRecord.call_id == str(item.id))
            )
            == 1
        )


def test_exhausted_failure_is_terminal_and_persists_sanitized_metrics(jobs):
    engine, store, settings, identity = jobs
    item = create(jobs)
    service, workflow = factory(engine, fails=100)
    runner = JobRunner(engine, store, settings, "cpu", service)
    runner.run(identity.tenant_id, str(item.id))
    time.sleep(0.03)
    runner.run(identity.tenant_id, str(item.id))
    runner.run(identity.tenant_id, str(item.id))
    result = owned_job(engine, identity, str(item.id))
    assert result.status == "failed" and result.attempts == 2 and workflow.calls == 2
    assert result.error_code == "analysis_failed" and result.finished_at is not None
    assert result.metrics["retries"] == 1


def test_cancel_queued_and_inflight_rolls_back_report(jobs):
    engine, store, settings, identity = jobs
    queued = create(jobs)
    assert owned_job(engine, identity, str(queued.id), cancel=True).status == "cancelled"
    item = create(jobs, "running")
    service, _ = factory(
        engine, callback=lambda: owned_job(engine, identity, str(item.id), cancel=True)
    )
    runner = JobRunner(engine, store, settings, "cpu", service)
    runner.run(identity.tenant_id, str(item.id))
    assert owned_job(engine, identity, str(item.id)).status == "cancelled"
    with session_scope(engine, tenant_id=identity.tenant_id) as session:
        assert session.scalar(select(CallRecord).where(CallRecord.call_id == str(item.id))) is None


def test_integrity_tampering_is_permanent_failure_and_bucket_is_private(jobs):
    engine, store, settings, identity = jobs
    item = create(jobs)
    store.put(identity.tenant_id, str(item.id), b"changed bytes")
    service, workflow = factory(engine)
    JobRunner(engine, store, settings, "cpu", service).run(identity.tenant_id, str(item.id))
    result = owned_job(engine, identity, str(item.id))
    assert result.status == "failed" and result.error_code == "audio_integrity_failed"
    assert workflow.calls == 0
    with pytest.raises(ClientError):
        store.client.list_buckets()


def test_cpu_gpu_separation(jobs):
    engine, store, settings, identity = jobs
    item = create(jobs, queue="gpu")
    service, workflow = factory(engine)
    JobRunner(engine, store, settings, "cpu", service).run(identity.tenant_id, str(item.id))
    assert owned_job(engine, identity, str(item.id)).status == "queued"
    assert workflow.calls == 0


def test_http_upload_returns_owned_job_id_and_cancel_is_scoped(jobs, api, keys):
    engine, _, settings, identity = jobs
    client = TestClient(
        create_app(
            ApiSettings(
                issuer="https://identity.example.test", audience="project28-api", public_key=keys[1]
            ),
            engine,
            queue_settings=settings,
        )
    )
    headers = {**api[1](), "Idempotency-Key": "http-synthetic"}
    response = client.post(
        "/api/v1/jobs",
        headers=headers,
        files={"audio": ("../../invalid-name.wav", make_wav_bytes(0.1))},
    )
    assert response.status_code == 202, response.text
    job_id = response.json()["id"]
    assert response.json()["status"] == "queued" and response.json()["call_id"] is None
    assert client.get(f"/api/v1/jobs/{job_id}", headers=api[1]("peer")).status_code == 404
    assert client.post(f"/api/v1/jobs/{job_id}/cancel", headers=api[1]("peer")).status_code == 404
    assert (
        client.post(f"/api/v1/jobs/{job_id}/cancel", headers=api[1]()).json()["status"]
        == "cancelled"
    )


def test_actual_redis_dispatch_and_redelivery(jobs):
    engine, store, settings, identity = jobs
    item = create(jobs)
    service, workflow = factory(engine)
    queue = QueueBroker(settings, JobRunner(engine, store, settings, "cpu", service))
    worker = dramatiq.Worker(queue.broker, worker_threads=1)
    worker.start()
    try:
        assert queue.dispatch(engine) == 1
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if owned_job(engine, identity, str(item.id)).status == "finished":
                break
            time.sleep(0.05)
        assert owned_job(engine, identity, str(item.id)).status == "finished"
        queue.actor.send(identity.tenant_id, str(item.id))
        time.sleep(0.2)
        assert workflow.calls == 1
    finally:
        worker.stop(timeout=5000)
        queue.broker.close()


def test_killed_worker_restarts_and_commits_one_logical_result(jobs, tmp_path):
    import json
    import os
    import subprocess
    import sys
    from dataclasses import asdict

    engine, _, settings, identity = jobs
    item = create(jobs)
    config = tmp_path / "private_queue.json"
    config.write_text(json.dumps(asdict(settings)), encoding="utf-8")
    marker = tmp_path / "entered"
    temporary = tmp_path / "worker-temporary"
    temporary.mkdir()
    env = dict(
        os.environ,
        QUEUE_CONFIG_FILE=str(config),
        DATABASE_URL_FILE=os.environ["PROJECT28_TEST_APP_URL_FILE"],
        TMP=str(temporary),
        TEMP=str(temporary),
        PYTHONIOENCODING="utf-8",
    )
    env.pop("DATABASE_URL", None)
    command = [sys.executable, "-m", "tests.workers.restart_child", "--marker", str(marker)]
    with (tmp_path / "child.log").open("wb") as log:
        process = subprocess.Popen([*command, "--block"], env=env, stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline and not marker.exists():
                assert process.poll() is None
                time.sleep(0.1)
            assert marker.exists()
            assert owned_job(engine, identity, str(item.id)).status == "running"
            process.kill()
            process.wait(timeout=5)
            process = subprocess.Popen(command, env=env, stdout=log, stderr=log)
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                assert process.poll() is None
                if owned_job(engine, identity, str(item.id)).status == "finished":
                    break
                time.sleep(0.1)
            final = owned_job(engine, identity, str(item.id))
            assert final.status == "finished" and final.attempts == 2
            with session_scope(engine, tenant_id=identity.tenant_id) as session:
                assert (
                    session.scalar(
                        select(func.count())
                        .select_from(CallRecord)
                        .where(CallRecord.call_id == str(item.id))
                    )
                    == 1
                )
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)


def test_failure_after_commit_does_not_repeat_analysis(jobs):
    engine, store, settings, identity = jobs
    item = create(jobs)
    original_factory, workflow = factory(engine)

    class BrokenAudit:
        def log(self, **kwargs):
            raise RuntimeError("synthetic crash after report commit")

    service = original_factory()
    service.audit = BrokenAudit()
    runner = JobRunner(engine, store, settings, "cpu", lambda: service)
    runner.run(identity.tenant_id, str(item.id))
    runner.run(identity.tenant_id, str(item.id))
    assert owned_job(engine, identity, str(item.id)).status == "finished"
    assert workflow.calls == 1


def test_overlapping_duplicate_deliveries_do_not_execute_twice(jobs):
    from threading import Event

    engine, store, settings, identity = jobs
    item = create(jobs)
    entered, release = Event(), Event()

    def block():
        entered.set()
        assert release.wait(10)

    service, workflow = factory(engine, callback=block)
    runner = JobRunner(engine, store, settings, "cpu", service)
    with ThreadPoolExecutor(max_workers=2) as pool:
        active = pool.submit(runner.run, identity.tenant_id, str(item.id))
        try:
            assert entered.wait(10)
            runner.run(identity.tenant_id, str(item.id))
        finally:
            release.set()
        active.result(timeout=10)
    assert workflow.calls == 1
    assert owned_job(engine, identity, str(item.id)).status == "finished"


def test_broker_ack_gap_redelivers_without_duplicate_result(jobs, monkeypatch):
    engine, store, settings, identity = jobs
    item = create(jobs)
    service, workflow = factory(engine)
    queue = QueueBroker(settings, JobRunner(engine, store, settings, "cpu", service))
    original = queue.actor.send

    def ambiguous(*args):
        original(*args)
        raise ConnectionError("synthetic lost publication acknowledgement")

    monkeypatch.setattr(queue.actor, "send", ambiguous)
    with pytest.raises(ConnectionError):
        queue.dispatch(engine)
    assert owned_job(engine, identity, str(item.id)).status == "queued"
    monkeypatch.setattr(queue.actor, "send", original)
    assert queue.dispatch(engine) == 1
    worker = dramatiq.Worker(queue.broker, worker_threads=1)
    worker.start()
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if owned_job(engine, identity, str(item.id)).status == "finished":
                break
            time.sleep(0.05)
        assert owned_job(engine, identity, str(item.id)).status == "finished"
        time.sleep(0.2)
        assert workflow.calls == 1
    finally:
        worker.stop(timeout=5000)
        queue.broker.close()
