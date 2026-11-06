from __future__ import annotations

import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Connection, Engine, make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry

from services.api.db.settings import LEGACY_TENANT_ID, SCHEMA_REVISION
from src.database.models import Base
from src.database.scope import current_identity


def get_engine(
    db_path: str, encryption_key: str | None = None, *, tenant_id: str = LEGACY_TENANT_ID
) -> Engine:
    if db_path.startswith(("postgresql://", "postgresql+psycopg://")):
        url = make_url(db_path).set(drivername="postgresql+psycopg")
        engine = create_engine(url, pool_pre_ping=True, hide_parameters=True)

        @event.listens_for(engine, "begin")
        def tenant_scope(connection: Connection) -> None:
            identity = current_identity()
            connection.execute(
                text("SELECT set_config('app.tenant_id', :tenant, true)"),
                {"tenant": identity.tenant_id if identity else tenant_id},
            )

        return engine
    if "://" in db_path and not db_path.startswith("sqlite:///"):
        raise ValueError("Unsupported database backend")
    if db_path.startswith("sqlite:///"):
        db_path = str(make_url(db_path).database)
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    # Only attempt PRAGMA key if encryption_key is explicitly
    # provided AND not an auto-generated default (starts with check).
    # SQLCipher may not be available on all platforms.
    if encryption_key and os.environ.get("DB_ENCRYPTION_KEY"):
        try:

            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(
                dbapi_conn: sqlite3.Connection, connection_record: ConnectionPoolEntry
            ) -> None:
                cursor = dbapi_conn.cursor()
                cursor.execute(f"PRAGMA key='{encryption_key}'")
                cursor.close()

        except Exception:
            pass  # Fall back to unencrypted SQLite

    return engine


def init_db(engine: Engine) -> None:
    if engine.dialect.name == "postgresql":
        with engine.connect() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
        if revision != SCHEMA_REVISION:
            raise RuntimeError(
                "Run the reviewed Alembic migrations before starting the application"
            )
        return
    Base.metadata.create_all(engine)


_session_factories: dict[int, sessionmaker[Session]] = {}


def get_session(engine: Engine) -> Session:
    engine_id = id(engine)
    if engine_id not in _session_factories:
        _session_factories[engine_id] = sessionmaker(bind=engine)
    return _session_factories[engine_id]()


@contextmanager
def session_scope(
    engine: Engine, *, tenant_id: str | None = None
) -> Generator[Session, None, None]:
    """Context manager that auto-commits on success, rolls back on error, always closes."""
    session = get_session(engine)
    try:
        if tenant_id and engine.dialect.name == "postgresql":
            session.execute(
                text("SELECT set_config('app.tenant_id', :tenant, true)"), {"tenant": tenant_id}
            )
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
