"""Validate parsing of the fixed public diarization reference format."""

import pytest

from scripts.benchmark_diarization import read_rttm


def test_read_rttm_rejects_single_speaker_and_wrong_recording(tmp_path):
    path = tmp_path / "example.rttm"
    path.write_text("SPEAKER example 1 0.0 1.0 <NA> <NA> speaker1 <NA> <NA>\n")
    with pytest.raises(ValueError, match="Two reference speakers"):
        read_rttm(path, "example")
    with pytest.raises(ValueError, match="Unexpected RTTM format"):
        read_rttm(path, "another")


def test_read_rttm_returns_two_timed_speakers(tmp_path):
    path = tmp_path / "example.rttm"
    path.write_text(
        "SPEAKER example 1 0.0 1.0 <NA> <NA> speaker1 <NA> <NA>\n"
        "SPEAKER example 1 0.5 1.5 <NA> <NA> speaker2 <NA> <NA>\n"
    )
    turns = read_rttm(path, "example")
    assert [(turn.start, turn.end, turn.speaker_id) for turn in turns] == [
        (0.0, 1.0, "speaker1"),
        (0.5, 2.0, "speaker2"),
    ]
