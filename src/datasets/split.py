"""Deterministic connected-component splitting with an externally pinned lock."""

import hashlib
import json
from collections import defaultdict
from datetime import date
from typing import Literal

from pydantic import Field

from src.datasets.manifest import Manifest, StrictModel, Token

Split = Literal["train", "validation", "test"]


class Lock(StrictModel):
    schema_version: Literal["1"] = "1"
    algorithm: Literal["sha256-components-v1"] = "sha256-components-v1"
    seed: Token
    assignments: dict[Token, Split] = Field(min_length=1)
    fingerprints: dict[Token, str] = Field(min_length=1)


def _fingerprint(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def plan_splits(manifest: Manifest, *, as_of: date, seed: str, prior: Lock | None = None) -> Lock:
    """Reject disallowed records; preserve old assignments and reject group bridges."""
    if prior and prior.seed != seed:
        raise ValueError("prior seed mismatch")
    records = {r.sample_id: r for r in manifest.records}
    if prior and (
        set(prior.assignments) != set(prior.fingerprints)
        or not set(prior.assignments).issubset(records)
    ):
        raise ValueError("prior lock records are missing or inconsistent")
    for r in manifest.records:
        rights = r.rights
        if (
            rights.status != "approved"
            or rights.basis == "unknown"
            or not rights.train
            or not rights.evaluate
            or rights.reviewed_on > as_of
            or rights.retention_until < as_of
            or r.label_status != "human_verified"
        ):
            raise ValueError(
                f"sample {r.sample_id} lacks current reviewed permissions or gold labels"
            )
        if prior and r.sample_id in prior.assignments:
            if _fingerprint(r.model_dump(mode="json")) != prior.fingerprints[r.sample_id]:
                raise ValueError(f"locked record changed: {r.sample_id}")

    parent = {key: key for key in records}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: str, right: str) -> None:
        left, right = find(left), find(right)
        if left != right:
            parent[max(left, right)] = min(left, right)

    seen: dict[tuple[str, str], str] = {}
    for r in manifest.records:
        keys = [("conversation", r.conversation_id), ("audio", r.audio_sha256)]
        keys.extend(("speaker", speaker) for speaker in r.speaker_ids)
        for key in keys:
            if key in seen:
                union(r.sample_id, seen[key])
            else:
                seen[key] = r.sample_id
    groups: dict[str, list[str]] = defaultdict(list)
    for sample_id in records:
        groups[find(sample_id)].append(sample_id)
    if len(groups) < 3:
        raise ValueError("at least three independent components are required")
    ordered = sorted(
        (sorted(g) for g in groups.values()), key=lambda g: (_fingerprint([seed, g]), g)
    )
    holdout_count = max(1, len(ordered) // 10)
    assignments: dict[str, Split] = {}
    for index, group in enumerate(ordered):
        pinned = {prior.assignments[x] for x in group if prior and x in prior.assignments}
        if len(pinned) > 1:
            raise ValueError("new links bridge previously locked partitions")
        if pinned and "test" in pinned and prior and any(x not in prior.assignments for x in group):
            raise ValueError("new records cannot enter a locked test component")
        choice: Split = (
            next(iter(pinned))
            if pinned
            else (
                "train"
                if prior
                else "test"
                if index < holdout_count
                else "validation"
                if index < 2 * holdout_count
                else "train"
            )
        )
        assignments.update({item: choice for item in group})
    if set(assignments.values()) != {"train", "validation", "test"}:
        raise ValueError("split must contain train, validation, and test")
    return Lock(
        seed=seed,
        assignments=assignments,
        fingerprints={
            r.sample_id: _fingerprint(r.model_dump(mode="json")) for r in manifest.records
        },
    )


def load_lock_verified(raw: bytes, expected_sha256: str) -> Lock:
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("prior lock hash mismatch")
    return Lock.model_validate_json(raw)
