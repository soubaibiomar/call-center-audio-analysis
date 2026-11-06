"""Migration-only connectivity; no dotenv, LLM or application bootstrap."""

from alembic import context
from sqlalchemy import create_engine

from services.api.db.models import Base
from services.api.db.settings import database_url


def configure(connection):
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


connection = context.config.attributes.get("connection")
if connection is not None:
    configure(connection)
else:
    url = database_url()
    if not url:
        raise ValueError("Migration requires private DATABASE_URL or DATABASE_URL_FILE")
    engine = create_engine(url, hide_parameters=True)
    with engine.connect() as connection:
        configure(connection)
    engine.dispose()
