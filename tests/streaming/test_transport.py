"""Real HTTP/WS authorization plus bounded broker and revocation tests."""

import asyncio
import time
from threading import Event
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect

from services.api.app import create_app
from services.api.auth import Principal
from services.api.db.models import User
from services.streaming.broker import LiveBroker
from services.streaming.contracts import LiveConsent, LivePeer, LiveSignal, LiveTranscriptSpan
from services.streaming.settings import LiveSettings

ORIGIN = "http://127.0.0.1:8788"
VOICE = b"\xb8\x0b" * 16000


class Recorder:
    def __init__(self):
        self.calls = []

    def transcribe(self, pcm):
        self.calls.append(pcm)
        return [LiveTranscriptSpan(start_seconds=0, end_seconds=1, text="Synthetic test event")]


@pytest.fixture
def live(api):
    asr = Recorder()
    settings = api[0].app.user_middleware[0].kwargs["auth"].settings
    app = create_app(
        settings, api[7], live_settings=LiveSettings(enabled=True, origins=(ORIGIN,)), live_asr=asr
    )
    with TestClient(app) as client:
        yield client, api[1], app.state.live_broker, asr, api


def headers(live, role="agent"):
    return live[1](role) | {"Origin": ORIGIN}


def create(live):
    result = live[0].post(
        "/api/v1/live/sessions", headers=headers(live), json={"peer_user_id": live[4][9]["peer"]}
    )
    assert result.status_code == 201, result.text
    return result.json()


def issue(live, room, role="agent"):
    result = live[0].post(
        f"/api/v1/live/sessions/{room['id']}/tickets", headers=headers(live, role)
    )
    assert result.status_code == 200, result.text
    return result.json()["ticket"]


def receive_session(socket, predicate=lambda value: True):
    for _ in range(24):
        value = socket.receive_json()
        if value["type"] == "session" and predicate(value["session"]):
            return value["session"]
    raise AssertionError("Expected bounded session update")


def authorize(live, room, a, b):
    for role in ["agent", "peer"]:
        result = live[0].patch(
            f"/api/v1/live/sessions/{room['id']}/consent",
            headers=headers(live, role),
            json={"microphone": True, "analysis": True},
        )
        assert result.status_code == 200
    a.send_json({"type": "connection", "media_state": "connected"})
    b.send_json({"type": "connection", "media_state": "connected"})
    return receive_session(a, lambda v: v["capture_allowed"])


def upload(
    live,
    room,
    revision,
    sequence=0,
    start_sample=None,
    pcm=VOICE,
    role="agent",
    content_type="application/octet-stream",
):
    return live[0].post(
        f"/api/v1/live/sessions/{room['id']}/audio",
        content=pcm,
        headers=headers(live, role)
        | {
            "Content-Type": content_type,
            "X-Audio-Sequence": str(sequence),
            "X-Audio-Start-Sample": str(sequence * 16000 if start_sample is None else start_sample),
            "X-Consent-Revision": str(revision),
        },
    )


def test_default_is_disabled_and_http_authenticated(api):
    client, token = api[:2]
    assert client.get("/api/v1/live/config", headers=token()).json()["enabled"] is False
    assert client.get("/api/v1/live/sessions", headers=token()).status_code == 503
    assert client.get("/api/v1/live/config").status_code == 401


def test_origin_membership_and_directory(live):
    room = create(live)
    client = live[0]
    assert (
        client.post(
            "/api/v1/live/sessions", headers=live[1](), json={"peer_user_id": live[4][9]["admin"]}
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/v1/live/sessions/{room['id']}/tickets", headers=headers(live, "supervisor")
        ).status_code
        == 404
    )
    assert client.get("/api/v1/live/sessions", headers=headers(live, "supervisor")).json() == {
        "items": []
    }
    peers = client.get("/api/v1/live/peers", headers=headers(live)).json()["items"]
    assert all(
        p["user_id"] not in {live[4][9]["disabled"], live[4][9]["service"], live[4][9]["agent"]}
        for p in peers
    )
    assert upload(live, room, 0).status_code == 403
    assert not live[3].calls


def test_one_use_ticket_and_no_cookie_or_cross_origin_auth(live):
    room = create(live)
    secret = issue(live, room)
    url = f"/api/v1/live/socket/{room['id']}"
    with live[0].websocket_connect(url, headers={"Origin": ORIGIN}) as socket:
        socket.send_json({"ticket": secret})
        receive_session(socket)
        with (
            pytest.raises(WebSocketDisconnect),
            live[0].websocket_connect(url, headers={"Origin": ORIGIN}) as replay,
        ):
            replay.send_json({"ticket": secret})
            replay.receive_json()
        assert room["id"] in live[2].rooms
    assert not live[2].rooms and not live[2].tickets
    with (
        pytest.raises(WebSocketDisconnect),
        live[0].websocket_connect(url, headers={"Origin": "https://untrusted.example"}),
    ):
        pass


def test_authorized_audio_reaches_asr_and_disconnect_clears(live):
    room = create(live)
    one, two = issue(live, room), issue(live, room, "peer")
    url = f"/api/v1/live/socket/{room['id']}"
    with (
        live[0].websocket_connect(url, headers={"Origin": ORIGIN}) as a,
        live[0].websocket_connect(url, headers={"Origin": ORIGIN}) as b,
    ):
        a.send_json({"ticket": one})
        receive_session(a)
        b.send_json({"ticket": two})
        receive_session(b)
        current = authorize(live, room, a, b)
        for seq in range(4):
            result = upload(live, room, current["consent_revision"], seq)
            assert result.status_code == 200, result.text
        for _ in range(24):
            result = a.receive_json()
            if result["type"] == "transcript":
                break
        assert result["type"] == "transcript"
        assert result["transcript"]["text"] == "Synthetic test event"
        assert len(live[3].calls) >= 1 and all(len(data) <= 256000 for data in live[3].calls)
        owned = live[2].rooms[room["id"]]
    assert live[2].rooms == {} and live[2].tickets == {}
    assert live[2].work.empty()
    assert all(
        not p.buffer and p.queue is None and not p.analysis for p in owned.participants.values()
    )


@pytest.mark.parametrize(
    "invalid,status",
    [
        ({"pcm": b"\0" * 32002}, 413),
        ({"pcm": b"\0" * 31999}, 422),
        ({"sequence": 1}, 409),
        ({"start_sample": 1}, 409),
        ({"content_type": "audio/L16"}, 415),
        ({"role": "supervisor"}, 404),
    ],
)
def test_bad_frames_denied(live, invalid, status):
    room = create(live)
    one, two = issue(live, room), issue(live, room, "peer")
    url = f"/api/v1/live/socket/{room['id']}"
    with (
        live[0].websocket_connect(url, headers={"Origin": ORIGIN}) as a,
        live[0].websocket_connect(url, headers={"Origin": ORIGIN}) as b,
    ):
        a.send_json({"ticket": one})
        receive_session(a)
        b.send_json({"ticket": two})
        receive_session(b)
        current = authorize(live, room, a, b)
        assert upload(live, room, current["consent_revision"], **invalid).status_code == status
        assert not live[3].calls


def test_partial_consent_never_admits_audio(live):
    room = create(live)
    one = issue(live, room)
    with live[0].websocket_connect(
        f"/api/v1/live/socket/{room['id']}", headers={"Origin": ORIGIN}
    ) as a:
        a.send_json({"ticket": one})
        receive_session(a)
        result = live[0].patch(
            f"/api/v1/live/sessions/{room['id']}/consent",
            headers=headers(live),
            json={"microphone": True, "analysis": True},
        )
        assert not result.json()["capture_allowed"]
        assert upload(live, room, result.json()["consent_revision"]).status_code == 403
        assert live[2].rooms[room["id"]].participants[live[4][9]["agent"]].buffer == b""


def test_expired_ticket_invitation_and_disabled_socket_clear(live):
    room = create(live)
    secret = issue(live, room)
    live[2].tickets[secret].deadline = time.monotonic() - 1
    with (
        pytest.raises(WebSocketDisconnect),
        live[0].websocket_connect(
            f"/api/v1/live/socket/{room['id']}", headers={"Origin": ORIGIN}
        ) as a,
    ):
        a.send_json({"ticket": secret})
        a.receive_json()
    secret = issue(live, room)
    with live[0].websocket_connect(
        f"/api/v1/live/socket/{room['id']}", headers={"Origin": ORIGIN}
    ) as a:
        a.send_json({"ticket": secret})
        receive_session(a)
        with Session(live[4][8]) as session, session.begin():
            session.get(User, live[4][9]["agent"]).enabled = False
        a.send_json({"type": "ping"})
        with pytest.raises(WebSocketDisconnect):
            while True:
                a.receive_json()
    assert not live[2].rooms


@pytest.mark.asyncio
async def test_revocation_fences_queued_and_inflight_results():
    started, release = Event(), Event()

    class Slow(Recorder):
        def transcribe(self, pcm):
            started.set()
            release.wait(3)
            return super().transcribe(pcm)

    a = Principal("tenant", "00000000-0000-4000-8000-000000000001", "agent")
    b = Principal("tenant", "00000000-0000-4000-8000-000000000002", "agent")
    asr = Slow()
    broker = LiveBroker(LiveSettings(enabled=True, origins=(ORIGIN,)), asr)
    view = broker.create(
        a,
        LivePeer(user_id=UUID(a.user_id), display_name="A"),
        LivePeer(user_id=UUID(b.user_id), display_name="B"),
    )
    room = broker.room(str(view.id), a)
    for identity in [a, b]:
        ticket = broker.issue(room, identity, time.time() + 60)
        broker.attach(room.id, ticket.ticket)
        broker.consent(room, identity, LiveConsent(microphone=True, analysis=True))
        broker.connection(room, identity, "connected")
    revision = room.revision
    for seq in range(4):
        broker.audio(room, a, VOICE, seq, seq * 16000, revision)
    await asyncio.to_thread(started.wait, 2)
    broker.consent(room, b, LiveConsent(microphone=True, analysis=False))
    release.set()
    await broker.worker
    assert not broker.allowed(room) and all(not p.buffer for p in room.participants.values())
    for p in room.participants.values():
        while not p.queue.empty():
            assert p.queue.get_nowait().type != "transcript"
    with pytest.raises(HTTPException) as error:
        broker.audio(room, a, VOICE, 0, 0, room.revision)
    assert error.value.status_code == 403
    await broker.close()


@pytest.mark.parametrize(
    "origin", ["http://example.com", "https://example.com/", "https://user:pass@example.com", "*"]
)
def test_insecure_origins_rejected(origin):
    with pytest.raises(ValueError):
        LiveSettings(enabled=True, origins=(origin,))


def test_audio_only_encrypted_sdp_contract():
    with pytest.raises(ValidationError):
        LiveSignal(
            kind="offer", sdp="v=0\nm=video 9 UDP/TLS/RTP/SAVPF 96\na=fingerprint:sha-256 ABC"
        )
    with pytest.raises(ValidationError):
        LiveSignal(kind="offer", sdp="v=0\nm=audio 9 RTP/AVP 0")


@pytest.mark.parametrize("binary", [True, False])
def test_invalid_socket_frames_terminate_without_media_admission(live, binary):
    room = create(live)
    secret = issue(live, room)
    with live[0].websocket_connect(
        f"/api/v1/live/socket/{room['id']}", headers={"Origin": ORIGIN}
    ) as socket:
        socket.send_json({"ticket": secret})
        receive_session(socket)
        if binary:
            socket.send_bytes(b"\0" * 32000)
        else:
            socket.send_text("not-json")
        with pytest.raises(WebSocketDisconnect):
            while True:
                socket.receive_json()
    assert not live[2].rooms and not live[3].calls


@pytest.mark.asyncio
async def test_backpressure_revokes_analysis_and_discards_queued_audio():
    started, release = Event(), Event()

    class Slow(Recorder):
        def transcribe(self, pcm):
            started.set()
            release.wait(3)
            return super().transcribe(pcm)

    a = Principal("tenant", "00000000-0000-4000-8000-000000000001", "agent")
    b = Principal("tenant", "00000000-0000-4000-8000-000000000002", "agent")
    broker = LiveBroker(LiveSettings(enabled=True, origins=(ORIGIN,), pending_windows=2), Slow())
    view = broker.create(
        a,
        LivePeer(user_id=UUID(a.user_id), display_name="A"),
        LivePeer(user_id=UUID(b.user_id), display_name="B"),
    )
    room = broker.room(str(view.id), a)
    for identity in [a, b]:
        ticket = broker.issue(room, identity, time.time() + 60)
        broker.attach(room.id, ticket.ticket)
        broker.consent(room, identity, LiveConsent(microphone=True, analysis=True))
        broker.connection(room, identity, "connected")
    for seq in range(2):
        broker.audio(room, a, VOICE, seq, seq * 16000, room.revision)
    await asyncio.to_thread(started.wait, 2)
    for seq in range(2):
        broker.audio(room, b, VOICE, seq, seq * 16000, room.revision)
    broker.flush(room, b, room.revision)
    broker.flush(room, a, room.revision)
    assert broker.work.qsize() == 2
    room.capture_started -= 4
    with pytest.raises(HTTPException) as failure:
        for seq in range(2, 4):
            broker.audio(room, a, VOICE, seq, seq * 16000, room.revision)
    release.set()
    await broker.worker
    assert failure.value.status_code == 429
    assert room.id in broker.rooms and not broker.allowed(room)
    assert broker.work.empty() and all(
        not p.buffer and not p.analysis for p in room.participants.values()
    )
    await broker.close()
