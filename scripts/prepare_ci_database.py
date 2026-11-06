"""Prepare only the disposable CI PostgreSQL service, never the local project database."""

import os
import secrets
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from services.api.db.admin import provision_runtime


def main() -> None:
    if os.getenv("CI") != "true":
        raise RuntimeError("This helper is restricted to disposable CI environments")
    admin_url = "postgresql+psycopg://postgres@127.0.0.1:5432/project28_ci"
    password = secrets.token_urlsafe(32)
    engine = create_engine(admin_url, hide_parameters=True)
    try:
        with engine.begin() as connection:
            config = Config("alembic.ini")
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        provision_runtime(engine, password)
    finally:
        engine.dispose()
    folder = Path(".local")
    folder.mkdir(exist_ok=True)
    (folder / "ci-admin-url").write_text(admin_url, encoding="utf-8")
    (folder / "ci-app-url").write_text(
        make_url(admin_url)
        .set(username="project28_app", password=password)
        .render_as_string(hide_password=False),
        encoding="utf-8",
    )
    print("Disposable CI database prepared")


if __name__ == "__main__":
    main()
