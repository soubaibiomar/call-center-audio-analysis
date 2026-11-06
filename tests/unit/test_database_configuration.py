"""Protect original SQLite operation and private PostgreSQL configuration."""

import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import inspect

from services.api.db.legacy_import import backup_sqlite, readonly_sqlite
from services.api.db.settings import database_url
from src.database.connection import get_engine, init_db


def test_online_backup_preserves_rows_and_cannot_overwrite(tmp_path: Path):
    source = tmp_path / "source.db"
    with sqlite3.connect(source) as conn:
        for name in ("call_records", "audit_log", "transcription_cache"):
            conn.execute(f"CREATE TABLE {name} (id INTEGER PRIMARY KEY)")
            conn.execute(f"INSERT INTO {name} VALUES (7)")
    snapshot = tmp_path / "backup.db"
    result = backup_sqlite(source, snapshot)
    assert result["rows"] == {"call_records": 1, "audit_log": 1, "transcription_cache": 1}
    with readonly_sqlite(snapshot) as conn:
        assert conn.execute("SELECT id FROM call_records").fetchone()[0] == 7
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("DELETE FROM call_records")
    with pytest.raises(FileExistsError):
        backup_sqlite(source, snapshot)


@pytest.mark.parametrize("as_url", [False, True])
def test_original_sqlite_backends_remain_three_tables(tmp_path: Path, as_url):
    path = tmp_path / "legacy.db"
    engine = get_engine(f"sqlite:///{path.as_posix()}" if as_url else str(path))
    init_db(engine)
    assert set(inspect(engine).get_table_names()) == {
        "call_records",
        "audit_log",
        "transcription_cache",
    }
    engine.dispose()


def test_private_url_file_and_mutually_exclusive_configuration(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL_FILE", raising=False)
    assert database_url() is None
    secret = tmp_path / "connection"
    secret.write_text("postgresql+psycopg://synthetic/fixture\n")
    monkeypatch.setenv("DATABASE_URL_FILE", str(secret))
    assert database_url() == "postgresql+psycopg://synthetic/fixture"
    monkeypatch.setenv("DATABASE_URL", "postgresql://another/fixture")
    with pytest.raises(ValueError, match="not both"):
        database_url()


def test_unsupported_database_backend_is_rejected():
    with pytest.raises(ValueError, match="Unsupported"):
        get_engine("mysql://synthetic/fixture")
