import json
from pathlib import Path

import pytest

from scripts.evaluate_diarization import read_annotation


def test_reads_timed_turns_and_grounded_roles(tmp_path: Path) -> None:
    path = tmp_path / "turns.json"
    path.write_text(
        json.dumps({"turns": [{"start": 0, "end": 1, "speaker_id": "a"}], "roles": {"a": "Agent"}})
    )
    turns, roles = read_annotation(path)
    assert turns[0].speaker_id == "a"
    assert roles == {"a": "Agent"}


def test_rejects_unknown_fields_and_unrecognized_roles(tmp_path: Path) -> None:
    path = tmp_path / "turns.json"
    path.write_text(json.dumps({"turns": [], "roles": {"a": "Manager"}}))
    with pytest.raises(ValueError):
        read_annotation(path)
    path.write_text(json.dumps({"turns": [], "transcript": "private"}))
    with pytest.raises(ValueError):
        read_annotation(path)
