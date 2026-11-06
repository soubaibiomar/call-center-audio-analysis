"""Model Lab/analysis receipts survive PostgreSQL and authorized HTTP reads."""

from sqlalchemy.orm import Session

from src.services.model_runs import ModelRun
from tests.api.test_api import fixture_report
from tests.integration.test_postgresql_persistence import add_report


def test_model_receipt_is_persisted_and_owner_scoped(api):
    client, token, _, _, _, tenant, _, _, admin, users = api
    report = fixture_report()
    report.model_runs = [
        ModelRun(
            provider="ollama",
            model_id="qwen-fixture:7b",
            model_version="qwen-fixture:7b",
            prompt_revision="synthetic-revision",
            schema_name="SummaryResult",
            attempt=2,
            retries=1,
            latency_ms=12,
            structured_output="valid",
        )
    ]
    with Session(admin) as session, session.begin():
        add_report(session, report, tenant, users["agent"])
    response = client.get(f"/api/v1/calls/{report.call_id}/report", headers=token())
    assert response.status_code == 200
    assert response.json()["model_runs"] == [report.model_runs[0].model_dump()]
    assert "audio_path" not in response.json()
    assert (
        client.get(f"/api/v1/calls/{report.call_id}/report", headers=token("peer")).status_code
        == 404
    )
