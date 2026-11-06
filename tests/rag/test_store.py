import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest

from services.knowledge.ingestion import Document, extract_chunks
from services.knowledge.store import KnowledgeStore


def test_pgvector_acl_update_delete_and_model_version():
    path = os.getenv("PROJECT28_KNOWLEDGE_TEST_URL_FILE")
    if not path:
        pytest.skip("Configure isolated knowledge pgvector test URL")
    with psycopg.connect(
        Path(path).read_text().strip(), autocommit=True, connect_timeout=10
    ) as connection:
        assert connection.info.dbname == "knowledge_test"
        store = KnowledgeStore(connection)
        store.initialize()
        doc = Document(
            id=uuid4(),
            tenant_id=uuid4(),
            department="support",
            roles={"agent"},
            version=1,
            source="synthetic policy",
            approved=True,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        vector = [1.0] + [0.0] * 1023
        chunks = extract_chunks(doc, b"Refund approval policy.", "p.txt")
        store.replace(doc, chunks, [vector], "synthetic-v1")
        query = dict(
            tenant_id=doc.tenant_id, department="support", role="agent", revision="synthetic-v1"
        )
        assert store.search(vector, **query)[0].citation_id == chunks[0].citation_id
        assert not store.search(vector, **{**query, "role": "admin"})
        assert not store.search(vector, **{**query, "tenant_id": uuid4()})
        assert not store.search(vector, **{**query, "department": "finance"})
        assert not store.search(vector, **{**query, "revision": "other"})
        revised = doc.model_copy(update={"version": 2})
        new = extract_chunks(revised, b"Updated policy.", "p.txt")
        store.replace(revised, new, [vector], "synthetic-v1")
        assert store.search(vector, **query)[0].citation_id == new[0].citation_id
        with pytest.raises(ValueError):
            store.replace(doc, chunks, [vector], "synthetic-v1")
        store.delete(doc.tenant_id, doc.id)
        assert not store.search(vector, **query)
