"""Durable tenant-owned analysis requests and transactional delivery outbox."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003_jobs"
down_revision = "0002_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("owner_user_id", sa.String(36), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("audio_sha256", sa.String(64), nullable=False),
        sa.Column("audio_size", sa.Integer, nullable=False),
        sa.Column("queue", sa.String(8), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer, nullable=False),
        sa.Column("max_attempts", sa.Integer, nullable=False),
        sa.Column("caller_id", sa.String(255)),
        sa.Column("department", sa.String(255)),
        sa.Column("call_id", sa.String(36)),
        sa.Column("error_code", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_published_at", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("metrics", JSONB, nullable=False),
        sa.UniqueConstraint("tenant_id", "owner_user_id", "idempotency_key", name="uq_job_request"),
        sa.ForeignKeyConstraint(["tenant_id", "owner_user_id"], ["users.tenant_id", "users.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "call_id"], ["calls.tenant_id", "calls.id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint("queue IN ('cpu','gpu')", name="ck_analysis_queue"),
        sa.CheckConstraint(
            "status IN ('queued','running','retrying','cancelling',"
            "'finished','failed','cancelled')",
            name="ck_analysis_status",
        ),
        sa.CheckConstraint(
            "attempts >= 0 AND max_attempts BETWEEN 1 AND 5", name="ck_analysis_attempts"
        ),
    )
    op.create_index("ix_analysis_jobs_tenant_id", "analysis_jobs", ["tenant_id"])
    op.create_index(
        "ix_analysis_dispatch", "analysis_jobs", ["tenant_id", "queue", "status", "next_attempt_at"]
    )
    op.execute("ALTER TABLE analysis_jobs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE analysis_jobs FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_scope ON analysis_jobs USING "
        "(tenant_id=NULLIF(current_setting('app.tenant_id',true),'')) WITH CHECK "
        "(tenant_id=NULLIF(current_setting('app.tenant_id',true),''))"
    )
    op.execute(
        "DO $$ BEGIN IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='project28_app') "
        "THEN GRANT SELECT,INSERT,UPDATE,DELETE ON analysis_jobs TO project28_app; END IF; END $$"
    )


def downgrade() -> None:
    op.execute("SET LOCAL row_security=off")
    if op.get_bind().execute(sa.text("SELECT EXISTS(SELECT 1 FROM analysis_jobs)")).scalar():
        raise RuntimeError("Refusing populated downgrade; restore a reviewed backup")
    op.drop_table("analysis_jobs")
