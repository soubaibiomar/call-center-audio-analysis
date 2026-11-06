"""Bounded text ingestion with explicit document provenance and access rules."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import PurePath
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class Document(BaseModel):
    id: UUID
    tenant_id: UUID
    department: str = Field(min_length=1, max_length=100)
    roles: frozenset[Literal["agent", "supervisor", "admin"]] = Field(min_length=1)
    version: int = Field(ge=1)
    source: str = Field(min_length=1, max_length=500)
    expires_at: datetime
    approved: bool = False
    effective_at: datetime | None = None

    @model_validator(mode="after")
    def aware_expiry(self) -> Document:
        if self.expires_at.tzinfo is None:
            raise ValueError("Retention timestamp must be timezone-aware")
        if self.effective_at is not None and self.effective_at.tzinfo is None:
            raise ValueError("Effective timestamp must be timezone-aware")
        return self


class Chunk(BaseModel):
    document: Document
    ordinal: int = Field(ge=0)
    section: str
    page: int | None = None
    text: str
    content_sha256: str
    citation_id: str


def extract_chunks(
    document: Document, data: bytes, filename: str, *, limit: int = 1000
) -> list[Chunk]:
    """Only approved UTF-8 plain text/Markdown; no active document parsers."""
    if not document.approved or document.expires_at <= datetime.now(UTC):
        raise ValueError("Document is unapproved or expired")
    if PurePath(filename).suffix.lower() not in {".txt", ".md"}:
        raise ValueError("Only UTF-8 TXT and Markdown are approved")
    if not 0 < len(data) <= 2 * 1024 * 1024 or not 100 <= limit <= 4000:
        raise ValueError("Document or chunk size exceeds bounds")
    text = data.decode("utf-8", errors="strict")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in text):
        raise ValueError("Binary/control payload rejected")
    chunks: list[Chunk] = []
    section = "document"
    buffer = ""

    def emit(value: str) -> None:
        normalized = value.strip()
        if not normalized:
            return
        digest = hashlib.sha256(normalized.encode()).hexdigest()
        ordinal = len(chunks)
        chunks.append(
            Chunk(
                document=document,
                ordinal=ordinal,
                section=section,
                text=normalized,
                content_sha256=digest,
                citation_id=f"{document.id}:v{document.version}:{ordinal}:{digest[:16]}",
            )
        )

    for line in text.splitlines():
        if line.startswith("#"):
            emit(buffer)
            buffer = ""
            section = line.lstrip("#").strip()[:200] or "untitled"
        while len(line) > limit:
            emit(buffer)
            buffer = ""
            emit(line[:limit])
            line = line[limit:]
        if len(buffer) + len(line) + 1 > limit:
            emit(buffer)
            buffer = ""
        buffer += line + "\n"
    emit(buffer)
    if not chunks:
        raise ValueError("Document has no indexable text")
    return chunks


def permitted(chunk: Chunk, tenant_id: UUID, department: str, role: str, now: datetime) -> bool:
    """Exact tenant, department and role grants; no implicit administrator bypass."""
    doc = chunk.document
    return (
        doc.approved
        and doc.tenant_id == tenant_id
        and doc.department == department
        and role in doc.roles
        and doc.expires_at > now
    )
