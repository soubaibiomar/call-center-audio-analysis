"""Request-local database identity; no mutable process-wide tenant state."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseIdentity:
    tenant_id: str
    user_id: str


_identity: ContextVar[DatabaseIdentity | None] = ContextVar("database_identity", default=None)


def current_identity() -> DatabaseIdentity | None:
    return _identity.get()


@contextmanager
def database_identity(tenant_id: str, user_id: str) -> Iterator[None]:
    token = _identity.set(DatabaseIdentity(tenant_id, user_id))
    try:
        yield
    finally:
        _identity.reset(token)
