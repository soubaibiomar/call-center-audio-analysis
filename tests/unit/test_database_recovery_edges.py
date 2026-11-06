"""Regression checks for database recovery resource ownership."""

import sqlite3

import pytest

from services.api.db.legacy_import import backup_sqlite


@pytest.mark.parametrize("complete", [True, False])
def test_backup_closes_owned_connections_on_success_and_failure(tmp_path, monkeypatch, complete):
    source = tmp_path / "source.db"
    original_connect = sqlite3.connect
    connection = original_connect(source)
    for table in (
        ["call_records", "audit_log", "transcription_cache"] if complete else ["call_records"]
    ):
        connection.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY)")
    connection.commit()
    connection.close()
    owned = []

    class TrackedConnection(sqlite3.Connection):
        closed = False

        def close(self):
            self.closed = True
            super().close()

    def connect(*args, **kwargs):
        result = original_connect(*args, **kwargs, factory=TrackedConnection)
        owned.append(result)
        return result

    monkeypatch.setattr(sqlite3, "connect", connect)
    try:
        if complete:
            backup_sqlite(source, tmp_path / "snapshot.db")
        else:
            with pytest.raises(sqlite3.OperationalError):
                backup_sqlite(source, tmp_path / "snapshot.db")
        assert len(owned) == 2
        assert all(item.closed for item in owned), "Backup left SQLite connections open"
    finally:
        for item in owned:
            item.close()
