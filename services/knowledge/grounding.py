"""Conservative extractive citation checking for trusted retrieval callers.

This is not an entailment verifier or a replacement for authenticated retrieval.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from services.knowledge.ingestion import Chunk, permitted
from services.knowledge.store import KnowledgeStore
from src.security.injection_detector import detect_injection


class PolicyEvidence(BaseModel):
    source_id: str
    passage: str
    effective_date: datetime | None = None


class PolicyAnswer(BaseModel):
    status: Literal["supported", "abstain"]
    answer: str | None = None
    sources: list[PolicyEvidence] = Field(default_factory=list)
    reason: str | None = None


def validate_extractive_answer(
    passage: str,
    citation_id: str,
    chunks: list[Chunk],
    *,
    tenant_id: UUID,
    department: str,
    role: str,
    now: datetime,
) -> PolicyAnswer:
    """Return an exact cited excerpt only; abstain on ambiguity or missing access.

    Callers must supply a trusted identity and freshly retrieved chunks. Multiple
    passages are not reconciled and require human review.
    """
    if now.tzinfo is None or not passage.strip():
        return PolicyAnswer(status="abstain", reason="Missing passage or timezone")
    allowed = [c for c in chunks if permitted(c, tenant_id, department, role, now)]
    if len(allowed) != 1:
        return PolicyAnswer(status="abstain", reason="Missing or ambiguous policy evidence")
    chunk = allowed[0]
    effective = chunk.document.effective_at
    if effective is None or effective > now:
        return PolicyAnswer(status="abstain", reason="Policy effective date missing or future")
    if detect_injection(chunk.text).injection_detected:
        return PolicyAnswer(status="abstain", reason="Suspicious policy requires review")
    if chunk.citation_id != citation_id or passage not in chunk.text:
        return PolicyAnswer(status="abstain", reason="Citation or passage is unsupported")
    return PolicyAnswer(
        status="supported",
        answer=passage,
        sources=[
            PolicyEvidence(source_id=chunk.citation_id, passage=passage, effective_date=effective)
        ],
    )


class GroundedPolicyService:
    """Trusted server-side scope; retrieval callback must fetch current SQL-filtered chunks.

    Extractive output is evidence, never executable instructions. No LLM or tool
    dispatch is reachable from document contents. Multiple hits require review.
    """

    def __init__(
        self, retrieve: Callable[[str], list[Chunk]], *, tenant_id: UUID, department: str, role: str
    ) -> None:
        self.retrieve = retrieve
        self.tenant_id = tenant_id
        self.department = department
        self.role = role

    def answer(self, query: str) -> PolicyAnswer:
        if not query.strip() or len(query) > 8000:
            return PolicyAnswer(status="abstain", reason="Query outside bounds")
        try:
            chunks = self.retrieve(query)
        except Exception:
            return PolicyAnswer(status="abstain", reason="Retrieval unavailable")
        if len(chunks) != 1:
            return PolicyAnswer(status="abstain", reason="Missing or conflicting policy evidence")
        chunk = chunks[0]
        return validate_extractive_answer(
            chunk.text,
            chunk.citation_id,
            chunks,
            now=datetime.now(UTC),
            tenant_id=self.tenant_id,
            department=self.department,
            role=self.role,
        )

    @classmethod
    def from_store(
        cls,
        store: KnowledgeStore,
        embed: Callable[[list[str]], list[list[float]]],
        *,
        revision: str,
        tenant_id: UUID,
        department: str,
        role: str,
    ) -> "GroundedPolicyService":
        """Bind trusted identity outside graph input; fetch fresh ACL-filtered evidence."""

        def retrieve(query: str) -> list[Chunk]:
            return store.search(
                embed([query])[0],
                tenant_id=tenant_id,
                department=department,
                role=role,
                revision=revision,
                limit=2,
            )

        return cls(retrieve, tenant_id=tenant_id, department=department, role=role)
