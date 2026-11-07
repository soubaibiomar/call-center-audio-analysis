"""Ephemeral signed synthetic preview. Credentials remain in ignored local files."""

import hashlib
import json
import os
import time
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
from services.api.auth import Principal
from services.api.db.models import ExternalIdentity, Tenant, User
from services.api.settings import ApiSettings
from services.reviews.contracts import Enrollment
from services.reviews.service import enroll
from src.database.connection import get_engine, session_scope
from tests.api.test_api import fixture_report
from tests.emotion.test_baseline import audio
from tests.integration.test_postgresql_persistence import add_report

admin_url = (
    Path(os.getenv("PROJECT28_TEST_ADMIN_URL_FILE", ".local/step08_test_admin_url"))
    .read_text()
    .strip()
)
if "test" not in (make_url(admin_url).database or ""):
    raise RuntimeError("Synthetic preview requires an isolated test database")
admin = create_engine(admin_url, hide_parameters=True)
runtime = get_engine(
    Path(os.getenv("PROJECT28_TEST_APP_URL_FILE", ".local/step08_test_app_url")).read_text().strip()
)
tenant = str(uuid4())
users = {role: str(uuid4()) for role in ["admin", "reviewerA", "reviewerB"]}
issuer = "https://synthetic-review.example.test"
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public = (
    key.public_key()
    .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    .decode()
)
data = audio()
source = Path(".local/step21-synthetic-review.wav")
source.write_bytes(data)
report = fixture_report()
report.acoustic_emotion = EmotionResult(
    status="completed",
    signals=[
        EmotionSignal(
            start=0,
            end=1,
            speaker_id="synthetic",
            label="angry",
            confidence=0.8,
            probabilities=dict(angry=0.8, neutral=0.1, happy=0.05, sad=0.05),
            model_id="synthetic-preview-fixture",
            model_revision="fixture-no-inference",
        ),
        EmotionSignal(
            start=1,
            end=2,
            speaker_id=None,
            reason="Synthetic uncertain-speaker fixture",
            model_id="synthetic-preview-fixture",
            model_revision="fixture-no-inference",
        ),
    ],
)
with Session(admin) as s, s.begin():
    s.add(Tenant(id=tenant, name="STEP21 synthetic preview"))
    s.flush()
    for role, user in users.items():
        s.add(
            User(
                id=user,
                tenant_id=tenant,
                display_name="Synthetic reviewer",
                role="admin" if role == "admin" else "supervisor",
                enabled=True,
            )
        )
    s.flush()
    for role, user in users.items():
        s.add(ExternalIdentity(tenant_id=tenant, user_id=user, issuer=issuer, subject=role))
    add_report(s, report, tenant, users["reviewerA"])
with session_scope(runtime, tenant_id=tenant) as s:
    for index in range(2):
        enroll(
            s,
            Principal(tenant, users["admin"], "admin"),
            str(report.call_id),
            Enrollment(
                segment_index=index,
                partition="train",
                audio_sha256=hashlib.sha256(data).hexdigest(),
                conversation_key=str(report.call_id),
                speaker_keys=["synthetic-only"],
                consent_to_train=False,
                consent_evidence="synthetic preview; not real training consent",
            ),
        )
now = int(time.time())
tokens = {
    role: jwt.encode(
        dict(iss=issuer, aud="step21", sub=role, tenant_id=tenant, iat=now, exp=now + 3600),
        key,
        algorithm="RS256",
    )
    for role in users
}
Path(".local/step21-ui-context.json").write_text(
    json.dumps(dict(tokens=tokens, tenant=tenant, users=users, call_id=str(report.call_id)))
)
app = create_app(
    ApiSettings(issuer=issuer, audience="step21", public_key=public, synthetic_data=True), runtime
)
uvicorn.run(app, host="127.0.0.1", port=8781, log_level="warning")
