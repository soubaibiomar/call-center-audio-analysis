"""Authenticated HTTP capture and one-use-ticket WebSocket signaling/event transport."""

import asyncio
import contextlib
import time
from collections.abc import Callable
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, WebSocket
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.engine import Engine
from starlette.concurrency import run_in_threadpool
from starlette.websockets import WebSocketDisconnect

from services.api.auth import Principal
from services.api.db.models import User
from services.api.routes.jobs import get_identity
from services.streaming.broker import LiveBroker
from services.streaming.contracts import (
    AudioReceipt,
    FlushReceipt,
    LiveConfig,
    LiveConsent,
    LiveCreate,
    LiveEvent,
    LivePeer,
    LivePeers,
    LiveSessions,
    LiveSessionView,
    LiveTicket,
    SocketAuth,
    SocketMessage,
    TranscriptFlush,
)
from src.database.connection import session_scope

Identity = Annotated[Principal, Depends(get_identity)]


def live_routers(broker: LiveBroker, engine: Callable[[], Engine]) -> tuple[APIRouter, APIRouter]:
    http, sockets = APIRouter(prefix="/live"), APIRouter()

    def available_user(identity: Principal) -> bool:
        with session_scope(engine(), tenant_id=identity.tenant_id) as session:
            return (
                session.scalar(
                    select(User.id).where(
                        User.tenant_id == identity.tenant_id,
                        User.id == identity.user_id,
                        User.enabled.is_(True),
                        User.role.in_(["agent", "supervisor", "admin"]),
                    )
                )
                is not None
            )

    def origin(request: Request) -> None:
        broker.enabled()
        if request.headers.get("origin") not in broker.settings.origins:
            raise HTTPException(403)

    @http.get("/config", response_model=LiveConfig)
    async def config(identity: Identity) -> LiveConfig:
        return LiveConfig(
            enabled=broker.settings.enabled,
            analysis_available=broker.asr is not None,
            model_id="local-faster-whisper" if broker.asr else None,
            session_limit_seconds=broker.settings.ttl_seconds,
        )

    @http.get("/peers", response_model=LivePeers)
    async def peers(identity: Identity) -> LivePeers:
        broker.enabled()

        def read() -> LivePeers:
            with session_scope(engine(), tenant_id=identity.tenant_id) as session:
                users = session.scalars(
                    select(User)
                    .where(
                        User.tenant_id == identity.tenant_id,
                        User.id != identity.user_id,
                        User.enabled.is_(True),
                        User.role.in_(["agent", "supervisor", "admin"]),
                    )
                    .order_by(User.display_name, User.id)
                    .limit(50)
                )
                return LivePeers(
                    items=[LivePeer(user_id=UUID(u.id), display_name=u.display_name) for u in users]
                )

        return await run_in_threadpool(read)

    @http.get("/sessions", response_model=LiveSessions)
    async def sessions(identity: Identity) -> LiveSessions:
        broker.enabled()
        broker.reap()
        return LiveSessions(
            items=[
                broker.view(room)
                for room in broker.rooms.values()
                if room.tenant == identity.tenant_id and identity.user_id in room.participants
            ]
        )

    @http.post("/sessions", response_model=LiveSessionView, status_code=201)
    async def create(data: LiveCreate, request: Request, identity: Identity) -> LiveSessionView:
        origin(request)

        def read() -> tuple[LivePeer, LivePeer]:
            with session_scope(engine(), tenant_id=identity.tenant_id) as session:
                users = list(
                    session.scalars(
                        select(User).where(
                            User.tenant_id == identity.tenant_id,
                            User.id.in_([identity.user_id, str(data.peer_user_id)]),
                            User.enabled.is_(True),
                            User.role.in_(["agent", "supervisor", "admin"]),
                        )
                    )
                )
                if len(users) != 2:
                    raise HTTPException(404)
                records = {
                    u.id: LivePeer(user_id=UUID(u.id), display_name=u.display_name) for u in users
                }
                return records[identity.user_id], records[str(data.peer_user_id)]

        me, peer = await run_in_threadpool(read)
        return broker.create(identity, me, peer)

    @http.patch("/sessions/{room_id}/consent", response_model=LiveSessionView)
    async def consent(
        room_id: UUID, data: LiveConsent, request: Request, identity: Identity
    ) -> LiveSessionView:
        origin(request)
        return broker.consent(broker.room(str(room_id), identity), identity, data)

    @http.post("/sessions/{room_id}/tickets", response_model=LiveTicket)
    async def ticket(room_id: UUID, request: Request, identity: Identity) -> LiveTicket:
        origin(request)
        # Boundary has already verified signature, issuer, audience and expiry.
        token = request.headers["authorization"].partition(" ")[2]
        expiry = float(jwt.decode(token, options={"verify_signature": False})["exp"])
        return broker.issue(broker.room(str(room_id), identity), identity, expiry)

    @http.delete("/sessions/{room_id}", status_code=204)
    async def end(room_id: UUID, request: Request, identity: Identity) -> Response:
        origin(request)
        broker.end(broker.room(str(room_id), identity), "ended")
        return Response(status_code=204)

    @http.post("/sessions/{room_id}/audio", response_model=AudioReceipt)
    async def audio(
        room_id: UUID,
        request: Request,
        identity: Identity,
        sequence: Annotated[int, Header(alias="X-Audio-Sequence", ge=0, le=600)],
        start_sample: Annotated[int, Header(alias="X-Audio-Start-Sample", ge=0, le=9600000)],
        revision: Annotated[int, Header(alias="X-Consent-Revision", ge=0)],
    ) -> AudioReceipt:
        origin(request)
        room = broker.room(str(room_id), identity)
        if not broker.allowed(room):
            raise HTTPException(403)
        for user_id in room.participants:
            if not await run_in_threadpool(
                available_user, Principal(room.tenant, user_id, "agent")
            ):
                broker.end(room, "ended")
                raise HTTPException(403)
        if request.headers.get("content-type") != "application/octet-stream":
            raise HTTPException(415)
        data = bytearray()
        async for part in request.stream():
            if len(data) + len(part) > 32000:
                raise HTTPException(413)
            data.extend(part)
        # Consent may have changed while the body was being received: recheck membership/gates.
        room = broker.room(str(room_id), identity)
        return broker.audio(room, identity, bytes(data), sequence, start_sample, revision)

    @http.post("/sessions/{room_id}/finalize", response_model=FlushReceipt)
    async def finalize(
        room_id: UUID, data: TranscriptFlush, request: Request, identity: Identity
    ) -> FlushReceipt:
        origin(request)
        room = broker.room(str(room_id), identity)
        if not broker.allowed(room):
            raise HTTPException(403)
        for user_id in room.participants:
            if not await run_in_threadpool(
                available_user, Principal(room.tenant, user_id, "agent")
            ):
                broker.end(room, "ended")
                raise HTTPException(403)
        return FlushReceipt(scheduled_windows=broker.flush(room, identity, data.consent_revision))

    @sockets.websocket("/api/v1/live/socket/{room_id}")
    async def socket(websocket: WebSocket, room_id: UUID) -> None:
        if (
            not broker.settings.enabled
            or websocket.headers.get("origin") not in broker.settings.origins
        ):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        room = None
        writer: asyncio.Task[None] | None = None

        async def text_frame(timeout: float) -> str:
            frame = await asyncio.wait_for(websocket.receive(), timeout=timeout)
            if frame["type"] == "websocket.disconnect":
                raise WebSocketDisconnect(frame.get("code", 1000))
            value = frame.get("text")
            if not isinstance(value, str):
                raise ValueError("Only text signaling/event frames are supported")
            return value

        try:
            raw = await text_frame(5)
            if len(raw) > 512:
                raise ValueError("Oversized authentication frame")
            auth = SocketAuth.model_validate_json(raw)
            room, credential, queue = broker.attach(str(room_id), auth.ticket)
            if not await run_in_threadpool(available_user, credential.identity):
                raise HTTPException(403)

            async def send() -> None:
                while True:
                    event = await queue.get()
                    await asyncio.wait_for(websocket.send_json(event.model_dump(mode="json")), 5)
                    if event.type == "terminated":
                        await websocket.close(code=1000)
                        return

            writer = asyncio.create_task(send())
            window_start, messages = time.monotonic(), 0
            while broker.rooms.get(room.id) is room:
                remaining = min(room.deadline, credential.auth_deadline) - time.monotonic()
                if remaining <= 0:
                    break
                if writer.done():
                    break
                raw = await text_frame(min(15, remaining))
                if len(raw) > 40000:
                    raise ValueError("Oversized signaling frame")
                now = time.monotonic()
                if now - window_start >= 1:
                    window_start, messages = now, 0
                messages += 1
                if messages > 40:
                    raise ValueError("Signaling rate limit")
                message = SocketMessage.model_validate_json(raw)
                broker.room(room.id, credential.identity)
                if not await run_in_threadpool(available_user, credential.identity):
                    raise HTTPException(403)
                if message.type == "signal" and message.signal is not None:
                    broker.signal(room, credential.identity, message.signal)
                elif message.type == "connection" and message.media_state is not None:
                    broker.connection(room, credential.identity, message.media_state)
                else:
                    queue.put_nowait(LiveEvent(type="pong"))
        except (
            WebSocketDisconnect,
            HTTPException,
            ValidationError,
            ValueError,
            TimeoutError,
            asyncio.QueueFull,
        ):
            pass
        finally:
            if room is not None:
                broker.end(room, "disconnected")
            if writer is not None:
                writer.cancel()
                with contextlib.suppress(
                    asyncio.CancelledError, WebSocketDisconnect, RuntimeError, TimeoutError
                ):
                    await writer
            with contextlib.suppress(RuntimeError, WebSocketDisconnect):
                await websocket.close(code=1008)

    return http, sockets
