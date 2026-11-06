"""Explicit PostgreSQL pgvector persistence with ACL filtering before ranking."""

import json
import math
from datetime import UTC, datetime
from uuid import UUID

import psycopg

from services.knowledge.ingestion import Chunk, Document


def vector_literal(vector: list[float]) -> str:
    norm_squared = sum(v * v for v in vector)
    if (
        len(vector) != 1024
        or any(not math.isfinite(v) for v in vector)
        or not math.isfinite(norm_squared)
        or norm_squared <= 1e-12
    ):
        raise ValueError("Expected a finite 1024-dimensional embedding")
    return "[" + ",".join(str(float(v)) for v in vector) + "]"


class KnowledgeStore:
    def __init__(self, connection: psycopg.Connection) -> None:
        self.connection = connection

    def initialize(self) -> None:
        """Explicit administrative setup; never runs on application import."""
        with self.connection.transaction():
            self.connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
            self.connection.execute("""CREATE TABLE IF NOT EXISTS knowledge_documents (
                tenant_id uuid NOT NULL, id uuid NOT NULL, version integer NOT NULL,
                metadata jsonb NOT NULL, model_revision text NOT NULL,
                PRIMARY KEY (tenant_id,id))""")
            self.connection.execute("""CREATE TABLE IF NOT EXISTS knowledge_chunks (
                tenant_id uuid NOT NULL, document_id uuid NOT NULL, ordinal integer NOT NULL,
                chunk jsonb NOT NULL, embedding vector(1024) NOT NULL,
                PRIMARY KEY (tenant_id,document_id,ordinal),
                FOREIGN KEY (tenant_id,document_id) REFERENCES knowledge_documents(tenant_id,id)
                ON DELETE CASCADE)""")

    def replace(
        self, document: Document, chunks: list[Chunk], vectors: list[list[float]], revision: str
    ) -> None:
        if not document.approved or document.expires_at <= datetime.now(UTC):
            raise ValueError("Document cannot be indexed")
        if not chunks or len(chunks) != len(vectors) or any(c.document != document for c in chunks):
            raise ValueError("Chunks do not match the approved document")
        encoded = [vector_literal(v) for v in vectors]
        with self.connection.transaction():
            # Serialize concurrent versions of the same tenant/document.
            self.connection.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                (str(document.tenant_id) + str(document.id),),
            )
            previous = self.connection.execute(
                "SELECT version FROM knowledge_documents WHERE tenant_id=%s AND id=%s",
                (document.tenant_id, document.id),
            ).fetchone()
            if previous and document.version <= previous[0]:
                raise ValueError("Document version must increase")
            self.delete(document.tenant_id, document.id)
            self.connection.execute(
                "INSERT INTO knowledge_documents VALUES (%s,%s,%s,%s::jsonb,%s)",
                (
                    document.tenant_id,
                    document.id,
                    document.version,
                    document.model_dump_json(),
                    revision,
                ),
            )
            for chunk, vector in zip(chunks, encoded):
                self.connection.execute(
                    "INSERT INTO knowledge_chunks VALUES (%s,%s,%s,%s::jsonb,%s::vector)",
                    (
                        document.tenant_id,
                        document.id,
                        chunk.ordinal,
                        chunk.model_dump_json(),
                        vector,
                    ),
                )

    def delete(self, tenant_id: UUID, document_id: UUID) -> None:
        self.connection.execute(
            "DELETE FROM knowledge_documents WHERE tenant_id=%s AND id=%s", (tenant_id, document_id)
        )

    def search(
        self,
        vector: list[float],
        *,
        tenant_id: UUID,
        department: str,
        role: str,
        revision: str,
        limit: int = 5,
    ) -> list[Chunk]:
        if not 1 <= limit <= 20 or role not in {"agent", "supervisor", "admin"}:
            raise ValueError("Invalid retrieval bounds")
        rows = self.connection.execute(
            """SELECT c.chunk FROM knowledge_chunks c
            JOIN knowledge_documents d ON (c.tenant_id=d.tenant_id AND c.document_id=d.id)
            WHERE d.tenant_id=%s AND d.metadata->>'department'=%s
            AND d.metadata->'roles' ? %s AND (d.metadata->>'approved')::boolean
            AND (d.metadata->>'expires_at')::timestamptz > now()
            AND d.model_revision=%s ORDER BY c.embedding <=> %s::vector LIMIT %s""",
            (tenant_id, department, role, revision, vector_literal(vector), limit),
        ).fetchall()
        return [
            Chunk.model_validate(row[0] if isinstance(row[0], dict) else json.loads(row[0]))
            for row in rows
        ]
