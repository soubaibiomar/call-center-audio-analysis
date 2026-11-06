"""Synthetic scoring inputs; these are not a neural-model benchmark."""

from types import SimpleNamespace

import pytest

from src.agents.diarization import SpeakerTurn
from src.agents.diarization_metrics import evaluate_turns


def test_overlap_and_role_diagnostics(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.agents.diarization_metrics as module

    class Annotation:
        def __setitem__(self, _key: object, _value: object) -> None:
            pass

    class Metric:
        def __init__(self, **kwargs: object) -> None:
            assert kwargs == {"collar": 0.0, "skip_overlap": False}

        def __call__(self, *_args: object, **_kwargs: object) -> dict[str, float]:
            return {"total": 4.0, "diarization error rate": 0.25}

    core = SimpleNamespace(
        Annotation=Annotation, Segment=lambda a, b: (a, b), Timeline=lambda **k: k
    )
    monkeypatch.setattr(
        module.importlib,
        "import_module",
        lambda name: core
        if name == "pyannote.core"
        else SimpleNamespace(DiarizationErrorRate=Metric),
    )
    result = evaluate_turns(
        [SpeakerTurn(0, 2, "a"), SpeakerTurn(1, 3, "b")],
        [SpeakerTurn(0, 2, "x"), SpeakerTurn(2, 3, "y")],
        duration=4,
        reference_roles={"a": "Agent", "b": "Customer"},
        hypothesis_roles={"x": "Agent", "y": "Customer"},
    )
    assert result.der == 0.25
    assert result.overlap_reference_seconds == result.overlap_missed_seconds == 1
    assert result.role_reference_seconds == result.role_correct_seconds == 2
    assert result.role_accuracy == result.role_coverage == 1

    unknown = evaluate_turns(
        [SpeakerTurn(0, 1, "a")],
        [SpeakerTurn(0, 1, "x")],
        duration=2,
        reference_roles={"a": "Agent"},
        hypothesis_roles={"x": "Unknown"},
    )
    assert unknown.role_accuracy == unknown.role_coverage == 0
    missing = evaluate_turns(
        [SpeakerTurn(0, 1, "a")],
        [SpeakerTurn(0, 1, "x")],
        duration=2,
        reference_roles={"a": "Agent"},
    )
    assert missing.role_reference_seconds == 1
    assert missing.role_accuracy == missing.role_coverage == 0


def test_invalid_scoring_region_rejected_before_import() -> None:
    with pytest.raises(ValueError):
        evaluate_turns([SpeakerTurn(0, 2, "a")], [], duration=1)
    with pytest.raises(ValueError):
        evaluate_turns([], [], duration=1)
