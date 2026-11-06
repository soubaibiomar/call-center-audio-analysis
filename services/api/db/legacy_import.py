"""Read-only SQLite snapshots and atomic, explicitly tenant-owned PostgreSQL import."""

import argparse
import hashlib
import json
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from services.api.db.models import Base, Call, LegacyImport, Tenant, User
from services.api.db.repository import store_report
from services.api.db.settings import LEGACY_TENANT_ID, LEGACY_USER_ID, database_url
from src.graph.state import CallReport

LEGACY_TABLES = ("call_records", "audit_log", "transcription_cache")


def file_checksum(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def readonly_sqlite(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def backup_sqlite(source: Path, destination: Path) -> dict[str, Any]:
    """Use SQLite's online backup API, not a potentially inconsistent WAL file copy."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb"):
        pass  # Exclusive creation prevents accidental backup replacement.
    with (
        closing(readonly_sqlite(source)) as original,
        closing(sqlite3.connect(destination)) as snapshot,
    ):
        original.backup(snapshot)
        snapshot.commit()
        # SQLite backup can preserve a WAL-mode header; normalize only the new artifact.
        if snapshot.execute("PRAGMA journal_mode=DELETE").fetchone()[0] != "delete":
            raise ValueError("Could not produce a standalone SQLite backup")
        if snapshot.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("SQLite backup integrity check failed")
        counts = {
            name: snapshot.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0]
            for name in LEGACY_TABLES
        }
    return {"sha256": file_checksum(destination), "rows": counts}


@contextmanager
def verified_snapshot(path: Path) -> Iterator[tuple[sqlite3.Connection, str]]:
    """Pin one standalone snapshot; a main-file hash cannot identify WAL state."""
    with closing(readonly_sqlite(path)) as source:
        source.execute("BEGIN")
        # Read a page to establish the SQLite read transaction before hashing.
        source.execute("SELECT name FROM sqlite_master").fetchall()
        journal = source.execute("PRAGMA journal_mode").fetchone()[0]
        if journal == "wal" or Path(str(path) + "-wal").exists():
            raise ValueError("Import requires a standalone SQLite backup; run backup first")
        yield source, file_checksum(path)


def import_backup(
    engine: Engine,
    snapshot: Path,
    *,
    tenant_id: str = LEGACY_TENANT_ID,
    owner_user_id: str = LEGACY_USER_ID,
) -> dict[str, Any]:
    """One transaction; exact replay is a no-op; conflicting targets are refused."""
    if engine.dialect.name != "postgresql":
        raise ValueError("Legacy import requires PostgreSQL")
    counts: dict[str, int] = {}
    with (
        verified_snapshot(snapshot) as (source, digest),
        Session(engine) as session,
        session.begin(),
    ):
        session.execute(
            text("SELECT set_config('app.tenant_id', :tenant, true)"), {"tenant": tenant_id}
        )
        # Serialize imports for this tenant; concurrent replays cannot duplicate rows.
        session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:tenant, 0))"),
            {"tenant": tenant_id},
        )
        previous = session.scalar(
            select(LegacyImport).where(
                LegacyImport.tenant_id == tenant_id, LegacyImport.source_sha256 == digest
            )
        )
        if previous:
            return {"sha256": digest, "rows": previous.row_counts, "replayed": True}
        tenant = session.get(Tenant, tenant_id)
        owner = session.get(User, owner_user_id)
        if tenant is None or owner is None or owner.tenant_id != tenant_id:
            raise ValueError("Import requires a provisioned tenant and same-tenant owner")
        for name in LEGACY_TABLES:
            table = Base.metadata.tables[name]
            if session.scalar(
                select(func.count()).select_from(table).where(table.c.tenant_id == tenant_id)
            ):
                raise ValueError(
                    "Target tenant has legacy rows; refusing implicit merge or overwrite"
                )
            count = 0
            for source_row in source.execute(f'SELECT * FROM "{name}" ORDER BY id'):
                row = dict(source_row)
                for column in ("processed_at", "timestamp", "created_at"):
                    if row.get(column):
                        row[column] = datetime.fromisoformat(row[column])
                row["tenant_id"] = tenant_id
                if session.execute(select(table.c.id).where(table.c.id == row["id"])).first():
                    raise ValueError("Legacy numeric ID collision; use an isolated target")
                session.execute(table.insert().values(**row))
                # Verify every preserved legacy field, not merely total row counts.
                actual = (
                    session.execute(select(table).where(table.c.id == row["id"])).mappings().one()
                )
                if any(actual[key] != value for key, value in row.items()):
                    raise ValueError("Legacy field parity check failed")
                count += 1
                if name == "call_records":
                    if row["report_json"]:
                        report = CallReport.model_validate_json(row["report_json"])
                        if str(report.call_id) != row["call_id"]:
                            raise ValueError("Legacy report identity mismatch")
                        call = store_report(session, report, tenant_id, owner_user_id)
                        call.audio_filename = row["audio_filename"]
                    else:
                        timestamp = row["processed_at"].replace(tzinfo=UTC)
                        session.add(
                            Call(
                                id=row["call_id"],
                                tenant_id=tenant_id,
                                owner_user_id=owner_user_id,
                                legacy_call_id=row["call_id"],
                                status=row["status"],
                                audio_filename=row["audio_filename"],
                                processed_at=timestamp,
                                expires_at=timestamp + timedelta(days=tenant.retention_days),
                            )
                        )
            counts[name] = count
        session.flush()
        if file_checksum(snapshot) != digest:
            raise ValueError("SQLite snapshot changed during import; target transaction aborted")
        for name in LEGACY_TABLES:
            # Table names are the fixed allowlist above, never user input.
            session.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence('{name}', 'id'), "
                    f'COALESCE(MAX(id),1), COUNT(*) > 0) FROM "{name}"'
                )
            )
        session.add(LegacyImport(tenant_id=tenant_id, source_sha256=digest, row_counts=counts))
    return {"sha256": digest, "rows": counts, "replayed": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    backup = sub.add_parser("backup")
    backup.add_argument("source", type=Path)
    backup.add_argument("destination", type=Path)
    load = sub.add_parser("import")
    load.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    if args.action == "backup":
        result = backup_sqlite(args.source, args.destination)
    else:
        url = database_url()
        if not url:
            raise ValueError("Import requires private database URL configuration")
        engine = create_engine(url, hide_parameters=True)
        try:
            result = import_backup(engine, args.snapshot)
        finally:
            engine.dispose()
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        raise SystemExit(
            f"Legacy operation failed ({type(error).__name__}); record contents omitted"
        ) from None
