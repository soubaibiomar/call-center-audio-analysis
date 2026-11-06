"""Independent edge-case regressions for STEP_09 correction review."""

import importlib.util
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations

from services.api.app import create_app
from services.api.settings import ApiSettings
from src.agents.intake import run_intake
from src.services.analysis import AnalysisService
from tests.conftest import make_wav_bytes


@pytest.mark.parametrize("tenant", [17, {}, []])
def test_non_string_signed_tenant_is_unauthenticated(api, tenant):
    client, token, *_ = api
    response = client.get("/api/v1/me", headers=token(tenant_id=tenant))
    assert response.status_code == 401


@pytest.mark.parametrize("path", ["/api/v1/calls/not-a-uuid", f"/api/v1/calls/{uuid4()}"])
def test_error_request_id_is_single_and_matches_body(api, path):
    client, token, *_ = api
    response = client.get(path, headers=token())
    assert response.status_code in {404, 422}
    assert response.headers.get_list("x-request-id") == [response.json()["error"]["request_id"]]
    UUID(response.headers["x-request-id"])
    assert response.headers.get_list("cache-control") == ["no-store"]


@pytest.mark.parametrize("raises", [False, True])
def test_failed_graph_does_not_leave_intake_audio(api, keys, raises):
    from fastapi.testclient import TestClient
    from langgraph.graph import END, START, StateGraph

    created = []

    def intake_failure(input):
        intake = run_intake(input["audio_input"])
        assert intake.validation_passed
        created.append(Path(intake.audio_path))
        assert created[-1].exists()
        if raises:
            raise RuntimeError("synthetic graph failure after intake")
        return {"status": "failed", "error": "synthetic graph failure", "intake": intake}

    graph = StateGraph(dict)
    graph.add_node("intake_failure", intake_failure)
    graph.add_edge(START, "intake_failure")
    graph.add_edge("intake_failure", END)
    workflow = graph.compile()

    class Audit:
        def log(self, **kwargs):
            pass

    _, token, *_ = api
    app = create_app(
        ApiSettings(
            issuer="https://identity.example.test", audience="project28-api", public_key=keys[1]
        ),
        api[7],
        lambda: AnalysisService(workflow, api[7], Audit()),
    )
    response = TestClient(app).post(
        "/api/v1/calls/analyze",
        headers=token(),
        files={"audio": ("sample.wav", make_wav_bytes(0.1))},
    )
    try:
        assert response.status_code == 502
        assert len(created) == 1
        assert not created[0].exists(), "Failed graph left its owned intake copy on disk"
    finally:
        # Only synthetic paths created by this test; never sweep the OS temp directory.
        for path in created:
            path.unlink(missing_ok=True)


def test_identity_downgrade_cannot_erase_rows_hidden_by_rls(api):
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    admin = api[8]
    suffix = uuid4().hex
    role, schema = f"review_owner_{suffix}", f"review_schema_{suffix}"
    source = Path("migrations/versions/0002_external_identities.py")
    spec = importlib.util.spec_from_file_location("review_identity_migration", source)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    # All roles/schema/rows/DDL are transaction-local and rolled back, including on failure.
    with admin.connect() as connection:
        transaction = connection.begin()
        try:
            connection.exec_driver_sql(f'CREATE ROLE "{role}" NOLOGIN NOBYPASSRLS')
            connection.exec_driver_sql(f'CREATE SCHEMA "{schema}" AUTHORIZATION "{role}"')
            connection.exec_driver_sql(f'SET LOCAL search_path TO "{schema}"')
            connection.exec_driver_sql(
                "CREATE TABLE external_identities(id text, tenant_id text, user_id text)"
            )
            for field in ("tenant_id", "user_id"):
                connection.exec_driver_sql(
                    f"CREATE INDEX ix_external_identities_{field} ON external_identities({field})"
                )
            connection.exec_driver_sql(
                "INSERT INTO external_identities VALUES ('synthetic','other-tenant','synthetic')"
            )
            connection.exec_driver_sql("ALTER TABLE external_identities ENABLE ROW LEVEL SECURITY")
            connection.exec_driver_sql("ALTER TABLE external_identities FORCE ROW LEVEL SECURITY")
            connection.exec_driver_sql(f'ALTER TABLE external_identities OWNER TO "{role}"')
            connection.exec_driver_sql(f'SET LOCAL ROLE "{role}"')
            assert connection.scalar(text("SELECT count(*) FROM external_identities")) == 0
            with pytest.raises((DBAPIError, RuntimeError)), connection.begin_nested():
                with Operations.context(MigrationContext.configure(connection)):
                    migration.downgrade()
            connection.exec_driver_sql("RESET ROLE")
            assert connection.scalar(text("SELECT count(*) FROM external_identities")) == 1
        finally:
            transaction.rollback()


def test_audio_workspace_resets_and_legacy_intake_still_works(tmp_path):
    from src.graph.state import AudioInput
    from src.utils.audio_workspace import audio_workspace, current_audio_workspace

    assert current_audio_workspace() is None
    with pytest.raises(RuntimeError), audio_workspace(tmp_path):
        assert current_audio_workspace() == tmp_path
        raise RuntimeError("synthetic")
    assert current_audio_workspace() is None
    intake = run_intake(AudioInput(audio_data=make_wav_bytes(0.1), filename="synthetic.wav"))
    try:
        assert intake.validation_passed and Path(intake.audio_path).exists()
        assert Path(intake.audio_path).parent != tmp_path
    finally:
        Path(intake.audio_path).unlink(missing_ok=True)
