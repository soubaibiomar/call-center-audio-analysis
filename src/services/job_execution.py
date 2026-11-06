"""Optional durable-job commit hook; legacy synchronous consumers need no hook."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from src.graph.state import CallReport


@dataclass(frozen=True)
class JobExecution:
    call_id: UUID
    before_commit: Callable[[Session, CallReport], None]


_execution: ContextVar[JobExecution | None] = ContextVar("job_execution", default=None)


def current_execution() -> JobExecution | None:
    return _execution.get()


@contextmanager
def job_execution(execution: JobExecution) -> Iterator[None]:
    token = _execution.set(execution)
    try:
        yield
    finally:
        _execution.reset(token)
