import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import psycopg

from services.knowledge.embeddings import BgeM3
from services.knowledge.ingestion import Document, extract_chunks
from services.knowledge.store import KnowledgeStore

revision = "5617a9f61b028005a4858fdac845db406aefb181"
model = BgeM3(Path(".local/step17-bge-m3").resolve(), revision)
texts = [
    "Refund requests require supervisor approval.",
    "Password resets require identity verification.",
    "Confidential audit procedure for supervisors.",
]
queries = ["Who must approve a refund?", "What is required to reset a password?"]
t = time.perf_counter()
vectors = model.encode(texts)
query_vectors = model.encode(queries)
encode_seconds = time.perf_counter() - t
tenant = uuid4()
docs = []
with psycopg.connect(
    Path(".local/step17-database-url").read_text().strip(), autocommit=True, connect_timeout=10
) as connection:
    store = KnowledgeStore(connection)
    store.initialize()
    t = time.perf_counter()
    for i, text in enumerate(texts):
        doc = Document(
            id=uuid4(),
            tenant_id=tenant,
            department="support",
            roles={"supervisor"} if i == 2 else {"agent"},
            version=1,
            source="synthetic local smoke fixture",
            approved=True,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        docs.append(doc)
        store.replace(doc, extract_chunks(doc, text.encode(), "policy.txt"), [vectors[i]], revision)
    index_seconds = time.perf_counter() - t
    hits = 0
    for i, vector in enumerate(query_vectors):
        rows = store.search(
            vector, tenant_id=tenant, department="support", role="agent", revision=revision, limit=1
        )
        hits += bool(rows and rows[0].document.id == docs[i].id)
    assert not store.search(
        query_vectors[0], tenant_id=uuid4(), department="support", role="agent", revision=revision
    )
    assert all(
        c.document.id != docs[2].id
        for c in store.search(
            vectors[2], tenant_id=tenant, department="support", role="agent", revision=revision
        )
    )
    store.delete(tenant, docs[0].id)
    assert all(
        c.document.id != docs[0].id
        for c in store.search(
            query_vectors[0],
            tenant_id=tenant,
            department="support",
            role="agent",
            revision=revision,
        )
    )
    storage = connection.execute(
        "SELECT pg_total_relation_size('knowledge_documents')"
        "+pg_total_relation_size('knowledge_chunks')"
    ).fetchone()[0]
    result = {
        "fixture": "3 synthetic procedures; 2 queries; not company production data",
        "model": "BAAI/bge-m3",
        "revision": revision,
        "dimension": len(vectors[0]),
        "recall_at_1": hits / 2,
        "queries": 2,
        "encoding_seconds": encode_seconds,
        "index_seconds": index_seconds,
        "total_table_bytes_including_existing_test_rows": storage,
        "acl_and_deletion_assertions": True,
        "device": "cpu",
    }
folder = Path("docs/implementation/evidence") / (
    "step17-repeat-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
)
folder.mkdir(parents=True, exist_ok=True)
with (folder / "neural-pgvector.json").open("x", encoding="utf8") as f:
    json.dump(result, f, indent=2)
print(result)
