import hashlib
import json
from datetime import date, timedelta

import pytest

from scripts.benchmark_emotion import validate_manifest


def manifest(tmp_path):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"synthetic")
    record = dict(
        id="fixture",
        path=audio.name,
        sha256=hashlib.sha256(audio.read_bytes()).hexdigest(),
        license="synthetic fixture",
        label_provenance="fixture",
    )
    data = dict(
        purpose="local evaluation only; no training",
        retention_review_date=(date.today() + timedelta(days=1)).isoformat(),
        permission_basis="synthetic",
        records=[record],
    )
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data))
    return path, data


def test_intake_manifest_integrity_and_evaluation_purpose(tmp_path):
    path, data = manifest(tmp_path)
    assert len(validate_manifest(path)["records"]) == 1
    (tmp_path / "audio.wav").write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum"):
        validate_manifest(path)
    data["purpose"] = "training"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="purpose"):
        validate_manifest(path)


def test_retention_and_path_escape_rejected(tmp_path):
    path, data = manifest(tmp_path)
    data["retention_review_date"] = "2000-01-01"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Retention"):
        validate_manifest(path)
    path, data = manifest(tmp_path)
    outside = tmp_path.parent / "emotion-outside-fixture"
    outside.write_bytes(b"fixture")
    data["records"][0]["path"] = "../emotion-outside-fixture"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Unsafe"):
        validate_manifest(path)
