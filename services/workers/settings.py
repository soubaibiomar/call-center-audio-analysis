"""Private queue/storage configuration; no broker or model setup on import."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID


@dataclass(frozen=True)
class QueueSettings:
    redis_url: str = field(repr=False)
    endpoint_url: str
    access_key: str = field(repr=False)
    secret_key: str = field(repr=False)
    bucket: str = "project28-audio"
    tenants: tuple[str, ...] = ()
    capacity: int = 32
    max_attempts: int = 3
    backoff_seconds: float = 5
    republish_seconds: float = 15
    region: str = "us-east-1"
    namespace: str = "project28"

    def __post_init__(self) -> None:
        value: int | float
        for name, value, maximum in (
            ("capacity", self.capacity, 10000),
            ("max_attempts", self.max_attempts, 5),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
                raise ValueError(f"{name} must be an integer between 1 and {maximum}")
        for name, value, maximum in (
            ("backoff_seconds", self.backoff_seconds, 300),
            ("republish_seconds", self.republish_seconds, 86400),
        ):
            # Chained bounded comparison also rejects NaN/infinity without overflow
            # converting an arbitrarily large JSON integer to a float.
            if (
                isinstance(value, bool)
                or not isinstance(value, int | float)
                or not 0 < value <= maximum
            ):
                raise ValueError(f"{name} must be finite and between 0 and {maximum} seconds")
        if any(not isinstance(tenant, str) for tenant in self.tenants):
            raise ValueError("Worker tenant IDs must be UUID strings")
        canonical = tuple(dict.fromkeys(str(UUID(tenant)) for tenant in self.tenants))
        object.__setattr__(self, "tenants", canonical)

    @classmethod
    def from_env(cls) -> "QueueSettings | None":
        filename = os.getenv("QUEUE_CONFIG_FILE")
        if not filename:
            return None
        data = json.loads(Path(filename).read_text(encoding="utf-8"))
        data["tenants"] = tuple(data.get("tenants", []))
        return cls(**data)
