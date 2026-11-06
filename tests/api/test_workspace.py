from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from ml.emotion.contracts import EmotionResult
from services.api.app import create_app
from services.api.db.models import Call, ModelVersion
from services.api.schemas import Report
from services.api.settings import ApiSettings
from src.database.models import CallRecord
from tests.api.test_api import fixture_report


def test_shared_report_conversion_withholds_real_emotion_by_default():
    report = fixture_report()
    report.acoustic_emotion = EmotionResult(status="completed")
    assert Report.from_report(report).acoustic_emotion is None
    assert Report.from_report(report, include_synthetic_emotion=True).acoustic_emotion is not None


def test_activity_respects_tenant_owner_and_utc_window(api):
    client, token, report, peer, _, tenant, _, _, admin, _ = api
    with Session(admin) as session, session.begin():
        own = session.get(Call, str(report.call_id))
        other = session.get(Call, str(peer.call_id))
        own.processed_at = datetime.now(UTC)
        other.processed_at = datetime.now(UTC)
        own.language, other.language = "ary", "fr"
    agent = client.get("/api/v1/dashboard/activity?days=7", headers=token())
    assert agent.status_code == 200
    value = agent.json()
    assert len(value["days"]) == 7 and sum(day["calls"] for day in value["days"]) == 1
    assert value["scope"] == "owned_calls" and value["timezone"] == "UTC"
    assert value["languages"] == [{"language": "ary", "calls": 1}]
    supervisor = client.get("/api/v1/dashboard/activity?days=7", headers=token("supervisor")).json()
    assert sum(day["calls"] for day in supervisor["days"]) == 2
    assert sum(language["calls"] for language in supervisor["languages"]) == 2
    assert client.get("/api/v1/dashboard/activity?days=91", headers=token()).status_code == 422


def test_call_filters_and_sort_are_server_scoped(api):
    client, token, report, peer, _, _, _, _, admin, _ = api
    with Session(admin) as session, session.begin():
        own, other = session.get(Call, str(report.call_id)), session.get(Call, str(peer.call_id))
        own.language, other.language = "ary", "fr"
        own.qa_score, other.qa_score = 2.0, 4.0
        other.status = "failed"
    result = client.get(
        "/api/v1/calls?sort=qa_score&direction=asc", headers=token("supervisor")
    ).json()
    assert [row["qa_score"] for row in result["items"]] == [2.0, 4.0]
    result = client.get(
        "/api/v1/calls?language=fr&status=failed", headers=token("supervisor")
    ).json()
    assert result["total"] == 1 and result["items"][0]["id"] == str(peer.call_id)
    assert client.get("/api/v1/calls?language=fr", headers=token()).json()["total"] == 0
    assert client.get("/api/v1/calls?sort=audio_object_key", headers=token()).status_code == 422
    assert client.get("/api/v1/calls?direction=invalid", headers=token()).status_code == 422


def test_registry_is_admin_only_and_omits_artifact_locations(api):
    client, token, _, _, _, tenant, other, _, admin, _ = api
    with Session(admin) as session, session.begin():
        for owner in (tenant, other):
            session.add(
                ModelVersion(
                    id=str(uuid4()),
                    tenant_id=owner,
                    family="synthetic",
                    version="fixture-only",
                    artifact_uri="private://not-exposed",
                )
            )
    assert client.get("/api/v1/model-versions", headers=token("supervisor")).status_code == 403
    response = client.get("/api/v1/model-versions", headers=token("admin"))
    assert response.status_code == 200 and len(response.json()["items"]) == 1
    assert "private://" not in response.text and "artifact_uri" not in response.text


def test_context_is_authenticated_and_emotion_remains_synthetic_only(api, keys):
    client, token, report, _, _, _, _, runtime, admin, _ = api
    report.acoustic_emotion = EmotionResult(status="completed")
    with Session(admin) as session, session.begin():
        record = session.scalar(select(CallRecord).where(CallRecord.call_id == str(report.call_id)))
        record.report_json = report.model_dump_json()
    assert client.get("/api/v1/workspace-context").status_code == 401
    assert (
        client.get("/api/v1/workspace-context", headers=token()).json()["data_kind"]
        == "stored_records"
    )
    assert (
        client.get(f"/api/v1/calls/{report.call_id}/report", headers=token()).json()[
            "acoustic_emotion"
        ]
        is None
    )
    with TestClient(
        create_app(
            ApiSettings(
                issuer="https://identity.example.test",
                audience="project28-api",
                public_key=keys[1],
                synthetic_data=True,
            ),
            runtime,
        )
    ) as preview:
        assert (
            preview.get("/api/v1/workspace-context", headers=token()).json()["data_kind"]
            == "synthetic_validation"
        )
        result = preview.get(f"/api/v1/calls/{report.call_id}/report", headers=token()).json()
        assert result["acoustic_emotion"]["status"] == "completed"
        assert result["duration_seconds"] == report.intake.audio_properties.duration_seconds
