"""Opt-in live transport; plaintext signaling is limited to explicit loopback origins."""

import os
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class LiveSettings:
    enabled: bool = False
    origins: tuple[str, ...] = ()
    model_path: str = ""
    ttl_seconds: int = 600
    max_sessions: int = 8
    pending_windows: int = 4

    def __post_init__(self) -> None:
        if self.enabled and os.getenv("WEB_CONCURRENCY", "1") != "1":
            raise ValueError("Ephemeral browser calling requires one ASGI worker")
        if not 10 <= self.ttl_seconds <= 600 or not 1 <= self.max_sessions <= 8:
            raise ValueError("Live session limits exceed the local demo budget")
        if not 1 <= self.pending_windows <= 4:
            raise ValueError("Pending ASR windows must remain bounded to at most four")
        if self.enabled and not self.origins:
            raise ValueError("Enabled live transport needs explicit allowed origins")
        for origin in self.origins:
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.query
                or parsed.fragment
                or parsed.path
                or origin.endswith("/")
                or parsed.scheme == "http"
                and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
            ):
                raise ValueError("Use exact HTTPS origins or explicit loopback HTTP origins")

    @classmethod
    def from_env(cls) -> "LiveSettings":
        return cls(
            enabled=os.getenv("LIVE_ENABLED", "false").lower() == "true",
            origins=tuple(
                x.strip() for x in os.getenv("LIVE_ALLOWED_ORIGINS", "").split(",") if x.strip()
            ),
            model_path=os.getenv("LIVE_ASR_MODEL_PATH", ""),
        )
