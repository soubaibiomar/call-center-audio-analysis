"""Execute correction decisions against PostgreSQL with real signed identities."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from services.api.db.models import Call, CallAnnotation, CallAnnotationEvent, EmotionPartitionKey
from services.reviews.call_service import fingerprint
from src.database.connection import session_scope
from src.database.models import CallRecord


def enroll(api, **overrides):
    client, token, report, *_ = api
    data = dict(
        partition="train",
        audio_sha256="a" * 64,
        conversation_key="synthetic-conversation",
        speaker_keys=["synthetic-speaker"],
        consent_to_train=True,
        consent_evidence="Synthetic test permission, no real audio",
        source_attested=True,
        source_attestation="Synthetic source fixture registered by administrator",
    )
    data.update(overrides)
    response = client.post(
        f"/api/v1/calls/{report.call_id}/reviews", json=data, headers=token("admin")
    )
    assert response.status_code == 201, response.text
    return response.json()


def edit(api, item, **overrides):
    payload = item["payload"] | {"expected_revision": item["revision"]}
    payload.update(overrides)
    response = api[0].patch(
        f"/api/v1/call-reviews/{item['id']}", json=payload, headers=api[1]("supervisor")
    )
    assert response.status_code == 200, response.text
    return response.json()


def decide(api, item, action="submit", subject="supervisor", **overrides):
    data = dict(
        action=action,
        expected_revision=item["revision"],
        rationale="Synthetic decision after fixture playback verification",
        listened_to_audio=True,
        observed_audio_sha256=item["source_audio_sha256"],
        observed_duration_seconds=item["original"]["duration_seconds"],
    )
    data.update(overrides)
    return api[0].post(
        f"/api/v1/call-reviews/{item['id']}/decisions", json=data, headers=api[1](subject)
    )


def exported(api):
    response = api[0].get("/api/v1/call-review-dataset", headers=api[1]("admin"))
    assert response.status_code == 200, response.text
    return response.json()


def approved(api, **overrides):
    item = edit(api, enroll(api, **overrides))
    response = decide(api, item)
    assert response.status_code == 200, response.text
    response = decide(api, response.json(), "approve", "admin")
    assert response.status_code == 200, response.text
    return response.json()


def test_word_speaker_score_original_and_audit(api):
    item = enroll(api)
    original = item["original"]
    segments = item["payload"]["segments"]
    segments[0].update(text="Synthetic corrected word", speaker_role="Customer", uncertain=False)
    segments[1].update(speaker_role="Agent", uncertain=False)
    item = edit(
        api,
        item,
        segments=segments,
        qa_override=dict(
            score=2.5,
            rationale="Synthetic scoring evidence within this range",
            audio_start=0.5,
            audio_end=1.5,
        ),
    )
    assert item["state"] == "draft" and item["author_id"] == api[9]["supervisor"]
    assert item["original"] == original
    assert item["original_sha256"] == fingerprint(original)
    response = decide(api, item)
    assert response.status_code == 200
    item = response.json()
    assert decide(api, item, "approve").status_code == 403
    item = decide(api, item, "approve", "admin").json()
    assert item["state"] == "approved" and item["approver_id"] == api[9]["admin"]
    manifest = exported(api)
    assert manifest["approved_segments"] == 2
    assert manifest["fingerprint"] == fingerprint(manifest["items"])
    assert manifest["items"][0]["payload"]["qa_override"]["score"] == 2.5
    with Session(api[8]) as session:
        source = session.scalar(select(CallRecord).where(CallRecord.call_id == str(api[2].call_id)))
        assert source.report_json == api[2].model_dump_json()
        events = session.scalars(
            select(CallAnnotationEvent)
            .where(CallAnnotationEvent.annotation_id == item["id"])
            .order_by(CallAnnotationEvent.revision)
        )
        events = list(events)
        assert [e.action for e in events] == ["enrolled", "edited", "submit", "approve"]
        assert all(fingerprint(e.payload) == e.payload_digest for e in events)
        assert events[-1].payload["playback_attestation"]["observed_audio_sha256"] == "a" * 64
    history = api[0].get(f"/api/v1/call-reviews/{item['id']}/history", headers=api[1]("supervisor"))
    assert len(history.json()) == 4 and "payload" not in history.json()[0]


@pytest.mark.parametrize("action", ["read", "edit", "decision", "history", "export", "erase"])
def test_agent_cannot_review(api, action):
    item = enroll(api)
    client, token = api[:2]
    base = f"/api/v1/call-reviews/{item['id']}"
    requests = {
        "read": lambda: client.get(f"/api/v1/calls/{item['call_id']}/review", headers=token()),
        "edit": lambda: client.patch(
            base, json=item["payload"] | {"expected_revision": 1}, headers=token()
        ),
        "decision": lambda: decide(api, item, subject="agent"),
        "history": lambda: client.get(base + "/history", headers=token()),
        "export": lambda: client.get("/api/v1/call-review-dataset", headers=token()),
        "erase": lambda: client.delete(base + "?expected_revision=1", headers=token()),
    }
    assert requests[action]().status_code == 403


@pytest.mark.parametrize(
    "invalid",
    [
        {"observed_audio_sha256": "b" * 64},
        {"observed_duration_seconds": 999},
        {"listened_to_audio": False},
        {"rationale": "short"},
        {"reviewer_id": str(uuid4())},
    ],
)
def test_bad_decision_evidence_rejected(api, invalid):
    item = edit(api, enroll(api))
    assert decide(api, item, **invalid).status_code == 422
    assert exported(api)["approved_segments"] == 0


@pytest.mark.parametrize(
    "override",
    [
        dict(score=2, rationale="", audio_start=0, audio_end=1),
        dict(score=6, rationale="A sufficiently detailed rationale", audio_start=0, audio_end=1),
        dict(score=2, rationale="A sufficiently detailed rationale", audio_start=1, audio_end=1),
        dict(score=2, rationale="A sufficiently detailed rationale", audio_start=0, audio_end=999),
    ],
)
def test_qa_mandatory_rationale_and_inbounds_audio(api, override):
    item = enroll(api)
    response = api[0].patch(
        f"/api/v1/call-reviews/{item['id']}",
        headers=api[1]("supervisor"),
        json=item["payload"] | {"expected_revision": 1, "qa_override": override},
    )
    assert response.status_code == 422


def test_concurrent_edits_and_stale_approval(api):
    item = enroll(api)
    path = f"/api/v1/call-reviews/{item['id']}"

    def write(word):
        payload = {
            "segments": [s | {"text": word} for s in item["payload"]["segments"]],
            "expected_revision": 1,
        }
        return api[0].patch(path, headers=api[1]("supervisor"), json=payload).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(write, ["Concurrent correction A", "Concurrent correction B"])) == [
            200,
            409,
        ]
    assert decide(api, item).status_code == 409
    with Session(api[8]) as session:
        assert session.get(CallAnnotation, item["id"]).revision == 2
        assert (
            len(
                list(
                    session.scalars(
                        select(CallAnnotationEvent).where(
                            CallAnnotationEvent.annotation_id == item["id"]
                        )
                    )
                )
            )
            == 2
        )


@pytest.mark.parametrize("uncertain,role", [(True, "Agent"), (False, "Unknown")])
def test_uncertain_and_unknown_excluded(api, uncertain, role):
    item = enroll(api)
    segments = [
        s | {"uncertain": uncertain, "speaker_role": role} for s in item["payload"]["segments"]
    ]
    item = edit(api, item, segments=segments)
    item = decide(api, item).json()
    item = decide(api, item, "approve", "admin").json()
    assert item["state"] == "approved" and not item["eligible_for_training"]
    assert exported(api)["approved_segments"] == 0


def test_revocation_edit_rejection_and_erasure(api):
    item = approved(api)
    before = exported(api)
    response = api[0].patch(
        f"/api/v1/call-reviews/{item['id']}/consent",
        headers=api[1]("admin"),
        json=dict(
            consent_to_train=False,
            consent_evidence="Permission withdrawn",
            expected_revision=item["revision"],
        ),
    )
    assert response.status_code == 200
    assert exported(api)["approved_segments"] == 0
    assert exported(api)["fingerprint"] != before["fingerprint"]
    item = edit(api, response.json())
    assert item["approver_id"] is None and item["state"] == "draft"
    item = decide(api, item).json()
    item = decide(api, item, "reject", "admin").json()
    assert item["state"] == "rejected"
    response = api[0].delete(
        f"/api/v1/call-reviews/{item['id']}?expected_revision={item['revision']}",
        headers=api[1]("admin"),
    )
    assert response.status_code == 204
    with Session(api[8]) as session:
        assert session.get(CallAnnotation, item["id"]) is None
        assert not list(
            session.scalars(
                select(CallAnnotationEvent).where(CallAnnotationEvent.annotation_id == item["id"])
            )
        )


def test_expiry_tenant_isolation_and_expired_erasure(api):
    item = approved(api)
    with session_scope(api[7], tenant_id=api[6]) as session:
        assert session.get(CallAnnotation, item["id"]) is None
        assert (
            session.scalar(
                select(CallAnnotationEvent).where(CallAnnotationEvent.annotation_id == item["id"])
            )
            is None
        )
    with Session(api[8]) as session, session.begin():
        session.get(Call, item["call_id"]).expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert exported(api)["approved_segments"] == 0
    assert (
        api[0].get(f"/api/v1/calls/{item['call_id']}/review", headers=api[1]("admin")).status_code
        == 404
    )
    assert (
        api[0]
        .delete(
            f"/api/v1/call-reviews/{item['id']}?expected_revision={item['revision']}",
            headers=api[1]("admin"),
        )
        .status_code
        == 204
    )


def test_evaluation_partition_is_protected_and_shared_locks(api):
    item = enroll(api, partition="evaluation", consent_to_train=False)
    assert (
        api[0]
        .get(f"/api/v1/calls/{item['call_id']}/review", headers=api[1]("supervisor"))
        .status_code
        == 404
    )
    assert exported(api)["items"] == []
    response = api[0].patch(
        f"/api/v1/call-reviews/{item['id']}/consent",
        headers=api[1]("admin"),
        json=dict(
            consent_to_train=True,
            consent_evidence="Invalid evaluation permission",
            expected_revision=1,
        ),
    )
    assert response.status_code == 422
    peer = api[3]
    response = api[0].post(
        f"/api/v1/calls/{peer.call_id}/reviews",
        headers=api[1]("admin"),
        json=dict(
            partition="train",
            audio_sha256="b" * 64,
            conversation_key="synthetic-conversation",
            speaker_keys=["unrelated"],
            consent_evidence="Synthetic",
            source_attested=True,
            source_attestation="Synthetic source fixture attestation",
        ),
    )
    assert response.status_code == 409
    with Session(api[8]) as session:
        assert (
            session.get(
                EmotionPartitionKey,
                (
                    api[5],
                    __import__("hashlib")
                    .sha256(b"conversation:synthetic-conversation")
                    .hexdigest(),
                ),
            ).partition
            == "evaluation"
        )


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE call_annotations SET original='{}'::jsonb WHERE id=:id",
        "UPDATE call_annotation_events SET action='forged' WHERE annotation_id=:id",
        "DELETE FROM call_annotation_events WHERE annotation_id=:id",
    ],
)
def test_database_source_and_audit_immutable(api, statement):
    item = enroll(api)
    with pytest.raises(DBAPIError), session_scope(api[7], tenant_id=api[5]) as session:
        session.execute(text(statement), {"id": item["id"]})


def test_duplicate_indices_and_pii_rejected(api):
    item = enroll(api)
    for segments in [
        item["payload"]["segments"][:1],
        [item["payload"]["segments"][0]] * 2,
        [s | {"text": "Call person@example.com"} for s in item["payload"]["segments"]],
    ]:
        response = api[0].patch(
            f"/api/v1/call-reviews/{item['id']}",
            headers=api[1]("supervisor"),
            json=dict(segments=segments, expected_revision=1),
        )
        assert response.status_code == 422
