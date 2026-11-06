"""Operator-only linking of a provisioned tenant user to an external subject."""

import argparse
from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine

from services.api.db.models import ExternalIdentity, User
from services.api.db.settings import database_url
from services.api.settings import ApiSettings
from src.database.connection import session_scope


def link_identity(engine: Engine, tenant_id: str, user_id: str, issuer: str, subject: str) -> None:
    tenant_id, user_id = str(UUID(tenant_id)), str(UUID(user_id))
    ApiSettings(issuer=issuer)
    if not issuer or len(issuer) > 512 or not 1 <= len(subject) <= 255:
        raise ValueError("A valid issuer and bounded subject are required")
    with session_scope(engine, tenant_id=tenant_id) as session:
        user = session.scalar(select(User).where(User.id == user_id, User.tenant_id == tenant_id))
        if user is None:
            raise ValueError("Provision the tenant user before linking an identity")
        mapping = session.scalar(
            select(ExternalIdentity).where(
                ExternalIdentity.tenant_id == tenant_id,
                ExternalIdentity.issuer == issuer,
                ExternalIdentity.subject == subject,
            )
        )
        if mapping is not None:
            if mapping.user_id != user_id:
                raise ValueError("Refusing to reassign an existing identity")
            return
        session.add(
            ExternalIdentity(tenant_id=tenant_id, user_id=user_id, issuer=issuer, subject=subject)
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("tenant-id", "user-id", "issuer", "subject"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    url = database_url()
    if not url:
        raise ValueError("Supply a private migration-owner database URL")
    engine = create_engine(url, hide_parameters=True)
    try:
        link_identity(engine, args.tenant_id, args.user_id, args.issuer, args.subject)
    finally:
        engine.dispose()
    print("Identity mapping verified; existing user enablement and role preserved")


if __name__ == "__main__":
    main()
