"""Single-ASGI-worker ephemeral rooms; bounded queues and consent-revision fencing."""

import asyncio
import secrets
import time
from dataclasses import dataclass, field, replace
from typing import Literal
from uuid import UUID, uuid4

from fastapi import HTTPException

from ml.asr.incremental import Reconciler, SpeechWindows, Window, Word
from services.api.auth import Principal
from services.streaming.asr import ASRPort, WordASRPort, recognize_words
from services.streaming.contracts import (
    AudioReceipt,
    LiveConsent,
    LiveEvent,
    LiveParticipant,
    LivePeer,
    LiveSessionView,
    LiveSignal,
    LiveTicket,
    LiveTranscriptSpan,
    MediaState,
    TranscriptRevision,
)
from services.streaming.settings import LiveSettings
from src.security.pii_redactor import redact_pii


@dataclass
class Participant:
    peer: LivePeer
    microphone: bool = False
    analysis: bool = False
    media_state: MediaState = "new"
    queue: asyncio.Queue[LiveEvent] | None = None
    track: SpeechWindows = field(default_factory=SpeechWindows)
    reconciler: Reconciler = field(default_factory=Reconciler)
    samples: int = 0
    sequence: int = 0
    anchor: float | None = None

    @property
    def buffer(self) -> bytearray:
        return self.track.buffer


@dataclass
class Room:
    id: str
    tenant: str
    initiator: str
    participants: dict[str, Participant]
    deadline: float
    revision: int = 0
    capture_started: float | None = None


@dataclass
class Ticket:
    room_id: str
    identity: Principal
    deadline: float
    auth_deadline: float


@dataclass
class Work:
    room: Room
    user_id: str
    revision: int
    window: Window
    ready_at: float
    attempt: int = 0


class LiveBroker:
    """All room methods run synchronously on one application event loop, never a DB thread."""

    def __init__(self, settings: LiveSettings, asr: ASRPort | None) -> None:
        self.settings, self.asr = settings, asr
        self.rooms: dict[str, Room] = {}
        self.tickets: dict[str, Ticket] = {}
        self.work: asyncio.Queue[Work] = asyncio.Queue(maxsize=settings.pending_windows)
        self.worker: asyncio.Task[None] | None = None
        self.coalesced = 0

    def enabled(self) -> None:
        if not self.settings.enabled:
            raise HTTPException(503)

    def reap(self) -> None:
        now = time.monotonic()
        for room in list(self.rooms.values()):
            if room.deadline <= now:
                self.end(room, "expired")
        self.tickets = {key: t for key, t in self.tickets.items() if t.deadline > now}

    def room(self, room_id: str, identity: Principal) -> Room:
        self.enabled()
        self.reap()
        room = self.rooms.get(room_id)
        if (
            room is None
            or room.tenant != identity.tenant_id
            or identity.user_id not in room.participants
        ):
            raise HTTPException(404)
        return room

    def allowed(self, room: Room) -> bool:
        return self.asr is not None and all(
            p.microphone and p.analysis and p.queue is not None and p.media_state == "connected"
            for p in room.participants.values()
        )

    def view(self, room: Room) -> LiveSessionView:
        return LiveSessionView(
            id=UUID(room.id),
            initiator_user_id=UUID(room.initiator),
            participants=[
                LiveParticipant(
                    user_id=p.peer.user_id,
                    display_name=p.peer.display_name,
                    microphone=p.microphone,
                    analysis=p.analysis,
                    socket_connected=p.queue is not None,
                    media_state=p.media_state,
                    accepted_samples=p.samples,
                )
                for p in room.participants.values()
            ],
            consent_revision=room.revision,
            capture_allowed=self.allowed(room),
            remaining_seconds=max(0, int(room.deadline - time.monotonic())),
        )

    def create(self, identity: Principal, me: LivePeer, peer: LivePeer) -> LiveSessionView:
        self.enabled()
        self.reap()
        if me.user_id == peer.user_id:
            raise HTTPException(422)
        users = {str(me.user_id), str(peer.user_id)}
        if any(
            room.tenant == identity.tenant_id and users.intersection(room.participants)
            for room in self.rooms.values()
        ):
            raise HTTPException(409)
        if len(self.rooms) >= self.settings.max_sessions:
            raise HTTPException(429)
        room = Room(
            str(uuid4()),
            identity.tenant_id,
            identity.user_id,
            {str(p.user_id): Participant(p) for p in (me, peer)},
            time.monotonic() + self.settings.ttl_seconds,
        )
        self.rooms[room.id] = room
        return self.view(room)

    def reset_capture(self, room: Room) -> None:
        room.revision += 1
        room.capture_started = time.monotonic() if self.allowed(room) else None
        for p in room.participants.values():
            p.track = SpeechWindows()
            p.reconciler = Reconciler()
            p.samples, p.sequence, p.anchor = 0, 0, None
        self.purge_work(room)

    def purge_work(self, room: Room) -> None:
        for _ in range(self.work.qsize()):
            job = self.work.get_nowait()
            self.work.task_done()
            if job.room is not room:
                self.work.put_nowait(job)

    def broadcast(self, room: Room, event: LiveEvent) -> None:
        for p in room.participants.values():
            if p.queue is not None:
                try:
                    p.queue.put_nowait(event)
                except asyncio.QueueFull:
                    self.end(room, "backpressure")
                    return

    def notify(self, room: Room) -> None:
        self.broadcast(room, LiveEvent(type="session", session=self.view(room)))

    def consent(self, room: Room, identity: Principal, consent: LiveConsent) -> LiveSessionView:
        p = room.participants[identity.user_id]
        if consent.analysis and self.asr is None:
            raise HTTPException(503)
        if p.queue is None:
            raise HTTPException(409)
        if not consent.microphone:
            self.end(room, "ended")
            raise HTTPException(409)
        p.microphone, p.analysis = consent.microphone, consent.analysis
        self.reset_capture(room)
        self.notify(room)
        return self.view(room)

    def issue(self, room: Room, identity: Principal, expires: float) -> LiveTicket:
        if room.participants[identity.user_id].queue is not None:
            raise HTTPException(409)
        self.tickets = {
            k: t
            for k, t in self.tickets.items()
            if (t.room_id, t.identity.user_id) != (room.id, identity.user_id)
        }
        now = time.monotonic()
        auth_deadline = now + max(0, expires - time.time())
        if auth_deadline <= now:
            raise HTTPException(401)
        secret = secrets.token_urlsafe(32)
        self.tickets[secret] = Ticket(
            room.id, identity, min(now + 30, auth_deadline), auth_deadline
        )
        return LiveTicket(ticket=secret, expires_in_seconds=min(30, int(auth_deadline - now)))

    def attach(self, room_id: str, secret: str) -> tuple[Room, Ticket, asyncio.Queue[LiveEvent]]:
        self.enabled()
        self.reap()
        ticket = self.tickets.pop(secret, None)
        if ticket is None or ticket.room_id != room_id:
            raise HTTPException(401)
        room = self.room(room_id, ticket.identity)
        participant = room.participants[ticket.identity.user_id]
        if participant.queue is not None:
            raise HTTPException(409)
        participant.queue = asyncio.Queue(maxsize=32)
        self.notify(room)
        return room, ticket, participant.queue

    def signal(self, room: Room, identity: Principal, signal: LiveSignal) -> None:
        if (
            signal.kind == "offer"
            and identity.user_id != room.initiator
            or signal.kind == "answer"
            and identity.user_id == room.initiator
        ):
            raise HTTPException(403)
        if not all(p.microphone and p.queue is not None for p in room.participants.values()):
            raise HTTPException(409)
        other = next(p for key, p in room.participants.items() if key != identity.user_id)
        if other.queue is None:
            raise HTTPException(409)
        try:
            other.queue.put_nowait(
                LiveEvent(type="signal", sender_user_id=UUID(identity.user_id), signal=signal)
            )
        except asyncio.QueueFull:
            self.end(room, "backpressure")

    def connection(self, room: Room, identity: Principal, state: MediaState) -> None:
        participant = room.participants[identity.user_id]
        if participant.media_state != state:
            participant.media_state = state
            self.reset_capture(room)
            self.notify(room)

    def audio(
        self,
        room: Room,
        identity: Principal,
        pcm: bytes,
        sequence: int,
        start_sample: int,
        revision: int,
    ) -> AudioReceipt:
        if not self.allowed(room):
            raise HTTPException(403)
        p = room.participants[identity.user_id]
        if revision != room.revision or sequence != p.sequence or start_sample != p.samples:
            raise HTTPException(409)
        if len(pcm) != 32000:
            raise HTTPException(422)
        # At most 3 seconds ahead of wall time: bounded burst allowance, not an upload API.
        if (
            room.capture_started is None
            or p.samples / 16000 > time.monotonic() - room.capture_started + 3
        ):
            raise HTTPException(429)
        if p.anchor is None:
            p.anchor = max(0, time.monotonic() - (room.capture_started or time.monotonic()) - 1)
        windows = p.track.push(pcm, start_sample)
        p.samples += 16000
        p.sequence += 1
        for window in windows:
            self.schedule(Work(room, identity.user_id, revision, window, time.perf_counter()))
        return AudioReceipt(
            sequence=sequence,
            accepted_samples=p.samples,
            buffered_samples=len(p.buffer) // 2,
            consent_revision=revision,
        )

    def pause_analysis(self, room: Room, code: str) -> None:
        for participant in room.participants.values():
            participant.analysis = False
        self.reset_capture(room)
        self.notify(room)
        self.broadcast(room, LiveEvent.model_validate({"type": "notice", "code": code}))

    def schedule(self, job: Work) -> None:
        pending = []
        while not self.work.empty():
            pending.append(self.work.get_nowait())
            self.work.task_done()
        replaced = False
        for i, old in enumerate(pending):
            if (old.room.id, old.user_id, old.window.utterance_id) == (
                job.room.id,
                job.user_id,
                job.window.utterance_id,
            ):
                if not old.window.final and (
                    job.window.final or job.window.end_sample >= old.window.end_sample
                ):
                    pending[i] = job
                replaced = True
                self.coalesced += 1
                break
        overflow = not replaced and len(pending) >= self.work.maxsize
        if not replaced and not overflow:
            pending.append(job)
        for queued in pending:
            self.work.put_nowait(queued)
        if overflow:
            self.pause_analysis(job.room, "backpressure")
            raise HTTPException(429)
        if self.worker is None or self.worker.done():
            self.worker = asyncio.create_task(self.process())

    def flush(self, room: Room, identity: Principal, revision: int) -> int:
        if not self.allowed(room):
            raise HTTPException(403)
        if room.revision != revision:
            raise HTTPException(409)
        window = room.participants[identity.user_id].track.flush()
        if window is not None:
            self.schedule(Work(room, identity.user_id, revision, window, time.perf_counter()))
        return int(window is not None)

    def valid_work(self, job: Work) -> bool:
        return (
            self.rooms.get(job.room.id) is job.room
            and job.room.revision == job.revision
            and self.allowed(job.room)
        )

    def publish(
        self,
        job: Work,
        words: list[Word],
        timing: Literal["word", "interpolated"],
        elapsed: float,
        *,
        failed: bool = False,
    ) -> None:
        p = job.room.participants[job.user_id]
        revision = p.reconciler.apply(job.window, words, failed=failed)
        if revision is None:
            return
        text = redact_pii(revision.text).redacted_text[:4000]
        anchor = p.anchor or 0.0
        update = TranscriptRevision(
            utterance_id=UUID(revision.utterance_id),
            revision=revision.revision,
            state=revision.state,
            text=text,
            start_seconds=anchor + revision.start,
            end_seconds=anchor + revision.end,
            agreed_prefix_words=revision.agreed_prefix_words,
            reason=revision.reason,
            timing=timing,
            window_start_seconds=anchor + job.window.start_sample / 16000,
            window_end_seconds=anchor + job.window.end_sample / 16000,
            ready_to_event_ms=(time.perf_counter() - job.ready_at) * 1000,
            inference_ms=elapsed,
        )
        self.broadcast(
            job.room,
            LiveEvent(
                type="transcript",
                sender_user_id=UUID(job.user_id),
                segments=[
                    LiveTranscriptSpan(
                        start_seconds=update.start_seconds,
                        end_seconds=update.end_seconds,
                        text=text,
                    )
                ]
                if update.state == "final" and text
                else [],
                consent_revision=job.revision,
                transcript=update,
            ),
        )

    async def process(self) -> None:
        while not self.work.empty():
            job = self.work.get_nowait()
            timing: Literal["word", "interpolated"] = (
                "word" if isinstance(self.asr, WordASRPort) else "interpolated"
            )
            try:
                self.reap()
                if not self.valid_work(job) or self.asr is None:
                    continue
                started = time.perf_counter()
                words, timing = await asyncio.to_thread(recognize_words, self.asr, job.window.pcm)
                elapsed = (time.perf_counter() - started) * 1000
                self.reap()
                if self.valid_work(job):
                    self.publish(job, words, timing, elapsed)
            except Exception:
                if self.valid_work(job):
                    self.publish(job, [], timing, 0.0, failed=True)
                    if job.attempt == 0:
                        self.broadcast(job.room, LiveEvent(type="notice", code="analysis_retrying"))
                        try:
                            self.schedule(replace(job, attempt=1))
                        except HTTPException:
                            pass
                    else:
                        self.pause_analysis(job.room, "analysis_failed")
            finally:
                self.work.task_done()

    def end(self, room: Room, code: str) -> None:
        if self.rooms.pop(room.id, None) is None:
            return
        self.tickets = {key: t for key, t in self.tickets.items() if t.room_id != room.id}
        self.reset_capture(room)
        for p in room.participants.values():
            p.microphone, p.analysis, p.media_state = False, False, "closed"
            if p.queue is not None:
                while not p.queue.empty():
                    p.queue.get_nowait()
                p.queue.put_nowait(LiveEvent.model_validate({"type": "terminated", "code": code}))
                p.queue = None

    async def close(self) -> None:
        for room in list(self.rooms.values()):
            self.end(room, "ended")
        if self.worker is not None:
            await self.worker
