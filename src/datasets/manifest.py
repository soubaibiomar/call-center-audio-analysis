"""Validated, metadata-only records. Approval is an attestation, not legal advice."""

from datetime import date
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Token = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")]
Language = Annotated[str, StringConstraints(pattern=r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")]
Digest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Rights(StrictModel):
    status: Literal["approved", "pending", "denied"]
    basis: Literal["license", "consent", "unknown"]
    license_id: str = Field(min_length=1, max_length=160)
    terms_url: str = Field(min_length=1, max_length=500)
    evidence_ref: Token
    reviewer_ref: Token
    reviewed_on: date
    retention_until: date
    train: bool = False
    evaluate: bool = False

    @model_validator(mode="after")
    def evidence_is_identifiable(self) -> "Rights":
        url = urlsplit(self.terms_url)
        if url.scheme != "https" or not url.hostname or url.username or url.password:
            raise ValueError("terms_url must be a credential-free HTTPS URL")
        if url.query or url.fragment:
            raise ValueError("terms_url must not contain a query or fragment")
        if self.status == "approved" and any(
            value.strip().lower() in {"", "unknown", "none", "pending", "unverified"}
            for value in (self.license_id, self.evidence_ref, self.reviewer_ref)
        ):
            raise ValueError("approved rights require identifiable evidence and reviewer")
        if self.retention_until < self.reviewed_on:
            raise ValueError("retention cannot end before review")
        return self


class Sample(StrictModel):
    sample_id: Token
    source_id: Token
    source_version: Token
    subset: Token
    conversation_id: Token
    speaker_ids: list[Token] = Field(min_length=1)
    audio_sha256: Digest
    duration_seconds: float = Field(gt=0, allow_inf_nan=False)
    languages: list[Language] = Field(min_length=1)
    label_status: Literal["human_verified", "machine_only", "unreviewed"]
    label_evidence_ref: Token | None = None
    label_reviewer_ref: Token | None = None
    rights: Rights

    @model_validator(mode="after")
    def distinct_fields(self) -> "Sample":
        if len(set(self.speaker_ids)) != len(self.speaker_ids):
            raise ValueError("duplicate speaker IDs")
        if len(set(self.languages)) != len(self.languages):
            raise ValueError("duplicate language labels")
        if self.label_status == "human_verified" and (
            not self.label_evidence_ref
            or not self.label_reviewer_ref
            or self.label_evidence_ref.lower() in {"unknown", "none", "pending", "unverified"}
            or self.label_reviewer_ref.lower() in {"unknown", "none", "pending", "unverified"}
        ):
            raise ValueError("human-verified labels require evidence and reviewer references")
        return self


class Manifest(StrictModel):
    schema_version: Literal["1"]
    records: list[Sample] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_sample_ids(self) -> "Manifest":
        if len({r.sample_id for r in self.records}) != len(self.records):
            raise ValueError("duplicate sample IDs")
        return self
