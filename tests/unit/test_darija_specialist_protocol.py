"""Independent checks for disjoint selection, bounded downloads and paired metrics."""

import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from scripts.download_upgrade_models import fetch_range_bytes
from scripts.intake_darija_specialist_benchmark import eligible
from scripts.intake_multilingual_benchmark import sha
from scripts.summarize_darija_specialist_benchmarks import paired_interval


def test_selection_excludes_previous_clip_group_and_reference():
    item = {"row": {"duration": 4, "transcription": "three source words", "seg_id": "new_1"}}
    assert eligible(item, set(), set(), set())
    assert not eligible(item, {"new_1"}, set(), set())
    assert not eligible(item, set(), {"new"}, set())
    assert not eligible(item, set(), set(), {sha(b"three source words")})


def test_ignored_range_is_rejected_before_reading_body():
    class Unreadable(httpx.SyncByteStream):
        def __iter__(self):
            raise AssertionError("Must not read an ignored range response")

    transport = httpx.MockTransport(lambda request: httpx.Response(200, stream=Unreadable()))
    with httpx.Client(transport=transport) as client:
        with pytest.raises(ValueError, match="Invalid byte range"):
            fetch_range_bytes(client, "https://model.test/weights", 0, 2, 3)


def test_exact_range_is_accepted():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            206, headers={"content-range": "bytes 0-2/3"}, content=b"abc"
        )
    )
    with httpx.Client(transport=transport) as client:
        assert fetch_range_bytes(client, "https://model.test/weights", 0, 2, 3) == b"abc"


def test_private_prediction_output_cannot_target_public_directory(tmp_path):
    output = tmp_path / "predictions.jsonl"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/benchmark_upgrade_asr.py",
            "--backend",
            "whisper",
            "--model",
            "unused",
            "--device",
            "cpu",
            "--output",
            str(tmp_path / "result.json"),
            "--manifest",
            str(tmp_path / "unused.json"),
            "--private-predictions",
            str(output),
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Private predictions require" in result.stderr
    assert not output.exists()


@pytest.mark.parametrize("content,error", [(b"abcd", "Oversized"), (b"ab", "Incomplete")])
def test_wrong_range_body_size_is_rejected(content, error):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            206, headers={"content-range": "bytes 0-2/3"}, content=content
        )
    )
    with httpx.Client(transport=transport) as client:
        with pytest.raises(ValueError, match=error):
            fetch_range_bytes(client, "https://model.test/weights", 0, 2, 3)


def test_pairing_uses_identical_reference_denominators_and_detects_improvement():
    base = [
        {"sample": str(i), "normalized_reference_words": 10, "normalized_word_errors": 5}
        for i in range(3)
    ]
    tuned = [dict(row, normalized_word_errors=2) for row in base]
    result = paired_interval(base, tuned, {str(i): str(i) for i in range(3)}, iterations=100)
    assert result["candidate_minus_baseline_wer_points"] == -30
    assert result["ci95_points"] == [-30, -30]
    tuned[0]["normalized_reference_words"] = 11
    with pytest.raises(ValueError, match="denominators"):
        paired_interval(base, tuned, {str(i): str(i) for i in range(3)}, iterations=100)
