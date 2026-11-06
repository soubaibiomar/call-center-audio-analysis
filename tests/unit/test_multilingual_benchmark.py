"""Independent scoring and input-boundary checks for multilingual evaluation."""

import copy
import hashlib

import pytest

from scripts.benchmark_upgrade_asr import normalize_comparison, validate_multilingual_manifest
from scripts.intake_multilingual_benchmark import SOURCES


def fixture_manifest():
    text = "Une phrase de référence."
    return {
        "schema_version": "multilingual-asr-v1",
        "purpose": "local non-commercial evaluation only; no training; no redistribution",
        "retention_until": "2100-01-01",
        "sources": copy.deepcopy(SOURCES),
        "records": [
            {
                "sample_id": "fr-1",
                "language": "fr",
                "filename": "clip.wav",
                "reference": text,
                "reference_sha256": hashlib.sha256(text.encode()).hexdigest(),
            }
        ],
    }


def test_french_accents_preserved_with_consistent_word_boundaries():
    assert normalize_comparison("ÉTÉ, c’est l'école!") == "été c est l école"
    assert normalize_comparison("été") != normalize_comparison("ete")


def test_arabic_marks_removed_without_collapsing_distinct_letters():
    assert normalize_comparison("سَلامــ، عَليكم!") == "سلام عليكم"
    assert normalize_comparison("إلى") != normalize_comparison("الى")
    assert normalize_comparison("123") == "123"


@pytest.mark.parametrize("filename", ["../outside.wav", "../../clip.wav"])
def test_audio_cannot_escape_corpus_root(tmp_path, filename):
    manifest = fixture_manifest()
    manifest["records"][0]["filename"] = filename
    with pytest.raises(ValueError, match="escapes"):
        validate_multilingual_manifest(manifest, tmp_path)


def test_reference_changes_and_duplicate_ids_are_rejected(tmp_path):
    manifest = fixture_manifest()
    validate_multilingual_manifest(manifest, tmp_path)
    manifest["records"][0]["reference"] = "Different reference"
    with pytest.raises(ValueError, match="Reference changed"):
        validate_multilingual_manifest(manifest, tmp_path)
    manifest = fixture_manifest()
    manifest["records"] *= 2
    with pytest.raises(ValueError, match="Duplicate"):
        validate_multilingual_manifest(manifest, tmp_path)


def test_expired_or_training_purpose_is_rejected(tmp_path):
    manifest = fixture_manifest()
    manifest["retention_until"] = "2000-01-01"
    with pytest.raises(ValueError, match="expired"):
        validate_multilingual_manifest(manifest, tmp_path)
    manifest = fixture_manifest()
    manifest["purpose"] = "training"
    with pytest.raises(ValueError, match="purpose"):
        validate_multilingual_manifest(manifest, tmp_path)
