"""HTTP/WS execution of finalize, revision updates and explicit decoder recovery."""

import pytest

from tests.streaming.test_transport import (
    ORIGIN,
    authorize,
    create,
    headers,
    issue,
    receive_session,
    upload,
)


def test_explicit_finalize_is_scoped_versioned_and_idempotent(live):
    room = create(live)
    url = f"/api/v1/live/sessions/{room['id']}"
    assert (
        live[0]
        .post(url + "/finalize", headers=headers(live), json={"consent_revision": 0})
        .status_code
        == 403
    )
    akey, bkey = issue(live, room), issue(live, room, "peer")
    with (
        live[0].websocket_connect(
            f"/api/v1/live/socket/{room['id']}", headers={"Origin": ORIGIN}
        ) as a,
        live[0].websocket_connect(
            f"/api/v1/live/socket/{room['id']}", headers={"Origin": ORIGIN}
        ) as b,
    ):
        a.send_json({"ticket": akey})
        receive_session(a)
        b.send_json({"ticket": bkey})
        receive_session(b)
        state = authorize(live, room, a, b)
        rev = state["consent_revision"]
        for seq in range(2):
            assert upload(live, room, rev, seq).status_code == 200
        response = live[0].post(
            url + "/finalize", headers=headers(live), json={"consent_revision": rev - 1}
        )
        assert response.status_code == 409
        response = live[0].post(
            url + "/finalize", headers=headers(live), json={"consent_revision": rev}
        )
        assert response.json() == {"scheduled_windows": 1}
        assert live[0].post(
            url + "/finalize", headers=headers(live), json={"consent_revision": rev}
        ).json() == {"scheduled_windows": 0}
        for _ in range(24):
            event = a.receive_json()
            if (
                event["type"] == "transcript"
                and event.get("transcript", {}).get("state") == "final"
            ):
                break
        assert event["transcript"]["reason"] == "manual"
        assert event["transcript"]["timing"] == "interpolated"


@pytest.mark.parametrize("permanent", [False, True])
def test_decoder_failure_retries_once_then_recovers_or_revokes(live, monkeypatch, permanent):
    original = live[3].transcribe
    attempts = []

    def failing(pcm):
        attempts.append(len(pcm))
        if len(attempts) == 1 or permanent:
            raise RuntimeError("private inference diagnostic")
        return original(pcm)

    monkeypatch.setattr(live[3], "transcribe", failing)
    room = create(live)
    akey, bkey = issue(live, room), issue(live, room, "peer")
    with (
        live[0].websocket_connect(
            f"/api/v1/live/socket/{room['id']}", headers={"Origin": ORIGIN}
        ) as a,
        live[0].websocket_connect(
            f"/api/v1/live/socket/{room['id']}", headers={"Origin": ORIGIN}
        ) as b,
    ):
        a.send_json({"ticket": akey})
        receive_session(a)
        b.send_json({"ticket": bkey})
        receive_session(b)
        state = authorize(live, room, a, b)
        rev = state["consent_revision"]
        for seq in range(2):
            assert upload(live, room, rev, seq).status_code == 200
        events = []
        for _ in range(24):
            event = a.receive_json()
            events.append(event)
            if permanent and event.get("code") == "analysis_failed":
                break
            if (
                not permanent
                and event.get("transcript")
                and event["transcript"]["state"] == "provisional"
            ):
                break
        assert len(attempts) == 2
        assert any(e.get("code") == "analysis_retrying" for e in events)
        assert any(e.get("transcript") and e["transcript"]["state"] == "failed" for e in events)
        assert "private inference diagnostic" not in str(events)
        if permanent:
            assert upload(live, room, rev, 2).status_code == 403
            assert not live[2].allowed(live[2].rooms[room["id"]])
        else:
            assert events[-1]["transcript"]["revision"] == 2
