"""Isolated human emotion annotations and protected split keys."""

import sqlalchemy as sa
from alembic import op

revision = "0004_emotion"
down_revision = "0003_jobs"
branch_labels = None
depends_on = None


TABLE_DDL = [
    """CREATE TABLE emotion_items (
        call_id VARCHAR(36) NOT NULL,
        segment_index INTEGER NOT NULL,
        prediction JSONB NOT NULL,
        partition VARCHAR(12) NOT NULL,
        source_digest VARCHAR(64) NOT NULL,
        group_keys JSONB NOT NULL,
        consent_to_train BOOLEAN NOT NULL,
        consent_evidence VARCHAR(300) NOT NULL,
        revision INTEGER NOT NULL,
        adjudicated_label VARCHAR(20),
        adjudicator_id VARCHAR(36),
        adjudication_note TEXT,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        id VARCHAR(36) NOT NULL,
        tenant_id VARCHAR(36) NOT NULL,
        PRIMARY KEY (id),
        CONSTRAINT uq_emotion_item_tenant UNIQUE (tenant_id, id),
        CONSTRAINT uq_emotion_segment UNIQUE (tenant_id, call_id, segment_index),
        FOREIGN KEY(tenant_id, call_id) REFERENCES calls (tenant_id, id) ON DELETE CASCADE,
        CONSTRAINT ck_emotion_partition CHECK (partition IN ('train','evaluation')),
        CONSTRAINT ck_emotion_consent CHECK (partition='train' OR NOT consent_to_train),
        CONSTRAINT ck_emotion_bounds CHECK (revision>0 AND segment_index>=0),
        FOREIGN KEY(tenant_id) REFERENCES tenants (id)
)""",
    """CREATE INDEX ix_emotion_items_tenant_id ON emotion_items (tenant_id)""",
    """CREATE TABLE emotion_partition_keys (
        tenant_id VARCHAR(36) NOT NULL,
        key_digest VARCHAR(64) NOT NULL,
        partition VARCHAR(12) NOT NULL,
        PRIMARY KEY (tenant_id, key_digest),
        FOREIGN KEY(tenant_id) REFERENCES tenants (id)
)""",
    """CREATE TABLE emotion_votes (
        item_id VARCHAR(36) NOT NULL,
        reviewer_id VARCHAR(36) NOT NULL,
        label VARCHAR(20) NOT NULL,
        notes TEXT NOT NULL,
        confirmed BOOLEAN NOT NULL,
        version INTEGER NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        id VARCHAR(36) NOT NULL,
        tenant_id VARCHAR(36) NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY(tenant_id, item_id) REFERENCES emotion_items (tenant_id, id) ON DELETE
CASCADE,
        FOREIGN KEY(tenant_id, reviewer_id) REFERENCES users (tenant_id, id),
        CONSTRAINT uq_emotion_reviewer UNIQUE (tenant_id, item_id, reviewer_id),
        CONSTRAINT ck_emotion_vote_label CHECK (label IN
('neutral','happy','angry','sad','Unknown')),
        FOREIGN KEY(tenant_id) REFERENCES tenants (id)
)""",
    """CREATE INDEX ix_emotion_votes_tenant_id ON emotion_votes (tenant_id)""",
]


def upgrade():
    for ddl in TABLE_DDL:
        op.execute(ddl)
    for table in ("emotion_items", "emotion_partition_keys", "emotion_votes"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_scope ON {table} "
            "USING (tenant_id=NULLIF(current_setting('app.tenant_id',true),'')) "
            "WITH CHECK (tenant_id=NULLIF(current_setting('app.tenant_id',true),''))"
        )
        privileges = (
            "SELECT,INSERT" if table == "emotion_partition_keys" else "SELECT,INSERT,UPDATE,DELETE"
        )
        op.execute(
            f"DO $$ BEGIN IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='project28_app') "
            f"THEN GRANT {privileges} ON {table} TO project28_app; END IF; END $$"
        )
    op.execute("""CREATE FUNCTION preserve_emotion_prediction() RETURNS trigger
    LANGUAGE plpgsql AS $$
    BEGIN
      IF ROW(OLD.tenant_id,OLD.id,OLD.call_id,OLD.segment_index,OLD.prediction,OLD.partition,
             OLD.source_digest,OLD.group_keys)
         IS DISTINCT FROM
         ROW(NEW.tenant_id,NEW.id,NEW.call_id,NEW.segment_index,NEW.prediction,NEW.partition,
             NEW.source_digest,NEW.group_keys) THEN
        RAISE EXCEPTION 'Original emotion inference and split are immutable';
      END IF;
      RETURN NEW;
    END $$""")
    op.execute(
        "CREATE TRIGGER immutable_emotion BEFORE UPDATE ON emotion_items "
        "FOR EACH ROW EXECUTE FUNCTION preserve_emotion_prediction()"
    )


def downgrade():
    op.get_bind().execute(sa.text("SET LOCAL row_security=off"))
    for name in ("emotion_items", "emotion_partition_keys", "emotion_votes"):
        if op.get_bind().execute(sa.text(f"SELECT EXISTS(SELECT 1 FROM {name})")).scalar():
            raise RuntimeError("Refusing populated downgrade of emotion data; use reviewed restore")
    op.drop_table("emotion_votes")
    op.drop_table("emotion_partition_keys")
    op.drop_table("emotion_items")
    op.execute("DROP FUNCTION preserve_emotion_prediction()")
