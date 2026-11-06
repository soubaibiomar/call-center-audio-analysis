"""Externally verified identities mapped to enabled tenant users."""

import sqlalchemy as sa
from alembic import op

revision = "0002_identity"
down_revision = "0001_platform"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "external_identities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("issuer", sa.String(512), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "user_id"], ["users.tenant_id", "users.id"]),
        sa.UniqueConstraint("tenant_id", "issuer", "subject", name="uq_external_identity"),
    )
    op.create_index("ix_external_identities_tenant_id", "external_identities", ["tenant_id"])
    op.create_index("ix_external_identities_user_id", "external_identities", ["user_id"])
    op.execute("ALTER TABLE external_identities ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE external_identities FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_scope ON external_identities "
        "USING (tenant_id=NULLIF(current_setting('app.tenant_id',true),'')) "
        "WITH CHECK (tenant_id=NULLIF(current_setting('app.tenant_id',true),''))"
    )
    op.execute(
        "DO $$ BEGIN IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='project28_app') "
        "THEN GRANT SELECT ON external_identities TO project28_app; END IF; END $$"
    )


def downgrade() -> None:
    # off does not bypass RLS: PostgreSQL raises if a policy would hide rows.
    # An owner subject to FORCE RLS must never mistake invisibility for emptiness.
    op.get_bind().execute(sa.text("SET LOCAL row_security = off"))
    if op.get_bind().execute(sa.text("SELECT EXISTS(SELECT 1 FROM external_identities)")).scalar():
        raise RuntimeError("Refusing populated downgrade of identities; restore a reviewed backup")
    op.drop_index("ix_external_identities_user_id", table_name="external_identities")
    op.drop_index("ix_external_identities_tenant_id", table_name="external_identities")
    op.drop_table("external_identities")
