"""Real PostgreSQL checks, explicitly enabled against an isolated test database."""

import hashlib
import os
import secrets
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from psycopg import sql
from sqlalchemy import create_engine, func, select, text, update
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from services.api.db import admin as database_admin
from services.api.db import legacy_import as legacy_module
from services.api.db.contracts import CallListItem
from services.api.db.legacy_import import backup_sqlite, import_backup
from services.api.db.models import (
    Base,
    Call,
    Job,
    ModelVersion,
    Review,
    Segment,
    Tenant,
    TrainingRun,
    User,
)
from services.api.db.repository import (
    expire_cache,
    expire_calls,
    scoped_calls,
    store_report,
    tenant_metrics,
)
from src.agents.report import compile_report, persist_report
from src.database.connection import get_engine, init_db, session_scope
from src.database.models import AuditLogEntry, CallRecord, TranscriptionCache
from src.graph.state import CallReport
from src.services.history import list_calls
from tests.conftest import make_intake_result, make_qa_scores, make_summary, make_transcription

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def pg_urls():
    paths = [
        os.environ.get(name)
        for name in ("PROJECT28_TEST_ADMIN_URL_FILE", "PROJECT28_TEST_APP_URL_FILE")
    ]
    if not all(paths):
        pytest.skip("Set private isolated PostgreSQL test URL files")
    return tuple(Path(path).read_text().strip() for path in paths)


@pytest.fixture
def pg_scope(pg_urls):
    admin = create_engine(pg_urls[0], hide_parameters=True)
    tenant, owner = str(uuid.uuid4()), str(uuid.uuid4())
    with Session(admin) as session, session.begin():
        session.add(Tenant(id=tenant, name="Synthetic tests", retention_days=30))
        session.flush()
        session.add(User(id=owner, tenant_id=tenant, display_name="Synthetic owner", role="agent"))
    runtime = get_engine(pg_urls[1], tenant_id=tenant)
    init_db(runtime)
    yield admin, runtime, tenant, owner
    runtime.dispose()
    admin.dispose()


def report_fixture():
    intake = make_intake_result()
    return compile_report(
        intake,
        make_transcription(call_id=intake.call_id),
        make_summary(call_id=intake.call_id),
        make_qa_scores(call_id=intake.call_id),
        "synthetic",
    )


def assign_available_ids(admin, db_engine):
    # Independent synthetic archives share a test database; preserve collision-free source IDs.
    with admin.connect() as connection, session_scope(db_engine) as session:
        for model in (CallRecord, AuditLogEntry, TranscriptionCache):
            next_id = (connection.scalar(select(func.max(model.id))) or 0) + 100
            session.execute(update(model).values(id=next_id))


def add_report(session: Session, report: CallReport, tenant: str, owner: str) -> Call:
    session.execute(text("SELECT set_config('app.tenant_id', :tenant, true)"), {"tenant": tenant})
    session.add(
        CallRecord(
            call_id=str(report.call_id),
            status=report.status,
            audio_filename="synthetic.wav",
            transcript_text=report.transcription.full_text,
            summary_json=report.summary.model_dump_json(),
            qa_scores_json=report.qa_scores.model_dump_json(),
            report_json=report.model_dump_json(),
            processed_at=report.processed_at,
        )
    )
    session.flush()
    return store_report(session, report, tenant, owner)


def test_legacy_snapshot_import_parity_and_replay(pg_scope, db_engine, tmp_path):
    admin, runtime, tenant, owner = pg_scope
    report = report_fixture()
    persist_report(report, engine=db_engine)
    with session_scope(db_engine) as session:
        session.add(
            AuditLogEntry(call_id=str(report.call_id), action="completed", user="synthetic")
        )
        session.add(
            TranscriptionCache(
                audio_hash="a" * 64, transcription_json=report.transcription.model_dump_json()
            )
        )
    snapshot = tmp_path / "backup.db"
    assign_available_ids(admin, db_engine)
    expected = backup_sqlite(Path(db_engine.url.database), snapshot)
    before = snapshot.read_bytes()
    result = import_backup(admin, snapshot, tenant_id=tenant, owner_user_id=owner)
    assert (
        result["rows"]
        == expected["rows"]
        == {"call_records": 1, "audit_log": 1, "transcription_cache": 1}
    )
    assert not result["replayed"]
    assert import_backup(admin, snapshot, tenant_id=tenant, owner_user_id=owner)["replayed"]
    assert snapshot.read_bytes() == before
    with session_scope(runtime) as session:
        calls = scoped_calls(session, tenant, owner_user_id=owner)
        assert len(calls) == 1
        assert CallListItem.model_validate(calls[0]).id == str(report.call_id)
        assert session.scalar(select(func.count()).select_from(Segment)) == len(
            report.transcription.segments
        )
        assert tenant_metrics(session, tenant).completed == 1
    assert list_calls(runtime)[0]["call_id"] == str(report.call_id)


def test_import_failure_rolls_back_every_legacy_row(pg_scope, db_engine, tmp_path):
    admin, runtime, tenant, owner = pg_scope
    with session_scope(db_engine) as session:
        session.add(
            CallRecord(
                call_id=str(uuid.uuid4()),
                status="completed",
                audio_filename="synthetic.wav",
                report_json="{}",
            )
        )
    snapshot = tmp_path / "invalid.db"
    assign_available_ids(admin, db_engine)
    backup_sqlite(Path(db_engine.url.database), snapshot)
    with pytest.raises(ValueError):
        import_backup(admin, snapshot, tenant_id=tenant, owner_user_id=owner)
    with session_scope(runtime) as session:
        assert session.scalar(select(func.count()).select_from(CallRecord)) == 0
        assert session.scalar(select(func.count()).select_from(Call)) == 0


def test_import_preserves_other_tenants_when_numeric_ids_collide(pg_scope, db_engine, tmp_path):
    admin, runtime, tenant, owner = pg_scope
    other_tenant, other_owner = str(uuid.uuid4()), str(uuid.uuid4())
    other_report = report_fixture()
    with Session(admin) as session, session.begin():
        session.add(Tenant(id=other_tenant, name="Existing archive", retention_days=30))
        session.flush()
        session.add(User(id=other_owner, tenant_id=other_tenant, display_name="Archive owner"))
        session.flush()
        add_report(session, other_report, other_tenant, other_owner)
        collision_id = session.scalar(
            select(CallRecord.id).where(CallRecord.call_id == str(other_report.call_id))
        )
    persist_report(report_fixture(), engine=db_engine)
    with session_scope(db_engine) as session:
        session.execute(update(CallRecord).values(id=collision_id))
    snapshot = tmp_path / "collision.db"
    backup_sqlite(Path(db_engine.url.database), snapshot)
    with pytest.raises(ValueError, match="numeric ID collision"):
        import_backup(admin, snapshot, tenant_id=tenant, owner_user_id=owner)
    with session_scope(runtime) as session:
        assert session.scalar(select(func.count()).select_from(CallRecord)) == 0
    with admin.connect() as connection:
        assert connection.scalar(
            select(CallRecord.call_id).where(CallRecord.id == collision_id)
        ) == str(other_report.call_id)


def test_rls_filters_unscoped_legacy_and_normalized_queries(pg_scope):
    admin, runtime, tenant, owner = pg_scope
    report = report_fixture()
    with Session(admin) as session, session.begin():
        add_report(session, report, tenant, owner)
    outsider = get_engine(
        runtime.url.render_as_string(hide_password=False), tenant_id=str(uuid.uuid4())
    )
    try:
        assert list_calls(outsider) == []
        with session_scope(outsider) as session:
            assert list(session.scalars(select(Call))) == []
        with session_scope(runtime) as session:
            assert len(list(session.scalars(select(Call)))) == 1
    finally:
        outsider.dispose()


def test_runtime_cannot_cross_tenant_write_or_execute_ddl(pg_scope):
    admin, runtime, tenant, owner = pg_scope
    with pytest.raises(DBAPIError):
        with session_scope(runtime) as session:
            session.execute(
                Base.metadata.tables["call_records"]
                .insert()
                .values(
                    call_id=str(uuid.uuid4()),
                    tenant_id=str(uuid.uuid4()),
                    status="completed",
                    audio_filename="synthetic.wav",
                    processed_at=datetime.now(),
                )
            )
    with pytest.raises(DBAPIError):
        with runtime.begin() as connection:
            connection.execute(text("CREATE TABLE forbidden_runtime_ddl (id integer)"))
    with pytest.raises(DBAPIError):
        with runtime.begin() as connection:
            connection.execute(text("DELETE FROM audit_log"))
    with pytest.raises(DBAPIError):
        with runtime.begin() as connection:
            connection.execute(text("UPDATE model_versions SET status='promoted'"))


def test_missing_tenant_context_is_default_deny(pg_scope):
    admin, runtime, tenant, owner = pg_scope
    report = report_fixture()
    with Session(admin) as session, session.begin():
        add_report(session, report, tenant, owner)
    unscoped = create_engine(runtime.url, hide_parameters=True)
    try:
        with unscoped.connect() as connection:
            assert connection.execute(text("SELECT count(*) FROM calls")).scalar() == 0
    finally:
        unscoped.dispose()


def test_composite_owner_fk_and_report_transaction_rollback(pg_scope):
    admin, runtime, tenant, owner = pg_scope
    foreign_tenant, foreign_owner = str(uuid.uuid4()), str(uuid.uuid4())
    with Session(admin) as session, session.begin():
        session.add(Tenant(id=foreign_tenant, name="Other tenant", retention_days=30))
        session.flush()
        session.add(User(id=foreign_owner, tenant_id=foreign_tenant, display_name="Other owner"))
    report = report_fixture()
    with pytest.raises(IntegrityError):
        with session_scope(runtime) as session:
            add_report(session, report, tenant, foreign_owner)
    with session_scope(runtime) as session:
        assert session.scalar(select(func.count()).select_from(CallRecord)) == 0


def test_retention_dry_run_legal_hold_and_cascade(pg_scope):
    admin, runtime, tenant, owner = pg_scope
    expired, held = report_fixture(), report_fixture()
    with Session(admin) as session, session.begin():
        for report, hold in [(expired, False), (held, True)]:
            call = add_report(session, report, tenant, owner)
            call.expires_at = datetime.now(UTC) - timedelta(days=1)
            call.legal_hold = hold
    with session_scope(runtime) as session:
        ids = expire_calls(session, tenant, before=datetime.now(UTC))
        assert ids == [str(expired.call_id)]
        assert len(scoped_calls(session, tenant)) == 2
        expire_calls(session, tenant, before=datetime.now(UTC), apply=True)
    with session_scope(runtime) as session:
        assert [call.id for call in scoped_calls(session, tenant)] == [str(held.call_id)]
        assert (
            session.scalar(
                select(func.count())
                .select_from(Segment)
                .where(Segment.call_id == str(expired.call_id))
            )
            == 0
        )


def test_populated_downgrade_is_refused(pg_scope):
    admin, runtime, tenant, owner = pg_scope
    cfg = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    with pytest.raises(RuntimeError, match="Refusing populated downgrade"):
        with admin.begin() as connection:
            cfg.attributes["connection"] = connection
            command.downgrade(cfg, "base")
    init_db(runtime)


def test_invalid_foreign_call_segment_is_rejected(pg_scope):
    admin, runtime, tenant, owner = pg_scope
    with pytest.raises(IntegrityError):
        with session_scope(runtime) as session:
            session.add(
                Segment(
                    tenant_id=tenant,
                    call_id=str(uuid.uuid4()),
                    position=0,
                    start_seconds=0,
                    end_seconds=1,
                    text="Synthetic",
                    speaker="Agent",
                    confidence=0.9,
                )
            )


def test_transaction_local_tenant_scope_does_not_leak_through_pool(pg_scope):
    admin, runtime, tenant, owner = pg_scope
    with Session(admin) as session, session.begin():
        add_report(session, report_fixture(), tenant, owner)
    with session_scope(runtime, tenant_id=str(uuid.uuid4())) as session:
        assert session.scalar(select(func.count()).select_from(CallRecord)) == 0
    with session_scope(runtime) as session:
        assert session.scalar(select(func.count()).select_from(CallRecord)) == 1


def test_raw_cache_retention_is_explicit_and_tenant_scoped(pg_scope):
    admin, runtime, tenant, owner = pg_scope
    with session_scope(runtime) as session:
        old = TranscriptionCache(
            audio_hash="b" * 64,
            transcription_json="{}",
            created_at=datetime.now() - timedelta(days=100),
        )
        session.add(old)
        session.flush()
        cache_id = old.id
    with session_scope(runtime) as session:
        assert expire_cache(session, tenant, before=datetime.now(UTC)) == [cache_id]
        assert session.scalar(select(func.count()).select_from(TranscriptionCache)) == 1
        expire_cache(session, tenant, before=datetime.now(UTC), apply=True)
    with session_scope(runtime) as session:
        assert session.scalar(select(func.count()).select_from(TranscriptionCache)) == 0


def test_platform_metadata_links_without_claiming_execution(pg_scope):
    admin, runtime, tenant, owner = pg_scope
    report = report_fixture()
    with Session(admin) as session, session.begin():
        model = ModelVersion(tenant_id=tenant, family="asr", version="synthetic-test-only")
        session.add(model)
        session.flush()
        model_id = model.id
        training = TrainingRun(
            tenant_id=tenant,
            model_version_id=model.id,
            requested_by_user_id=owner,
            dataset_version="synthetic-fixture",
        )
        session.add(training)
        session.flush()
        assert training.status == "planned" and training.metrics == {}
    with session_scope(runtime) as session:
        call = add_report(session, report, tenant, owner)
        call.model_version_id = model_id
        job = Job(tenant_id=tenant, call_id=call.id)
        review = Review(tenant_id=tenant, call_id=call.id, reviewer_user_id=owner, version=1)
        session.add_all([job, review])
        session.flush()
        assert job.status == "queued" and job.attempts == 0
        assert not review.approved_for_training
        assert CallListItem.model_validate(call).model_version_id == model_id


def test_import_rejects_wal_state_not_covered_by_main_file_hash(pg_scope, db_engine, tmp_path):
    admin, runtime, tenant, owner = pg_scope
    path = Path(db_engine.url.database)
    with admin.connect() as conn:
        row_id = (conn.scalar(select(func.max(AuditLogEntry.id))) or 0) + 100
    writer = sqlite3.connect(path)
    try:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("PRAGMA wal_autocheckpoint=0")
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        writer.execute(
            'INSERT INTO audit_log (id, call_id, action, "user", timestamp) VALUES (?, ?, ?, ?, ?)',
            (row_id, "synthetic-wal", "completed", "test", "2026-01-01 00:00:00"),
        )
        writer.commit()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == before
        assert writer.execute("SELECT count(*) FROM audit_log").fetchone()[0] == 1
        with pytest.raises(ValueError, match="standalone SQLite backup"):
            import_backup(admin, path, tenant_id=tenant, owner_user_id=owner)
        with session_scope(runtime) as session:
            assert session.scalar(select(func.count()).select_from(AuditLogEntry)) == 0
        snapshot = tmp_path / "standalone.db"
        backup_sqlite(path, snapshot)
        result = import_backup(admin, snapshot, tenant_id=tenant, owner_user_id=owner)
        assert result["rows"]["audit_log"] == 1 and not result["replayed"]
    finally:
        writer.close()


def test_import_closes_source_connection(pg_scope, db_engine, tmp_path, monkeypatch):
    admin, runtime, tenant, owner = pg_scope
    snapshot = tmp_path / "empty.db"
    backup_sqlite(Path(db_engine.url.database), snapshot)
    opened = []
    original = legacy_module.readonly_sqlite

    def capture(path):
        connection = original(path)
        opened.append(connection)
        return connection

    monkeypatch.setattr(legacy_module, "readonly_sqlite", capture)
    try:
        import_backup(admin, snapshot, tenant_id=tenant, owner_user_id=owner)
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            opened[0].execute("SELECT 1")
    finally:
        for connection in opened:
            connection.close()


def test_runtime_provisioning_rejects_role_memberships(pg_urls, monkeypatch):
    admin_url = make_url(pg_urls[0])
    assert admin_url.database.startswith("project28_step08_check_")
    token = uuid.uuid4().hex[:12]
    member, group = f"p28_review_member_{token}", f"p28_review_group_{token}"
    engine = create_engine(admin_url, hide_parameters=True)
    url = admin_url.set(drivername="postgresql").render_as_string(hide_password=False)
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(
            sql.SQL("CREATE ROLE {} NOLOGIN NOINHERIT").format(sql.Identifier(member))
        )
        connection.execute(sql.SQL("CREATE ROLE {} NOLOGIN CREATEDB").format(sql.Identifier(group)))
        connection.execute(
            sql.SQL("GRANT {} TO {}").format(sql.Identifier(group), sql.Identifier(member))
        )
    monkeypatch.setattr(database_admin, "APP_ROLE", member)
    try:
        with psycopg.connect(url, autocommit=True) as connection:
            connection.execute(
                sql.SQL("SET SESSION AUTHORIZATION {}").format(sql.Identifier(member))
            )
            connection.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(group)))
            assert connection.execute("SELECT current_user").fetchone()[0] == group
            assert connection.execute(
                "SELECT rolcreatedb FROM pg_roles WHERE rolname=current_user"
            ).fetchone()[0]
        with pytest.raises(ValueError, match="role memberships"):
            database_admin.provision_runtime(engine, secrets.token_urlsafe(36))
    finally:
        with psycopg.connect(url, autocommit=True) as connection:
            oid = connection.execute(
                "SELECT oid FROM pg_roles WHERE rolname=%s", (member,)
            ).fetchone()[0]
            assert (
                connection.execute(
                    "SELECT count(*) FROM pg_class WHERE relowner=%s", (oid,)
                ).fetchone()[0]
                == 0
            )
            connection.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(member)))
            connection.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(member)))
            connection.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(group)))
        engine.dispose()
