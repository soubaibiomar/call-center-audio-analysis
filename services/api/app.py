"""Versioned HTTP boundary around the shared synchronous analysis service.

Run: uvicorn services.api.app:create_app --factory --host 127.0.0.1 --port 8000
"""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import BoundedSemaphore
from typing import Annotated, Any, Literal, cast
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Select, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from services.api.analysis import analyze_call
from services.api.auth import Authenticator, Principal
from services.api.db.models import Call, Job
from services.api.routes.call_reviews import call_reviews_router
from services.api.routes.jobs import jobs_router
from services.api.routes.reviews import reviews_router
from services.api.routes.workspace import workspace_router
from services.api.schemas import (
    CallItem,
    CallPage,
    Dashboard,
    ErrorResponse,
    Health,
    Identity,
    JobStatus,
    Report,
)
from services.api.settings import ApiSettings
from services.streaming.asr import ASRPort, LocalWhisper
from services.streaming.broker import LiveBroker
from services.streaming.contracts import LiveEvent, SocketAuth, SocketMessage
from services.streaming.routes import live_routers
from services.streaming.settings import LiveSettings
from services.workers.jobs import owned_job
from services.workers.settings import QueueSettings
from src.database.connection import get_engine, init_db, session_scope
from src.database.models import CallRecord
from src.database.scope import database_identity
from src.graph.state import CallReport, QAScoreResult, TranscriptionResult
from src.services.contracts import AnalysisPort, AnalysisRequest
from src.utils.audio import detect_audio_format, validate_audio_file
from src.utils.audio_workspace import audio_workspace

ERROR_MESSAGES = {
    409: ("idempotency_conflict", "This request key was used for different input"),
    400: ("invalid_request", "The request could not be read"),
    401: ("unauthenticated", "A valid bearer token is required"),
    403: ("forbidden", "User access has not been enabled"),
    404: ("not_found", "The requested resource was not found"),
    405: ("method_not_allowed", "This method is not supported"),
    413: ("upload_too_large", "The audio upload exceeds the configured limit"),
    415: ("unsupported_audio", "A supported audio file is required"),
    422: ("invalid_input", "Request fields did not pass validation"),
    429: ("analysis_busy", "Analysis is busy; try again later"),
    500: ("internal_error", "The request could not be completed"),
    502: ("analysis_failed", "Analysis could not be completed"),
    503: ("unavailable", "The required service is not ready"),
}


def error_response(status: int, request_id: str) -> JSONResponse:
    code, message = ERROR_MESSAGES.get(status, ERROR_MESSAGES[500])
    headers = {"Cache-Control": "no-store", "X-Request-ID": request_id}
    if status == 401:
        headers["WWW-Authenticate"] = "Bearer"
    if status in {429, 503}:
        headers["Retry-After"] = "1"
    return JSONResponse(
        {
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
                "retryable": status in {429, 502, 503},
            }
        },
        status_code=status,
        headers=headers,
    )


class Boundary:
    """Authenticate before multipart parsing; cap even chunked request bodies."""

    def __init__(self, app: ASGIApp, auth: Authenticator, max_body: int) -> None:
        self.app, self.auth, self.max_body = app, auth, max_body

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        state = scope.setdefault("state", {})
        state["request_id"] = str(uuid4())
        started = False

        async def checked_send(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                message["headers"] = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() not in {b"cache-control", b"x-request-id"}
                ] + [
                    (b"cache-control", b"no-store"),
                    (b"x-request-id", state["request_id"].encode()),
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                ]
            await send(message)

        consumed = 0

        async def checked_receive() -> Message:
            nonlocal consumed
            message = await receive()
            if message["type"] == "http.request":
                consumed += len(message.get("body", b""))
                if consumed > self.max_body:
                    raise HTTPException(413)
            return message

        try:
            if scope["path"] == "/api/v1" or scope["path"].startswith("/api/v1/"):
                request = Request(scope)
                state["principal"] = await run_in_threadpool(
                    self.auth.authenticate, request.headers.get("authorization", "")
                )
                length = request.headers.get("content-length")
                if length is not None:
                    try:
                        size = int(length)
                    except ValueError as exc:
                        raise HTTPException(400) from exc
                    if size < 0:
                        raise HTTPException(400)
                    if size > self.max_body:
                        raise HTTPException(413)
            await self.app(scope, checked_receive, checked_send)
        except StarletteHTTPException as exc:
            if started:
                raise
            await error_response(exc.status_code, state["request_id"])(scope, receive, send)
        except SQLAlchemyError:
            if started:
                raise
            await error_response(503, state["request_id"])(scope, receive, send)
        except Exception:
            if started:
                raise
            await error_response(500, state["request_id"])(scope, receive, send)


_bearer = HTTPBearer(auto_error=False)


def principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    # The ASGI boundary verifies the token before any request body is parsed.
    return cast(Principal, request.state.principal)


PrincipalDependency = Annotated[Principal, Depends(principal)]


def create_app(
    settings: ApiSettings | None = None,
    engine: Engine | None = None,
    analysis_factory: Callable[[], AnalysisPort] | None = None,
    queue_settings: QueueSettings | None = None,
    live_settings: LiveSettings | None = None,
    live_asr: ASRPort | None = None,
) -> FastAPI:
    settings = settings or ApiSettings.from_env()
    owned_engine = engine is None
    if engine is None and settings.database_url:
        engine = get_engine(settings.database_url)
    if engine is not None and engine.dialect.name != "postgresql":
        raise ValueError("The authenticated API requires PostgreSQL tenant isolation")
    auth = Authenticator(settings, engine)
    analysis: AnalysisPort | None = None
    gate = BoundedSemaphore(1)
    live_settings = live_settings or LiveSettings.from_env()
    if live_asr is None and live_settings.enabled and live_settings.model_path:
        live_asr = LocalWhisper(live_settings.model_path)
    live = LiveBroker(live_settings, live_asr)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await live.close()
            if engine is not None and owned_engine:
                engine.dispose()

    app = FastAPI(
        title="Adaptive Call Center Intelligence",
        version="0.9.0",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.add_middleware(Boundary, auth=auth, max_body=settings.max_upload_bytes + 65536)
    app.state.live_broker = live

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return error_response(exc.status_code, request.state.request_id)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(422, request.state.request_id)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        return error_response(503, request.state.request_id)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return error_response(500, request.state.request_id)

    @app.get("/health", response_model=Health)
    def health() -> Health:
        return Health(status="ok")

    @app.get("/ready", response_model=Health, responses={503: {"model": ErrorResponse}})
    def ready() -> Health:
        if engine is None or not settings.auth_configured:
            raise HTTPException(503)
        try:
            init_db(engine)
        except RuntimeError as exc:
            raise HTTPException(503) from exc
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return Health(status="ready")

    router = APIRouter(
        prefix="/api/v1", responses={status: {"model": ErrorResponse} for status in ERROR_MESSAGES}
    )

    def db() -> Engine:
        if engine is None:
            raise HTTPException(503)
        return engine

    live_http, live_sockets = live_routers(live, db)
    router.include_router(live_http, dependencies=[Depends(principal)])
    app.include_router(live_sockets)

    def call_query(identity: Principal) -> Select[tuple[Call]]:
        query = select(Call).where(Call.tenant_id == identity.tenant_id)
        if identity.owner_filter:
            query = query.where(Call.owner_user_id == identity.owner_filter)
        return query

    def read_report(call_id: UUID, identity: Principal) -> CallReport:
        with session_scope(db(), tenant_id=identity.tenant_id) as session:
            call = session.scalar(call_query(identity).where(Call.id == str(call_id)))
            if call is None:
                raise HTTPException(404)
            record = session.scalar(
                select(CallRecord).where(CallRecord.call_id == call.legacy_call_id)
            )
            if record is None or record.report_json is None:
                raise HTTPException(404)
            return CallReport.model_validate_json(record.report_json)

    @router.get("/me", response_model=Identity)
    def me(identity: PrincipalDependency) -> Identity:
        return Identity(
            tenant_id=UUID(identity.tenant_id),
            user_id=UUID(identity.user_id),
            role=cast(Any, identity.role),
        )

    @router.get("/calls", response_model=CallPage)
    def calls(
        identity: PrincipalDependency,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0, le=10000)] = 0,
        status: Literal["completed", "failed", "flagged_for_review"] | None = None,
        language: Annotated[str | None, Query(max_length=30)] = None,
        sort: Literal["processed_at", "qa_score"] = "processed_at",
        direction: Literal["asc", "desc"] = "desc",
    ) -> CallPage:
        with session_scope(db(), tenant_id=identity.tenant_id) as session:
            query = call_query(identity)
            if status is not None:
                query = query.where(Call.status == status)
            if language is not None:
                query = query.where(Call.language == language)
            total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
            column = Call.qa_score if sort == "qa_score" else Call.processed_at
            ordering = column.asc() if direction == "asc" else column.desc()
            items = session.scalars(
                query.order_by(ordering.nulls_last(), Call.id).limit(limit).offset(offset)
            )
            return CallPage(
                items=[CallItem.model_validate(item) for item in items],
                total=total,
                limit=limit,
                offset=offset,
            )

    @router.get("/calls/{call_id}", response_model=CallItem)
    def call_detail(call_id: UUID, identity: PrincipalDependency) -> CallItem:
        with session_scope(db(), tenant_id=identity.tenant_id) as session:
            call = session.scalar(call_query(identity).where(Call.id == str(call_id)))
            if call is None:
                raise HTTPException(404)
            return CallItem.model_validate(call)

    @router.get("/calls/{call_id}/transcript", response_model=TranscriptionResult)
    def transcript(call_id: UUID, identity: PrincipalDependency) -> TranscriptionResult:
        return read_report(call_id, identity).transcription

    @router.get("/calls/{call_id}/qa", response_model=QAScoreResult)
    def qa(call_id: UUID, identity: PrincipalDependency) -> QAScoreResult:
        return read_report(call_id, identity).qa_scores

    @router.get("/calls/{call_id}/report", response_model=Report)
    def report(call_id: UUID, identity: PrincipalDependency) -> Report:
        return Report.from_report(
            read_report(call_id, identity), include_synthetic_emotion=settings.synthetic_data
        )

    @router.get(
        "/calls/{call_id}/report.pdf",
        response_class=Response,
        responses={200: {"content": {"application/pdf": {}}}},
    )
    def pdf(call_id: UUID, identity: PrincipalDependency) -> Response:
        from src.agents.report import generate_report_pdf

        return Response(
            generate_report_pdf(read_report(call_id, identity)),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="report-{call_id}.pdf"'},
        )

    @router.get("/dashboard", response_model=Dashboard)
    def dashboard(identity: PrincipalDependency) -> Dashboard:
        with session_scope(db(), tenant_id=identity.tenant_id) as session:
            rows = session.execute(
                select(
                    Call.status, func.count(), func.sum(Call.qa_score), func.count(Call.qa_score)
                )
                .where(Call.id.in_(call_query(identity).with_only_columns(Call.id)))
                .group_by(Call.status)
            ).all()
            counts = {row[0]: row[1] for row in rows}
            count_scores = sum(row[3] for row in rows)
            return Dashboard(
                total_calls=sum(counts.values()),
                completed=counts.get("completed", 0),
                failed=counts.get("failed", 0),
                flagged_for_review=counts.get("flagged_for_review", 0),
                average_qa_score=sum(row[2] or 0 for row in rows) / count_scores
                if count_scores
                else None,
                scope="owned_calls" if identity.owner_filter else "tenant",
            )

    @router.get("/jobs/{job_id}", response_model=JobStatus)
    def job(job_id: UUID, identity: PrincipalDependency) -> JobStatus:
        durable = owned_job(db(), identity, str(job_id))
        if durable is not None:
            return durable
        with session_scope(db(), tenant_id=identity.tenant_id) as session:
            item = session.scalar(
                select(Job).where(
                    Job.id == str(job_id),
                    Job.tenant_id == identity.tenant_id,
                    Job.call_id.in_(call_query(identity).with_only_columns(Call.id)),
                )
            )
            if item is None:
                raise HTTPException(404)
            return JobStatus(
                id=UUID(item.id),
                call_id=UUID(item.call_id),
                status=item.status,
                attempts=item.attempts,
            )

    def invoke(
        path: Path, caller: str | None, department: str | None, identity: Principal
    ) -> Report:
        nonlocal analysis
        if not gate.acquire(blocking=False):
            raise HTTPException(429)
        try:
            with (
                database_identity(identity.tenant_id, identity.user_id),
                audio_workspace(path.parent),
            ):
                if analysis is None:
                    if analysis_factory is not None:
                        analysis = analysis_factory()
                    else:
                        from src.graph.workflow import compile_workflow
                        from src.security.audit import AuditLogger
                        from src.services.analysis import AnalysisService
                        from src.utils.config import load_config

                        analysis = AnalysisService(
                            compile_workflow(load_config(), db_engine=db()),
                            db(),
                            AuditLogger(engine=db()),
                        )
                result = analyze_call(
                    analysis, AnalysisRequest(path, caller, department, downloads=False)
                )
                return Report.from_report(result)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(502) from exc
        finally:
            gate.release()

    @router.post("/calls/analyze", response_model=Report, status_code=201)
    async def analyze(
        identity: PrincipalDependency,
        audio: Annotated[UploadFile, File()],
        caller_id: Annotated[str | None, Form(max_length=255)] = None,
        department: Annotated[str | None, Form(max_length=255)] = None,
    ) -> Report:
        try:
            data = await audio.read(settings.max_upload_bytes + 1)
            if len(data) > settings.max_upload_bytes:
                raise HTTPException(413)
            if not validate_audio_file(data, "upload").is_valid:
                raise HTTPException(415)
            with TemporaryDirectory(prefix="project28-api-") as folder:
                path = Path(folder) / f"{uuid4()}.{detect_audio_format(data)}"
                path.write_bytes(data)
                return await run_in_threadpool(invoke, path, caller_id, department, identity)
        finally:
            await audio.close()

    router.include_router(
        jobs_router(db, queue_settings or QueueSettings.from_env(), settings.max_upload_bytes),
        dependencies=[Depends(principal)],
    )
    router.include_router(reviews_router(db), dependencies=[Depends(principal)])
    router.include_router(call_reviews_router(db), dependencies=[Depends(principal)])
    router.include_router(
        workspace_router(db, call_query, settings.synthetic_data, live_settings.enabled),
        dependencies=[Depends(principal)],
    )
    app.include_router(router)
    review_assets = Path(__file__).resolve().parents[2] / "apps/web/dist"
    if review_assets.is_dir():
        app.mount("/review-ui", StaticFiles(directory=review_assets, html=True), name="review-ui")
    workspace_assets = Path(__file__).resolve().parents[2] / "apps/web/dist-workspace"
    if workspace_assets.is_dir():
        app.mount(
            "/workspace", StaticFiles(directory=workspace_assets, html=True), name="workspace"
        )
    # WebSocket frames are not inferred by OpenAPI; publish their actual Pydantic contracts.
    schema = app.openapi()
    for contract in (LiveEvent, SocketAuth, SocketMessage):
        definition = contract.model_json_schema(ref_template="#/components/schemas/{model}")
        schema["components"]["schemas"].update(definition.pop("$defs", {}))
        schema["components"]["schemas"][contract.__name__] = definition
    schema["x-live-websocket"] = {
        "path": "/api/v1/live/socket/{room_id}",
        "authentication": "SocketAuth: single-use HTTP-issued ticket in first text frame",
        "client_frame": "SocketMessage",
        "server_frame": "LiveEvent",
        "media": "WebRTC peer audio; separate authorized HTTP PCM capture; no binary WS media",
    }
    return app
