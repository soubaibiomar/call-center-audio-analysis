from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.engine import Engine

from src.database.connection import get_engine, init_db, session_scope
from src.database.models import AuditLogEntry


class AuditLogger:
    def __init__(
        self,
        db_path: str | None = None,
        encryption_key: str | None = None,
        engine: Engine | None = None,
    ) -> None:
        if engine is not None:
            self.engine = engine
        else:
            if db_path is None:
                raise ValueError("AuditLogger requires an engine or db_path")
            self.engine = get_engine(db_path, encryption_key)
            init_db(self.engine)

    def log(
        self, call_id: str, action: str, user: str, details: dict[str, object] | None = None
    ) -> None:
        with session_scope(self.engine) as session:
            entry = AuditLogEntry(
                call_id=call_id,
                action=action,
                user=user,
                timestamp=datetime.now(),
                details=json.dumps(details) if details else None,
            )
            session.add(entry)
