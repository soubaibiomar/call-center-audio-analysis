"""Authenticated durable upload and cooperative cancellation routes."""

from collections.abc import Callable
from typing import Annotated, Literal, cast
from uuid import UUID

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile
from sqlalchemy.engine import Engine
from starlette.concurrency import run_in_threadpool

from services.api.auth import Principal
from services.api.schemas import JobStatus
from services.workers.jobs import owned_job, submit
from services.workers.settings import QueueSettings
from services.workers.storage import AudioStore, IntegrityError
from src.utils.audio import validate_audio_file


def get_identity(request: Request) -> Principal:
    return cast(Principal, request.state.principal)


def jobs_router(
    engine: Callable[[], Engine],
    settings: QueueSettings | None,
    upload_limit: int = 50 * 1024 * 1024,
) -> APIRouter:
    router = APIRouter()
    storage: AudioStore | None = None

    @router.post("/jobs", response_model=JobStatus, status_code=202)
    async def upload(
        identity: Annotated[Principal, Depends(get_identity)],
        audio: Annotated[UploadFile, File()],
        idempotency_key: Annotated[
            str, Header(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")
        ],
        queue: Annotated[Literal["cpu", "gpu"], Form()] = "cpu",
        caller_id: Annotated[str | None, Form(max_length=255)] = None,
        department: Annotated[str | None, Form(max_length=255)] = None,
    ) -> JobStatus:
        nonlocal storage
        try:
            if settings is None:
                raise HTTPException(503)
            data = await audio.read(upload_limit + 1)
            if len(data) > upload_limit:
                raise HTTPException(413)
            if not validate_audio_file(data, "upload").is_valid:
                raise HTTPException(415)
            if storage is None:
                storage = AudioStore(settings)
            return await run_in_threadpool(
                submit,
                engine(),
                storage,
                settings,
                identity,
                data,
                idempotency_key,
                queue,
                caller_id,
                department,
            )
        except (BotoCoreError, ClientError, IntegrityError) as exc:
            raise HTTPException(503) from exc
        finally:
            await audio.close()

    @router.post("/jobs/{job_id}/cancel", response_model=JobStatus, status_code=202)
    def cancel(job_id: UUID, identity: Annotated[Principal, Depends(get_identity)]) -> JobStatus:
        result = owned_job(engine(), identity, str(job_id), cancel=True)
        if result is None:
            raise HTTPException(404)
        return result

    return router
