"""Metadata-only tests with synthetic permissions; no audio or user data."""

import copy
import hashlib
import json
import subprocess
import sys
from datetime import date

import pytest
from pydantic import ValidationError

from src.datasets.manifest import Manifest
from src.datasets.split import load_lock_verified, plan_splits

AS_OF = date(2026, 10, 27)


def sample(i):
    return {
        "sample_id": f"sample{i}",
        "source_id": "synthetic",
        "source_version": "v1",
        "subset": "demo",
        "conversation_id": f"call{i}",
        "speaker_ids": [f"speaker{i}"],
        "audio_sha256": hashlib.sha256(f"synthetic{i}".encode()).hexdigest(),
        "duration_seconds": 12.0,
        "languages": ["ar-MA", "fr"],
        "label_status": "human_verified",
        "label_evidence_ref": "synthetic-label-evidence",
        "label_reviewer_ref": "synthetic-label-reviewer",
        "rights": {
            "status": "approved",
            "basis": "consent",
            "license_id": "synthetic-consent",
            "terms_url": "https://example.test/terms",
            "evidence_ref": "synthetic-evidence",
            "reviewer_ref": "synthetic-reviewer",
            "reviewed_on": "2026-01-01",
            "retention_until": "2027-01-01",
            "train": True,
            "evaluate": True,
        },
    }


def manifest(rows):
    return Manifest.model_validate_json(json.dumps({"schema_version": "1", "records": rows}))


def test_manifest_and_split_without_audio():
    rows = [sample(i) for i in range(8)]
    rows[1]["speaker_ids"] = ["speaker0"]
    rows[2]["conversation_id"] = rows[1]["conversation_id"]
    rows[3]["audio_sha256"] = rows[2]["audio_sha256"]
    result = plan_splits(manifest(rows), as_of=AS_OF, seed="seed1")
    assert len({result.assignments[f"sample{i}"] for i in range(4)}) == 1
    assert set(result.assignments.values()) == {"train", "validation", "test"}
    assert result == plan_splits(manifest(list(reversed(rows))), as_of=AS_OF, seed="seed1")


@pytest.mark.parametrize(
    "patch",
    [
        {"status": "pending"},
        {"status": "denied"},
        {"basis": "unknown"},
        {"train": False},
        {"evaluate": False},
        {"retention_until": "2026-05-01"},
        {"reviewed_on": "2027-01-01"},
    ],
)
def test_unapproved_expired_or_wrong_purpose_rejected(patch):
    rows = [sample(i) for i in range(4)]
    rows[0]["rights"].update(patch)
    with pytest.raises(ValueError, match="lacks current"):
        plan_splits(manifest(rows), as_of=AS_OF, seed="seed1")


@pytest.mark.parametrize("status", ["machine_only", "unreviewed"])
def test_pseudo_labels_never_promoted_to_gold(status):
    rows = [sample(i) for i in range(4)]
    rows[0]["label_status"] = status
    with pytest.raises(ValueError, match="gold"):
        plan_splits(manifest(rows), as_of=AS_OF, seed="seed1")


def test_lock_preserves_membership_and_frozen_test():
    rows = [sample(i) for i in range(8)]
    old = plan_splits(manifest(rows), as_of=AS_OF, seed="seed1")
    raw = old.model_dump_json().encode()
    loaded = load_lock_verified(raw, hashlib.sha256(raw).hexdigest())
    updated = plan_splits(manifest(rows + [sample(99)]), as_of=AS_OF, seed="seed1", prior=loaded)
    assert all(updated.assignments[k] == v for k, v in old.assignments.items())
    assert updated.assignments["sample99"] == "train"
    with pytest.raises(ValueError, match="hash mismatch"):
        load_lock_verified(raw, "0" * 64)


def test_rejects_new_links_into_test_or_across_locked_splits():
    rows = [sample(i) for i in range(8)]
    lock = plan_splits(manifest(rows), as_of=AS_OF, seed="seed1")
    test_id = next(k for k, v in lock.assignments.items() if v == "test")
    train_id = next(k for k, v in lock.assignments.items() if v == "train")
    test_row = next(x for x in rows if x["sample_id"] == test_id)
    train_row = next(x for x in rows if x["sample_id"] == train_id)
    bridge = sample(99)
    bridge["speaker_ids"] = [test_row["speaker_ids"][0]]
    with pytest.raises(ValueError, match="locked test"):
        plan_splits(manifest(rows + [bridge]), as_of=AS_OF, seed="seed1", prior=lock)
    bridge["speaker_ids"].append(train_row["speaker_ids"][0])
    with pytest.raises(ValueError, match="bridge"):
        plan_splits(manifest(rows + [bridge]), as_of=AS_OF, seed="seed1", prior=lock)


def test_locked_content_removal_or_edit_is_rejected():
    rows = [sample(i) for i in range(6)]
    lock = plan_splits(manifest(rows), as_of=AS_OF, seed="seed1")
    changed = copy.deepcopy(rows)
    changed[0]["duration_seconds"] = 13.0
    with pytest.raises(ValueError, match="locked record changed"):
        plan_splits(manifest(changed), as_of=AS_OF, seed="seed1", prior=lock)
    with pytest.raises(ValueError, match="missing"):
        plan_splits(manifest(rows[1:]), as_of=AS_OF, seed="seed1", prior=lock)


def test_rejects_duplicate_ids_unverified_identity_and_unknown_fields():
    with pytest.raises(ValidationError):
        manifest([sample(0), sample(0)])
    bad = sample(1)
    bad["speaker_ids"] = []
    with pytest.raises(ValidationError):
        manifest([bad])
    bad = sample(1)
    bad["raw_transcript"] = "not permitted in metadata"
    with pytest.raises(ValidationError):
        manifest([bad])


@pytest.mark.parametrize(
    "patch",
    [
        {"license_id": "unknown"},
        {"reviewer_ref": "unknown"},
        {"terms_url": "http://example.test/terms"},
        {"terms_url": "https://example.test/terms?token=private"},
        {"retention_until": "2025-01-01"},
    ],
)
def test_approved_rights_require_reviewable_safe_evidence(patch):
    row = sample(0)
    row["rights"].update(patch)
    with pytest.raises(ValidationError):
        manifest([row])


def test_independent_groups_use_approximate_eighty_ten_ten_split():
    result = plan_splits(manifest([sample(i) for i in range(100)]), as_of=AS_OF, seed="seed1")
    assert list(result.assignments.values()).count("train") == 80
    assert list(result.assignments.values()).count("validation") == 10
    assert list(result.assignments.values()).count("test") == 10


def test_gold_label_requires_review_provenance():
    row = sample(1)
    row["label_reviewer_ref"] = None
    with pytest.raises(ValidationError, match="human-verified labels"):
        manifest([row])


def test_cli_writes_exclusively_and_git_ignores_sensitive_artifacts(tmp_path):
    source = tmp_path / "manifest.json"
    source.write_text(json.dumps({"schema_version": "1", "records": [sample(i) for i in range(8)]}))
    output = tmp_path / "lock.json"
    cmd = [
        sys.executable,
        "-m",
        "src.datasets",
        str(source),
        "--as-of",
        "2026-10-27",
        "--seed",
        "seed1",
        "--output",
        str(output),
    ]
    assert subprocess.run(cmd, capture_output=True).returncode == 0
    original = output.read_bytes()
    assert subprocess.run(cmd, capture_output=True).returncode != 0
    assert output.read_bytes() == original
    for path in [
        "data/datasets/private/audio.mp3",
        "data/manifests/private.json",
        ".local/example.json",
    ]:
        assert subprocess.run(["git", "check-ignore", "--quiet", path]).returncode == 0


def test_cli_does_not_echo_rejected_sensitive_input(tmp_path):
    row = sample(0)
    row["raw_transcript"] = "SYNTHETIC_PRIVATE_SENTINEL"
    source = tmp_path / "invalid.json"
    source.write_text(json.dumps({"schema_version": "1", "records": [row]}))
    cmd = [
        sys.executable,
        "-m",
        "src.datasets",
        str(source),
        "--as-of",
        "2026-10-27",
        "--seed",
        "seed1",
        "--output",
        str(tmp_path / "lock.json"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode != 0
    assert "SYNTHETIC_PRIVATE_SENTINEL" not in result.stdout + result.stderr
