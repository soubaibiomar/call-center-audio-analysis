"""Bounded signaling, consent, capture and event contracts; audio is never a WS message."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints, model_validator

from services.reviews.contracts import Strict


class LiveConfig(Strict):
    enabled: bool
    analysis_available: bool
    model_id: str | None
    transport: Literal["webrtc-direct"] = "webrtc-direct"
    sample_rate: Literal[16000] = 16000
    session_limit_seconds: int = 600


class LivePeer(Strict):
    user_id: UUID
    display_name: str


class LiveCreate(Strict):
    peer_user_id: UUID


class LiveConsent(Strict):
    microphone: bool
    analysis: bool

    @model_validator(mode="after")
    def analysis_needs_microphone(self) -> "LiveConsent":
        if self.analysis and not self.microphone:
            raise ValueError("Microphone consent is required before analysis")
        return self


MediaState = Literal["new", "connecting", "connected", "disconnected", "failed", "closed"]


class LiveParticipant(LivePeer):
    microphone: bool
    analysis: bool
    socket_connected: bool
    media_state: MediaState
    accepted_samples: int


class LiveSessionView(Strict):
    id: UUID
    initiator_user_id: UUID
    participants: list[LiveParticipant]
    consent_revision: int
    capture_allowed: bool
    remaining_seconds: int


class LiveSessions(Strict):
    items: list[LiveSessionView]


class LivePeers(Strict):
    items: list[LivePeer]


class LiveTicket(Strict):
    ticket: str
    expires_in_seconds: int


class SocketAuth(Strict):
    ticket: Annotated[str, StringConstraints(min_length=32, max_length=128)]


class LiveSignal(Strict):
    kind: Literal["offer", "answer", "ice"]
    sdp: str | None = Field(default=None, max_length=32768)
    candidate: str | None = Field(default=None, max_length=2048)
    sdp_mid: str | None = Field(default=None, max_length=64)
    sdp_mline_index: int | None = Field(default=None, ge=0, le=2)

    @model_validator(mode="after")
    def audio_only(self) -> "LiveSignal":
        if self.kind in {"offer", "answer"}:
            if not self.sdp or self.candidate is not None:
                raise ValueError("Expected audio session description")
            media = [line for line in self.sdp.splitlines() if line.startswith("m=")]
            if len(media) != 1 or not media[0].startswith("m=audio "):
                raise ValueError("Only one audio media section is allowed")
            if "a=fingerprint:sha-256 " not in self.sdp:
                raise ValueError("DTLS fingerprint is required")
        elif self.sdp is not None:
            raise ValueError("ICE messages cannot carry session descriptions")
        return self


class SocketMessage(Strict):
    type: Literal["signal", "connection", "ping"]
    signal: LiveSignal | None = None
    media_state: MediaState | None = None

    @model_validator(mode="after")
    def appropriate_fields(self) -> "SocketMessage":
        if (self.type == "signal") != (self.signal is not None):
            raise ValueError("Invalid signaling message")
        if (self.type == "connection") != (self.media_state is not None):
            raise ValueError("Invalid connection message")
        return self


class LiveTranscriptSpan(Strict):
    start_seconds: float = Field(ge=0, allow_inf_nan=False)
    end_seconds: float = Field(ge=0, allow_inf_nan=False)
    text: str = Field(max_length=4000)


class TranscriptRevision(Strict):
    utterance_id: UUID
    revision: int = Field(ge=1)
    state: Literal["provisional", "final", "failed"]
    text: str = Field(max_length=4000)
    start_seconds: float = Field(ge=0, allow_inf_nan=False)
    end_seconds: float = Field(ge=0, allow_inf_nan=False)
    agreed_prefix_words: int = Field(ge=0, le=500)
    reason: Literal["silence", "window_limit", "manual", "partial"]
    timing: Literal["word", "interpolated"]
    window_start_seconds: float = Field(ge=0, allow_inf_nan=False)
    window_end_seconds: float = Field(ge=0, allow_inf_nan=False)
    ready_to_event_ms: float = Field(ge=0, allow_inf_nan=False)
    inference_ms: float = Field(ge=0, allow_inf_nan=False)


class TranscriptFlush(Strict):
    consent_revision: int = Field(ge=0)


class FlushReceipt(Strict):
    scheduled_windows: int = Field(ge=0, le=1)


class LiveEvent(Strict):
    type: Literal["session", "signal", "transcript", "notice", "pong", "terminated"]
    session: LiveSessionView | None = None
    sender_user_id: UUID | None = None
    signal: LiveSignal | None = None
    segments: list[LiveTranscriptSpan] = Field(default_factory=list, max_length=100)
    consent_revision: int | None = None
    transcript: TranscriptRevision | None = None
    code: (
        Literal[
            "analysis_failed",
            "analysis_retrying",
            "ended",
            "disconnected",
            "expired",
            "backpressure",
        ]
        | None
    ) = None


class AudioReceipt(Strict):
    sequence: int
    accepted_samples: int
    buffered_samples: int
    consent_revision: int
