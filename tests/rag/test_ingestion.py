from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from services.knowledge.embeddings import BgeM3
from services.knowledge.ingestion import Document, extract_chunks, permitted
from services.knowledge.store import vector_literal


def document(**kwargs):
    return Document(
        id=uuid4(),
        tenant_id=uuid4(),
        department="support",
        roles={"agent"},
        version=1,
        source="synthetic procedure",
        expires_at=datetime.now(UTC) + timedelta(days=1),
        approved=True,
        **kwargs,
    )


def test_chunk_provenance_and_acl():
    doc = document()
    chunks = extract_chunks(doc, b"# Refunds\nUse the approved refund procedure.", "policy.md")
    assert chunks[0].section == "Refunds"
    assert str(doc.id) in chunks[0].citation_id
    now = datetime.now(UTC)
    assert permitted(chunks[0], doc.tenant_id, "support", "agent", now)
    assert not permitted(chunks[0], uuid4(), "support", "agent", now)
    assert not permitted(chunks[0], doc.tenant_id, "finance", "agent", now)
    assert not permitted(chunks[0], doc.tenant_id, "support", "admin", now)
    assert not permitted(chunks[0], doc.tenant_id, "support", "agent", now + timedelta(days=2))


def test_unapproved_binary_and_unsupported_inputs_rejected():
    doc = document()
    with pytest.raises(ValueError):
        extract_chunks(doc.model_copy(update={"approved": False}), b"policy", "p.txt")
    with pytest.raises(ValueError):
        extract_chunks(doc, b"\x00payload", "p.txt")
    with pytest.raises(ValueError):
        extract_chunks(doc, b"policy", "p.pdf")


def test_version_changes_citation():
    doc = document()
    first = extract_chunks(doc, b"Policy text.", "p.txt")[0]
    second = extract_chunks(doc.model_copy(update={"version": 2}), b"Policy text.", "p.txt")[0]
    assert first.citation_id != second.citation_id


@pytest.mark.parametrize("vector", [[0.0] * 1024, [float("nan")] * 1024, [1.0] * 3, [1e308] * 1024])
def test_invalid_embeddings_rejected(vector):
    with pytest.raises(ValueError):
        vector_literal(vector)


def test_model_refuses_modified_weights_without_loading_runtime(tmp_path):
    (tmp_path / "pytorch_model.bin").write_bytes(b"modified")
    with pytest.raises(ValueError, match="weights differ"):
        BgeM3(tmp_path, "5617a9f61b028005a4858fdac845db406aefb181")
