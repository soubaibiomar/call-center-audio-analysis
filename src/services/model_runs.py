"""Content-free inference receipts, scoped to one graph execution."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ModelRun(BaseModel):
    provider: str
    model_id: str
    # A tag is the configured version; a registry digest is not inferred from it.
    model_version: str
    prompt_revision: str
    schema_name: str
    attempt: int = Field(ge=1)
    retries: int = Field(ge=0)
    latency_ms: float = Field(ge=0)
    structured_output: Literal["valid", "invalid", "error"]
    error_code: str | None = None
    fallback: Literal["none"] = "none"


_runs: ContextVar[list[ModelRun] | None] = ContextVar("model_runs", default=None)


@contextmanager
def capture_model_runs() -> Iterator[list[ModelRun]]:
    runs: list[ModelRun] = []
    token = _runs.set(runs)
    try:
        yield runs
    finally:
        _runs.reset(token)


def record_model_run(run: ModelRun) -> None:
    runs = _runs.get()
    if runs is not None:
        runs.append(run)
    # No transcript, response, exception body, endpoint or identity is logged.
    logger.info("model_inference %s", run.model_dump_json())
