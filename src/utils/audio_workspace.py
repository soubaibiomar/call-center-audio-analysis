"""Request-owned intake storage, inherited by context-aware graph execution."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

_workspace: ContextVar[Path | None] = ContextVar("audio_workspace", default=None)


def current_audio_workspace() -> Path | None:
    return _workspace.get()


@contextmanager
def audio_workspace(directory: Path) -> Iterator[None]:
    token = _workspace.set(directory)
    try:
        yield
    finally:
        _workspace.reset(token)
