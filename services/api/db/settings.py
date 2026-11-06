"""Read private connection configuration without logging credential values."""

import os
from pathlib import Path

LEGACY_TENANT_ID = "00000000-0000-0000-0000-000000000001"
LEGACY_USER_ID = "00000000-0000-0000-0000-000000000002"
SCHEMA_REVISION = "0005_call_review"


def database_url() -> str | None:
    direct = os.environ.get("DATABASE_URL", "").strip()
    filename = os.environ.get("DATABASE_URL_FILE", "").strip()
    if direct and filename:
        raise ValueError("Set DATABASE_URL or DATABASE_URL_FILE, not both")
    if filename:
        direct = Path(filename).read_text(encoding="utf-8").strip()
    return direct or None
