"""Real signed reviewer identities, restricted PostgreSQL and immutable originals."""

import hashlib
from uuid import uuid4

import pytest
from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from ml.emotion.contracts import EmotionResult, EmotionSignal
from services.api.db.models import EmotionItem, EmotionVote, ExternalIdentity, User
from src.database.connection import session_scope
from src.database.models import CallRecord
from tests.api import test_api as api_fixtures

api_fixture = api_fixtures.api
keys = api_fixtures.keys


@pytest.fixture
def reviews(api_fixture):
    client, token, report, peer, job, tenant, other, runtime, admin, users = api_fixture
    with Session(admin) as session, session.begin():
        reviewer = str(uuid4())
        users["reviewer2"] = reviewer
        session.add(
            User(
                id=reviewer,
                tenant_id=tenant,
                display_name="Synthetic reviewer",
                role="supervisor",
                enabled=True,
            )
        )
        session.flush()
        session.add(
            ExternalIdentity(
                tenant_id=tenant,
                user_id=reviewer,
                issuer="https://identity.example.test",
                subject="reviewer2",
            )
        )
        for r in (report, peer):
            r.acoustic_emotion = EmotionResult(
                status="completed",
                signals=[
                    EmotionSignal(
                        start=0,
                        end=1,
                        speaker_id="synthetic",
                        label="angry",
                        confidence=0.8,
                        probabilities=dict(angry=0.8, happy=0.1, neutral=0.05, sad=0.05),
                    )
                ],
            )
            record = session.scalar(select(CallRecord).where(CallRecord.call_id == str(r.call_id)))
            record.report_json = r.model_dump_json()

    def enroll(r=report, partition="train", **overrides):
        data = dict(
            segment_index=0,
            partition=partition,
            audio_sha256=hashlib.sha256(str(r.call_id).encode()).hexdigest(),
            conversation_key=str(r.call_id),
            speaker_keys=[str(r.call_id)],
            consent_to_train=partition == "train",
            consent_evidence="synthetic permission fixture",
        )
        data.update(overrides)
        return client.post(
            f"/api/v1/calls/{r.call_id}/emotion-review-items", headers=token("admin"), json=data
        )

    yield api_fixture, enroll


def vote(client, token, item, role, label="sad"):
    return client.post(
        f"/api/v1/emotion-reviews/{item['id']}/votes",
        headers=token(role),
        json=dict(
            label=label,
            notes="Synthetic reviewed label",
            confirmed=True,
            expected_revision=item["revision"],
        ),
    )


def test_dual_review_original_immutable_and_revocation(reviews):
    api, enroll = reviews
    client, token, *_ = api
    response = enroll()
    assert response.status_code == 201, response.text
    item = response.json()
    original = item["prediction"]
    item = vote(client, token, item, "supervisor").json()
    assert item["status"] == "pending"
    stale = vote(client, token, {**item, "revision": 1}, "reviewer2")
    assert stale.status_code == 409
    item = vote(client, token, item, "reviewer2").json()
    assert item["status"] == "verified" and item["corrected_label"] == "sad"
    assert item["prediction"] == original and item["eligible_for_training"]
    before = client.get("/api/v1/emotion-training-dataset", headers=token("admin")).json()
    assert len(before["records"]) == 1
    response = client.delete(
        f"/api/v1/emotion-reviews/{item['id']}/votes/me", headers=token("reviewer2")
    )
    assert response.status_code == 200 and response.json()["prediction"] == original
    after = client.get("/api/v1/emotion-training-dataset", headers=token("admin")).json()
    assert not after["records"] and after["fingerprint"] != before["fingerprint"]


def test_evaluation_hidden_and_split_contamination_rejected(reviews):
    api, enroll = reviews
    client, token, report, peer, *_ = api
    held = enroll(peer, "evaluation")
    assert held.status_code == 201
    hidden = held.json()
    assert client.get("/api/v1/emotion-reviews", headers=token("supervisor")).json() == []
    assert vote(client, token, hidden, "supervisor").status_code == 404
    assert client.get("/api/v1/emotion-reviews", headers=token("agent")).status_code == 403
    assert (
        client.get("/api/v1/emotion-training-dataset", headers=token("supervisor")).status_code
        == 403
    )
    conflict = enroll(report, speaker_keys=[str(peer.call_id)])
    assert conflict.status_code == 409
    changed = client.patch(
        f"/api/v1/emotion-reviews/{hidden['id']}/consent",
        headers=token("admin"),
        json=dict(consent_to_train=True, consent_evidence="fixture", expected_revision=1),
    )
    assert changed.status_code == 422


def test_disagreement_needs_independent_admin_and_changes_invalidate(reviews):
    api, enroll = reviews
    client, token, *_ = api
    item = enroll().json()
    item = vote(client, token, item, "supervisor", "sad").json()
    item = vote(client, token, item, "reviewer2", "happy").json()
    assert item["status"] == "disagreement"
    response = client.post(
        f"/api/v1/emotion-reviews/{item['id']}/adjudicate",
        headers=token("admin"),
        json=dict(
            label="sad",
            notes="Independent synthetic adjudication",
            confirmed=True,
            expected_revision=item["revision"],
        ),
    )
    assert response.status_code == 200, response.text
    item = response.json()
    assert item["status"] == "adjudicated" and item["eligible_for_training"]
    item = vote(client, token, item, "supervisor", "Unknown").json()
    assert not item["eligible_for_training"] and item["adjudication_note"] is None


def test_consent_and_deletion_propagate_without_mutating_source(reviews):
    api, enroll = reviews
    client, token, report, peer, job, tenant, other, runtime, admin, users = api
    item = enroll().json()
    item = vote(client, token, item, "supervisor").json()
    item = vote(client, token, item, "reviewer2").json()
    current = client.patch(
        f"/api/v1/emotion-reviews/{item['id']}/consent",
        headers=token("admin"),
        json=dict(
            consent_to_train=False,
            consent_evidence="synthetic revocation",
            expected_revision=item["revision"],
        ),
    )
    assert current.status_code == 200 and not current.json()["eligible_for_training"]
    assert (
        client.get("/api/v1/emotion-training-dataset", headers=token("admin")).json()["records"]
        == []
    )
    assert (
        client.delete(f"/api/v1/emotion-reviews/{item['id']}", headers=token("admin")).status_code
        == 204
    )
    with Session(admin) as session:
        assert not list(
            session.scalars(select(EmotionVote).where(EmotionVote.item_id == item["id"]))
        )
        original = session.scalar(
            select(CallRecord).where(CallRecord.call_id == str(report.call_id))
        )
        assert "angry" in original.report_json


def test_db_immutability_and_tenant_rls(reviews):
    api, enroll = reviews
    client, token, report, peer, job, tenant, other, runtime, *_ = api
    item = enroll().json()
    with session_scope(runtime, tenant_id=other) as session:
        assert session.scalar(select(EmotionItem).where(EmotionItem.id == item["id"])) is None
    with pytest.raises(DBAPIError), session_scope(runtime, tenant_id=tenant) as session:
        session.execute(
            update(EmotionItem)
            .where(EmotionItem.id == item["id"])
            .values(prediction={"label": "happy"})
        )


@pytest.mark.parametrize(
    "patch", [{"label": "definitely depressed"}, {"confirmed": False}, {"reviewer_id": "spoof"}]
)
def test_invalid_labels_confirmation_and_spoofed_reviewer_rejected(reviews, patch):
    api, enroll = reviews
    client, token, *_ = api
    item = enroll().json()
    body = dict(label="sad", notes="", confirmed=True, expected_revision=1)
    body.update(patch)
    response = client.post(
        f"/api/v1/emotion-reviews/{item['id']}/votes", headers=token("supervisor"), json=body
    )
    assert response.status_code == 422


def test_paired_agreement_metrics_are_actual_and_not_invented(reviews):
    api, enroll = reviews
    client, token, report, peer, *_ = api
    empty = client.get("/api/v1/emotion-review-metrics", headers=token("supervisor")).json()
    assert empty["exact_label_agreement"] is None
    first = enroll().json()
    first = vote(client, token, first, "supervisor", "sad").json()
    first = vote(client, token, first, "reviewer2", "sad").json()
    second = enroll(peer).json()
    second = vote(client, token, second, "supervisor", "sad").json()
    second = vote(client, token, second, "reviewer2", "happy").json()
    result = client.get("/api/v1/emotion-review-metrics", headers=token("supervisor")).json()
    assert result["corrected_segments"] == 1 and result["audit_pairs"] == 2
    assert result["agreeing_pairs"] == 1 and result["exact_label_agreement"] == 0.5


def test_source_erasure_cascades_annotations(reviews):
    from sqlalchemy import delete

    api, enroll = reviews
    client, token, report, peer, job, tenant, other, runtime, admin, users = api
    item = enroll().json()
    item = vote(client, token, item, "supervisor").json()
    with Session(admin) as session, session.begin():
        session.execute(delete(CallRecord).where(CallRecord.call_id == str(report.call_id)))
    with Session(admin) as session:
        assert session.get(EmotionItem, item["id"]) is None
        assert not list(
            session.scalars(select(EmotionVote).where(EmotionVote.item_id == item["id"]))
        )
    assert not client.get("/api/v1/emotion-training-dataset", headers=token("admin")).json()[
        "records"
    ]
