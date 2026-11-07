"""Loopback-only synthetic STEP_23 preview, never a production identity provider."""

import asyncio
import json
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import jwt
import uvicorn
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from ml.emotion.contracts import EmotionResult, EmotionSignal
from services.api.app import create_app
from services.api.db.models import ExternalIdentity, Job, ModelVersion, Tenant, User
from services.api.settings import ApiSettings
from services.knowledge.grounding import PolicyAnswer, PolicyEvidence
from src.database.connection import get_engine
from src.graph.state import ActionItem, ComplianceFlag, TranscriptionSegment
from src.services.model_runs import ModelRun
from tests.api.test_api import fixture_report
from tests.conftest import make_wav_bytes
from tests.integration.test_postgresql_persistence import add_report


def main() -> None:
    step = os.getenv("PROJECT28_PREVIEW_STEP", "23")
    port = int(os.getenv("PROJECT28_PREVIEW_PORT", "8784"))
    if step not in {"23", "24", "25", "26"} or port not in {8784, 8786, 8788, 8790}:
        raise ValueError("Unsupported isolated preview")
    admin_url = Path(os.environ["PROJECT28_TEST_ADMIN_URL_FILE"]).read_text().strip()
    runtime_url = Path(os.environ["PROJECT28_TEST_APP_URL_FILE"]).read_text().strip()
    owner, app_url = make_url(admin_url), make_url(runtime_url)
    if (
        not owner.database
        or "test" not in owner.database
        or owner.database != app_url.database
        or owner.host != "127.0.0.1"
        or app_url.host != "127.0.0.1"
    ):
        raise RuntimeError("Preview requires matching, explicitly isolated loopback test databases")
    admin = create_engine(owner, hide_parameters=True)
    runtime = get_engine(runtime_url)
    tenant = str(uuid4())
    users = {role: str(uuid4()) for role in ["admin", "supervisor", "agent", "empty"]}
    issuer, audience = "https://workspace-fixture.example.test", "step23"
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = (
        key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    ids = []
    source = Path(f".local/step{step}-synthetic.wav")
    source.write_bytes(make_wav_bytes(4))
    job_id = str(uuid4())
    with Session(admin) as session, session.begin():
        session.add(Tenant(id=tenant, name="STEP23 synthetic validation"))
        session.flush()
        for role, user_id in users.items():
            session.add(
                User(
                    id=user_id,
                    tenant_id=tenant,
                    display_name="Synthetic validation account",
                    role="agent" if role == "empty" else role,
                    enabled=True,
                )
            )
        session.flush()
        for role, user_id in users.items():
            session.add(
                ExternalIdentity(tenant_id=tenant, user_id=user_id, issuer=issuer, subject=role)
            )
        session.add(
            ModelVersion(
                id=str(uuid4()),
                tenant_id=tenant,
                family="synthetic-validation",
                version="fixture-not-trained",
                status="candidate",
            )
        )
        for index, language in enumerate(["ary", "fr", "ar"]):
            report = fixture_report()
            ids.append(str(report.call_id))
            report.processed_at = datetime.now(UTC) - timedelta(days=index)
            report.intake.audio_properties.duration_seconds = 4
            report.transcription.segments = [
                TranscriptionSegment(
                    text="Synthetic opening for playback verification.",
                    start_time=0,
                    end_time=1,
                    speaker="Agent",
                    confidence=0.9,
                    low_confidence=False,
                ),
                TranscriptionSegment(
                    text="Synthetic evidence requiring review.",
                    start_time=1.25,
                    end_time=2.5,
                    speaker="Customer",
                    confidence=0.5,
                    low_confidence=True,
                ),
            ]
            report.transcription.full_text = " ".join(s.text for s in report.transcription.segments)
            report.summary.call_purpose = (
                "Synthetic call analysis fixture — not an operational result"
            )
            report.summary.key_discussion_points = [
                "Fictional support scenario",
                "Playback and citation validation",
            ]
            report.summary.action_items = [
                ActionItem(description="Review this synthetic evidence", owner="agent")
            ]
            report.qa_scores.compliance_flags = [
                ComplianceFlag(
                    violation="Synthetic review flag",
                    severity="medium",
                    transcript_reference=report.transcription.segments[1].text,
                )
            ]
            report.qa_scores.policy_evidence = PolicyAnswer(
                status="supported",
                answer="Synthetic policy example.",
                sources=[
                    PolicyEvidence(
                        source_id="synthetic-policy-v1",
                        passage="Synthetic policy example.",
                        effective_date=datetime.now(UTC) - timedelta(days=1),
                    )
                ],
            )
            report.acoustic_emotion = EmotionResult(
                status="completed",
                signals=[
                    EmotionSignal(
                        start=1.25,
                        end=2.5,
                        label="Unknown",
                        reason="Synthetic uncertain observation",
                        model_id="synthetic-fixture",
                    )
                ],
            )
            report.model_runs = [
                ModelRun(
                    provider="synthetic",
                    model_id="fixture-no-inference",
                    model_version="fixture-only",
                    prompt_revision="fixture-v1",
                    schema_name="Fixture",
                    attempt=1,
                    retries=0,
                    latency_ms=0,
                    structured_output="valid",
                )
            ]
            report.status = "flagged_for_review" if index == 0 else "completed"
            call = add_report(session, report, tenant, users["agent"])
            call.language = language
        session.add(Job(id=job_id, tenant_id=tenant, call_id=ids[0], status="queued", attempts=0))
    now = int(time.time())
    tokens = {
        role: jwt.encode(
            dict(iss=issuer, aud=audience, sub=role, tenant_id=tenant, iat=now, exp=now + 3600),
            key,
            algorithm="RS256",
        )
        for role in users
    }
    Path(f".local/step{step}-ui-context.json").write_text(
        json.dumps(
            dict(tokens=tokens, call_ids=ids, job_id=job_id, source=str(source), tenant=tenant)
        ),
        encoding="utf-8",
    )
    app = create_app(
        ApiSettings(issuer=issuer, audience=audience, public_key=public, synthetic_data=True),
        runtime,
    )
    if os.name == "nt" and step in {"25", "26"}:
        # Avoid Windows Proactor shutdown callbacks when a browser drops a socket.
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    uvicorn.run(
        app, host="127.0.0.1", port=port, log_level="warning", ws_max_size=65536, ws_max_queue=8
    )


if __name__ == "__main__":
    main()
