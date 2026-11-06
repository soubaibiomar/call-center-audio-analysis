"""Immutable source snapshots and append-only call annotation decisions."""

# ruff: noqa: E501
import sqlalchemy as sa
from alembic import op

revision = "0005_call_review"
down_revision = "0004_emotion"
branch_labels = None
depends_on = None
TABLE_DDL = [
    """
CREATE TABLE call_annotations (
	call_id VARCHAR(36) NOT NULL,
	original JSONB NOT NULL,
	original_digest VARCHAR(64) NOT NULL,
	source_digest VARCHAR(64) NOT NULL,
	source_attestation VARCHAR(500) NOT NULL,
	group_keys JSONB NOT NULL,
	partition VARCHAR(12) NOT NULL,
	consent_to_train BOOLEAN NOT NULL,
	consent_evidence VARCHAR(300) NOT NULL,
	payload JSONB NOT NULL,
	state VARCHAR(16) NOT NULL,
	revision INTEGER NOT NULL,
	author_id VARCHAR(36),
	submitter_id VARCHAR(36),
	approver_id VARCHAR(36),
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	id VARCHAR(36) NOT NULL,
	tenant_id VARCHAR(36) NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_call_annotation_tenant UNIQUE (tenant_id, id),
	CONSTRAINT uq_call_annotation_source UNIQUE (tenant_id, call_id),
	FOREIGN KEY(tenant_id, call_id) REFERENCES calls (tenant_id, id) ON DELETE CASCADE,
	FOREIGN KEY(tenant_id, author_id) REFERENCES users (tenant_id, id),
	FOREIGN KEY(tenant_id, submitter_id) REFERENCES users (tenant_id, id),
	FOREIGN KEY(tenant_id, approver_id) REFERENCES users (tenant_id, id),
	CONSTRAINT ck_call_annotation_partition CHECK (partition IN ('train','evaluation')),
	CONSTRAINT ck_call_annotation_consent CHECK (partition='train' OR NOT consent_to_train),
	CONSTRAINT ck_call_annotation_state CHECK (revision>0 AND state IN ('draft','submitted','approved','rejected')),
	CONSTRAINT ck_call_annotation_independence CHECK (state<>'approved' OR (approver_id IS NOT NULL AND author_id IS NOT NULL AND submitter_id IS NOT NULL AND approver_id<>author_id AND approver_id<>submitter_id)),
	FOREIGN KEY(tenant_id) REFERENCES tenants (id)
)

""",
    """CREATE INDEX ix_call_annotations_tenant_id ON call_annotations (tenant_id)""",
    """
CREATE TABLE call_annotation_events (
	annotation_id VARCHAR(36) NOT NULL,
	actor_id VARCHAR(36) NOT NULL,
	action VARCHAR(24) NOT NULL,
	revision INTEGER NOT NULL,
	payload JSONB NOT NULL,
	payload_digest VARCHAR(64) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	id VARCHAR(36) NOT NULL,
	tenant_id VARCHAR(36) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(tenant_id, annotation_id) REFERENCES call_annotations (tenant_id, id) ON DELETE CASCADE,
	FOREIGN KEY(tenant_id, actor_id) REFERENCES users (tenant_id, id),
	CONSTRAINT uq_call_annotation_event_revision UNIQUE (tenant_id, annotation_id, revision),
	FOREIGN KEY(tenant_id) REFERENCES tenants (id)
)

""",
    """CREATE INDEX ix_call_annotation_events_tenant_id ON call_annotation_events (tenant_id)""",
]


def upgrade():
    for ddl in TABLE_DDL:
        op.execute(ddl)
    for table in ("call_annotations", "call_annotation_events"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_scope ON {table} USING (tenant_id=NULLIF(current_setting('app.tenant_id',true),'')) WITH CHECK (tenant_id=NULLIF(current_setting('app.tenant_id',true),''))"
        )
        rights = (
            "SELECT,INSERT" if table == "call_annotation_events" else "SELECT,INSERT,UPDATE,DELETE"
        )
        op.execute(
            f"DO $$ BEGIN IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='project28_app') THEN GRANT {rights} ON {table} TO project28_app; END IF; END $$"
        )
    op.execute("""CREATE FUNCTION preserve_call_annotation_source() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF ROW(OLD.id,OLD.tenant_id,OLD.call_id,OLD.original,OLD.original_digest,OLD.source_digest,OLD.source_attestation,OLD.group_keys,OLD.partition,OLD.created_at)
        IS DISTINCT FROM ROW(NEW.id,NEW.tenant_id,NEW.call_id,NEW.original,NEW.original_digest,NEW.source_digest,NEW.source_attestation,NEW.group_keys,NEW.partition,NEW.created_at) THEN
        RAISE EXCEPTION 'Registered source and original prediction are immutable';
      END IF;
      RETURN NEW;
    END $$""")
    op.execute(
        "CREATE TRIGGER immutable_call_annotation BEFORE UPDATE ON call_annotations FOR EACH ROW EXECUTE FUNCTION preserve_call_annotation_source()"
    )
    op.execute("""CREATE FUNCTION preserve_call_annotation_event() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN RAISE EXCEPTION 'Annotation audit events are append-only'; END $$""")
    op.execute(
        "CREATE TRIGGER immutable_call_annotation_event BEFORE UPDATE ON call_annotation_events FOR EACH ROW EXECUTE FUNCTION preserve_call_annotation_event()"
    )


def downgrade():
    op.get_bind().execute(sa.text("SET LOCAL row_security=off"))
    for table in ("call_annotations", "call_annotation_events"):
        if op.get_bind().execute(sa.text(f"SELECT EXISTS(SELECT 1 FROM {table})")).scalar():
            raise RuntimeError(
                "Refusing populated downgrade: call annotations; use reviewed restore"
            )
    op.drop_table("call_annotation_events")
    op.drop_table("call_annotations")
    op.execute("DROP FUNCTION preserve_call_annotation_event()")
    op.execute("DROP FUNCTION preserve_call_annotation_source()")
