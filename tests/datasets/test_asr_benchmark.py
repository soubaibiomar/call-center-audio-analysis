from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.benchmark_asr import model_fingerprint
from src.datasets.asr_benchmark import (
    Observation,
    QwenAdapter,
    Transcript,
    WhisperAdapter,
    edit_distance,
    normalize,
    observe,
    summarize,
)


def test_normalization_and_edit_distance() -> None:
    assert normalize("  ÉCOLE\t e\u0301  ") == "école é"
    assert edit_distance("abc", "axcd") == 2
    assert edit_distance(["hello", "world"], ["hello", "there"]) == 1


def test_adapters_have_same_output_contract() -> None:
    class Whisper:
        def transcribe(self, audio: str, **kwargs: object) -> tuple[object, object]:
            assert kwargs["language"] is None
            return iter([SimpleNamespace(text=" hello ")]), SimpleNamespace(language="fr")

    class Qwen:
        def transcribe(self, **kwargs: object) -> list[object]:
            assert kwargs["language"] is None
            return [SimpleNamespace(text="hello", language="fr")]

    assert WhisperAdapter(Whisper()).transcribe(Path("dummy")) == Transcript(
        text="hello", language="fr"
    )
    assert QwenAdapter(Qwen()).transcribe(Path("dummy")) == Transcript(text="hello", language="fr")


def test_metric_aggregation_and_missing_results() -> None:
    obs = Observation(
        language="fr",
        audio_seconds=4,
        latency_seconds=2,
        word_errors=1,
        reference_words=2,
        char_errors=2,
        reference_chars=8,
    )
    summary = summarize([obs], 2)
    assert summary["failure_rate"] == 0.5
    assert summary["metrics"] == {
        "languages": {"fr": {"count": 1, "wer": 0.5, "cer": 0.25}},
        "latency_p50_seconds": 2,
        "latency_p95_seconds": 2,
        "real_time_factor": 0.5,
        "peak_gpu_memory_bytes": None,
    }
    assert summarize([], 1)["metrics"] is None
    with pytest.raises(ValueError):
        summarize([obs], 0)


def test_empty_reference_is_rejected() -> None:
    with pytest.raises(ValueError, match="Empty"):
        observe(WhisperAdapter(object()), Path("dummy"), "   ", "fr", 1)


def test_model_fingerprint_tracks_weights_not_download_cache(tmp_path: Path) -> None:
    weights = tmp_path / "weights.bin"
    weights.write_bytes(b"one")
    before = model_fingerprint(tmp_path)
    cache = tmp_path / ".cache"
    cache.mkdir()
    (cache / "metadata").write_bytes(b"mutable")
    assert model_fingerprint(tmp_path) == before
    weights.write_bytes(b"two")
    assert model_fingerprint(tmp_path) != before
