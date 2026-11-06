"""HTTP contracts, real RSA signatures and real restricted PostgreSQL sessions."""

import os
import time
from pathlib import Path
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from services.api.app import create_app
from services.api.db.models import ExternalIdentity, Job, Tenant, User
from services.api.settings import ApiSettings
from src.agents.report import compile_report
from src.database.connection import get_engine, session_scope
from src.database.scope import current_identity, database_identity
from src.graph.state import CallReport
from src.services.analysis import AnalysisService
from tests.conftest import (
    make_intake_result,
    make_qa_scores,
    make_summary,
    make_transcription,
    make_wav_bytes,
)
from tests.integration.test_postgresql_persistence import add_report


@pytest.fixture(scope="module")
def keys():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = (
        key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    return key, public


def fixture_report() -> CallReport:
    intake = make_intake_result()
    return compile_report(
        intake,
        make_transcription(call_id=intake.call_id),
        make_summary(call_id=intake.call_id),
        make_qa_scores(call_id=intake.call_id),
        "synthetic",
    )


def test_default_is_fail_closed_and_schema_is_public():
    client = TestClient(create_app(ApiSettings()))
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").status_code == 503
    assert client.get("/api/v1/calls").status_code == 503
    schema = client.get("/openapi.json").json()
    assert len(schema["paths"]) == 41
    assert schema["paths"]["/api/v1/calls"]["get"]["security"] == [{"HTTPBearer": []}]
    assert "ErrorResponse" in schema["components"]["schemas"]
    assert client.get("/docs").status_code == 404


@pytest.fixture
def api(keys):
    paths = [
        os.getenv(name) for name in ("PROJECT28_TEST_ADMIN_URL_FILE", "PROJECT28_TEST_APP_URL_FILE")
    ]
    if not all(paths):
        pytest.skip("Set private isolated PostgreSQL test URL files")
    admin = create_engine(Path(paths[0]).read_text().strip(), hide_parameters=True)
    runtime = get_engine(Path(paths[1]).read_text().strip())
    tenant, other = str(uuid4()), str(uuid4())
    users = {
        role: str(uuid4())
        for role in ("agent", "peer", "supervisor", "admin", "empty", "disabled", "service")
    }
    issuer = "https://identity.example.test"
    with Session(admin) as session, session.begin():
        session.add_all(
            [
                Tenant(id=tenant, name="Synthetic HTTP tests"),
                Tenant(id=other, name="Other synthetic tenant"),
            ]
        )
        session.flush()
        for role, user_id in users.items():
            session.add(
                User(
                    id=user_id,
                    tenant_id=tenant,
                    display_name="Synthetic",
                    role="agent" if role in {"peer", "empty", "disabled"} else role,
                    enabled=role != "disabled",
                )
            )
        session.flush()
        session.add_all(
            [
                ExternalIdentity(tenant_id=tenant, user_id=user_id, issuer=issuer, subject=role)
                for role, user_id in users.items()
            ]
        )
        report = fixture_report()
        add_report(session, report, tenant, users["agent"])
        peer_report = fixture_report()
        add_report(session, peer_report, tenant, users["peer"])
        job_id = str(uuid4())
        session.add(Job(id=job_id, tenant_id=tenant, call_id=str(report.call_id), status="queued"))

    class Workflow:
        def invoke(self, input):
            return {"status": "completed", "report": fixture_report()}

    class Audit:
        def log(self, **kwargs):
            assert current_identity().tenant_id == tenant

    settings = ApiSettings(issuer=issuer, audience="project28-api", public_key=keys[1])
    client = TestClient(
        create_app(settings, runtime, lambda: AnalysisService(Workflow(), runtime, Audit()))
    )

    def token(subject="agent", **overrides):
        now = int(time.time())
        claims = dict(
            iss=issuer, aud="project28-api", sub=subject, tenant_id=tenant, iat=now, exp=now + 300
        )
        claims.update(overrides)
        return {"Authorization": "Bearer " + jwt.encode(claims, keys[0], algorithm="RS256")}

    yield client, token, report, peer_report, job_id, tenant, other, runtime, admin, users
    client.close()
    runtime.dispose()
    admin.dispose()


@pytest.mark.parametrize(
    "claims",
    [
        {"exp": 1},
        {"aud": "other"},
        {"iss": "https://evil.example.test"},
        {"tenant_id": "not-uuid"},
        {"sub": ""},
        {"iat": 9999999999},
        {"exp": 9999999999},
        {"tenant_id": None},
        {"nbf": 9999999999},
    ],
)
def test_invalid_signed_tokens_denied(api, claims):
    client, token, *_ = api
    response = client.get("/api/v1/calls", headers=token(**claims))
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("subject", ["disabled", "missing", "service"])
def test_unmapped_disabled_service_denied(api, subject):
    client, token, *_ = api
    assert client.get("/api/v1/me", headers=token(subject)).status_code == 403


def test_unsigned_wrong_key_and_missing_denied(api):
    client, token, *_ = api
    valid = token()["Authorization"].split()[1]
    payload = jwt.decode(valid, options={"verify_signature": False})
    bad = jwt.encode(payload, "a" * 40, algorithm="HS256")
    for headers in (
        {},
        {"Authorization": "Bearer " + bad},
        {"Authorization": "Bearer invalid"},
        {"Authorization": "Basic abc"},
        {"Authorization": "Bearer " + "x" * 16385},
    ):
        assert (
            client.post("/api/v1/calls/analyze", headers=headers, content=b"invalid").status_code
            == 401
        )
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    bad = jwt.encode(payload, other_key, algorithm="RS256")
    assert client.get("/api/v1/me", headers={"Authorization": "Bearer " + bad}).status_code == 401


def test_ownership_tenant_and_database_role(api):
    client, token, report, peer, job_id, tenant, other, runtime, admin, users = api
    own = token()
    assert client.get("/ready").status_code == 200
    assert client.get("/api/v1/calls", headers=own).json()["total"] == 1
    assert client.get("/api/v1/dashboard", headers=own).json()["total_calls"] == 1
    assert client.get("/api/v1/dashboard", headers=token("supervisor")).json()["total_calls"] == 2
    for suffix in ("", "/transcript", "/qa", "/report", "/report.pdf"):
        assert client.get(f"/api/v1/calls/{report.call_id}{suffix}", headers=own).status_code == 200
        assert client.get(f"/api/v1/calls/{peer.call_id}{suffix}", headers=own).status_code == 404
    assert (
        client.get(f"/api/v1/calls/{peer.call_id}", headers=token(roles=["admin"])).status_code
        == 404
    )
    assert (
        client.get(f"/api/v1/calls/{peer.call_id}", headers=token("supervisor")).status_code == 200
    )
    assert client.get("/api/v1/me", headers=token(tenant_id=other)).status_code == 403
    assert client.get(f"/api/v1/jobs/{job_id}", headers=own).json()["progress"] is None
    assert client.get(f"/api/v1/jobs/{job_id}", headers=token("peer")).status_code == 404
    public = client.get(f"/api/v1/calls/{report.call_id}/report", headers=own).json()
    assert "intake" not in public and "trace_id" not in public
    with session_scope(runtime, tenant_id=other) as session:
        assert session.scalar(select(ExternalIdentity)) is None


@pytest.mark.parametrize(
    "url",
    [
        "/api/v1/calls?limit=0",
        "/api/v1/calls?limit=101",
        "/api/v1/calls?offset=-1",
        "/api/v1/calls/not-uuid",
    ],
)
def test_invalid_inputs_are_sanitized(api, url):
    client, token, *_ = api
    response = client.get(url, headers=token())
    assert response.status_code == 422
    assert set(response.json()["error"]) == {"code", "message", "request_id", "retryable"}
    assert "not-uuid" not in response.text


def test_upload_executes_shared_pipeline_and_persists_current_owner(api):
    client, token, *_ = api
    response = client.post(
        "/api/v1/calls/analyze",
        headers=token(),
        files={"audio": ("../../untrusted.wav", make_wav_bytes(0.1))},
    )
    assert response.status_code == 201, response.text
    call_id = response.json()["call_id"]
    assert client.get(f"/api/v1/calls/{call_id}/report", headers=token()).status_code == 200
    assert client.get(f"/api/v1/calls/{call_id}", headers=token("peer")).status_code == 404
    assert client.get("/api/v1/calls", headers=token()).json()["total"] == 2
    assert current_identity() is None


def test_bad_and_oversize_uploads(api):
    client, token, *_ = api
    assert (
        client.post(
            "/api/v1/calls/analyze", headers=token(), files={"audio": ("secret.txt", b"not audio")}
        ).status_code
        == 415
    )
    assert client.post("/api/v1/calls/analyze", headers=token()).status_code == 422
    settings = ApiSettings(
        issuer="https://identity.example.test",
        audience="project28-api",
        public_key=client.app.user_middleware[0].kwargs["auth"].settings.public_key,
        max_upload_bytes=100,
    )
    small = TestClient(create_app(settings, api[7]))
    assert (
        small.post(
            "/api/v1/calls/analyze",
            headers=token(),
            files={"audio": ("test.wav", make_wav_bytes(0.1))},
        ).status_code
        == 413
    )
    assert (
        small.post("/api/v1/calls/analyze", headers=token(), content=b"a" * 66000).status_code
        == 413
    )


def test_request_local_scope_resets_after_failure():
    assert current_identity() is None
    with pytest.raises(RuntimeError), database_identity("tenant", "owner"):
        assert current_identity().tenant_id == "tenant"
        raise RuntimeError("synthetic")
    assert current_identity() is None


def test_disabled_user_revocation_applies_to_existing_token(api):
    client, token, _, _, _, _, _, _, admin, users = api
    headers = token()
    assert client.get("/api/v1/me", headers=headers).status_code == 200
    with Session(admin) as session, session.begin():
        user = session.get(User, users["agent"])
        user.enabled = False
    assert client.get("/api/v1/me", headers=headers).status_code == 403


def test_operator_link_is_idempotent_and_runtime_cannot_reassign(api):
    from sqlalchemy.exc import DBAPIError

    from services.api.provision_identity import link_identity

    client, token, _, _, _, tenant, _, runtime, admin, users = api
    issuer = "https://identity.example.test"
    link_identity(admin, tenant, users["agent"], issuer, "linked")
    link_identity(admin, tenant, users["agent"], issuer, "linked")
    assert client.get("/api/v1/me", headers=token("linked")).status_code == 200
    with pytest.raises(ValueError, match="reassign"):
        link_identity(admin, tenant, users["peer"], issuer, "linked")
    with pytest.raises(DBAPIError):
        link_identity(runtime, tenant, users["agent"], issuer, "blocked")


def test_failed_analysis_is_sanitized_and_releases_gate(api, keys):
    client, token, *_ = api

    def broken():
        raise RuntimeError("private provider credential and path")

    settings = ApiSettings(
        issuer="https://identity.example.test", audience="project28-api", public_key=keys[1]
    )
    failed = TestClient(create_app(settings, api[7], broken))
    for _ in range(2):
        response = failed.post(
            "/api/v1/calls/analyze",
            headers=token(),
            files={"audio": ("test.wav", make_wav_bytes(0.1))},
        )
        assert response.status_code == 502
        assert "private" not in response.text
        assert current_identity() is None


def test_concurrent_analysis_returns_busy(api, keys):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from src.services.contracts import PipelineResult

    _, token, *_ = api
    entered, release = Event(), Event()

    class Slow:
        def analyze(self, request):
            entered.set()
            assert release.wait(10)
            return PipelineResult(success=True, report=fixture_report())

    settings = ApiSettings(
        issuer="https://identity.example.test", audience="project28-api", public_key=keys[1]
    )
    client = TestClient(create_app(settings, api[7], Slow))

    def upload():
        return client.post(
            "/api/v1/calls/analyze",
            headers=token(),
            files={"audio": ("test.wav", make_wav_bytes(0.1))},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(upload)
        try:
            assert entered.wait(10)
            response = upload()
            assert response.status_code == 429
            assert response.headers["Retry-After"] == "1"
        finally:
            release.set()
        assert first.result().status_code == 201


def test_pinned_jwks_key_verifies_and_unavailable_keys_fail_closed(api, keys, monkeypatch):
    from types import SimpleNamespace

    from fastapi import HTTPException
    from jwt.exceptions import PyJWKClientConnectionError

    from services.api.auth import Authenticator

    _, token, *_ = api
    settings = ApiSettings(
        issuer="https://identity.example.test",
        audience="project28-api",
        jwks_url="https://identity.example.test/jwks.json",
    )
    auth = Authenticator(settings, api[7])
    headers = token()
    original = headers["Authorization"].split()[1]
    claims = jwt.decode(original, options={"verify_signature": False})
    signed = jwt.encode(claims, keys[0], algorithm="RS256", headers={"kid": "fixture-key"})
    monkeypatch.setattr(
        auth.jwks,
        "get_signing_key_from_jwt",
        lambda value: SimpleNamespace(key=keys[0].public_key()),
    )
    assert auth.authenticate("Bearer " + signed).role == "agent"

    def unavailable(value):
        raise PyJWKClientConnectionError("private URL detail")

    monkeypatch.setattr(auth.jwks, "get_signing_key_from_jwt", unavailable)
    with pytest.raises(HTTPException) as exc:
        auth.authenticate("Bearer " + signed)
    assert exc.value.status_code == 503


def test_chunked_body_limit_has_no_content_length(api, keys):
    _, token, *_ = api
    settings = ApiSettings(
        issuer="https://identity.example.test",
        audience="project28-api",
        public_key=keys[1],
        max_upload_bytes=100,
    )
    client = TestClient(create_app(settings, api[7]))
    body = b'--boundary\r\nContent-Disposition: form-data; name="audio"; filename="a.wav"\r\n\r\n'
    headers = {**token(), "Content-Type": "multipart/form-data; boundary=boundary"}
    response = client.post(
        "/api/v1/calls/analyze",
        headers=headers,
        content=iter([body, b"a" * 66000, b"\r\n--boundary--\r\n"]),
    )
    assert response.status_code == 413


def test_empty_state_and_admin_scope(api):
    client, token, *_ = api
    assert client.get("/api/v1/calls", headers=token("empty")).json()["items"] == []
    empty = client.get("/api/v1/dashboard", headers=token("empty")).json()
    assert empty["total_calls"] == 0 and empty["average_qa_score"] is None
    assert client.get("/api/v1/calls", headers=token("admin")).json()["total"] == 2


@pytest.mark.parametrize(
    "config",
    [
        {"issuer": "http://insecure.test"},
        {"issuer": "https:"},
        {"jwks_url": "http://insecure.test/keys"},
        {"jwks_url": "https://user:password@example.test/keys"},  # pragma: allowlist secret
        {"max_upload_bytes": 0},
        {"tenant_claim": ""},
    ],
)
def test_invalid_configuration_is_rejected(config):
    with pytest.raises(ValueError):
        ApiSettings(**config)


def test_pdf_treats_untrusted_markup_as_text(monkeypatch):
    from reportlab.lib import utils

    from src.agents.report import generate_report_pdf

    def deny_image(*args, **kwargs):
        raise AssertionError("Untrusted report markup attempted image access")

    monkeypatch.setattr(utils, "ImageReader", deny_image)
    report = fixture_report()
    markup = '<img src="https://private.invalid/image"/> < & malformed'
    report.summary.call_purpose = markup
    report.summary.sentiment_trajectory = markup
    report.qa_scores.empathy.justification = markup
    assert generate_report_pdf(report).startswith(b"%PDF")


def test_generated_openapi_matches_factory():
    import json

    path = Path(__file__).resolve().parents[2] / "docs/api/openapi.json"
    assert json.loads(path.read_text(encoding="utf-8")) == create_app(ApiSettings()).openapi()
