"""Exercise private benchmark input integrity without loading neural models."""

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import benchmark_unidata
from src.datasets.asr_benchmark import edit_distance


def _fixture(tmp_path: Path) -> tuple[Path, Path, str]:
    root = tmp_path / "data/datasets/unidata-preview-research-20261028"
    root.mkdir(parents=True)
    model = tmp_path / "model"
    model.mkdir()
    records = []
    for index in range(5):
        filename = f"sample-{index}.flac"
        audio = f"audio-{index}".encode()
        (root / filename).write_bytes(audio)
        reference = "hello world"
        records.append(
            {
                "sample_id": f"sample-{index}",
                "filename": filename,
                "audio_sha256": hashlib.sha256(audio).hexdigest(),
                "reference": reference,
                "reference_sha256": hashlib.sha256(reference.encode()).hexdigest(),
                "label_review": "unverified_source_transcript",
            }
        )
    data = {
        "license": "CC-BY-NC-ND-4.0",
        "purpose": "non-commercial preliminary evaluation",
        "retention_until": "9999-12-31",
        "records": records,
    }
    raw = json.dumps(data).encode()
    (root / "benchmark-inputs.json").write_bytes(raw)
    return root, model, hashlib.sha256(raw).hexdigest()


def test_evaluates_fixed_inputs_without_writing_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, model_dir, digest = _fixture(tmp_path)
    monkeypatch.chdir(tmp_path)

    class FakeWhisper:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def transcribe(self, *_args: object, **_kwargs: object) -> tuple[object, object]:
            return iter([SimpleNamespace(text="hello there")]), SimpleNamespace(duration=2.0)

    def fake_import(name: str) -> object:
        if name == "rapidfuzz.distance.Levenshtein":
            return SimpleNamespace(distance=edit_distance)
        if name == "faster_whisper":
            return SimpleNamespace(WhisperModel=FakeWhisper)
        raise AssertionError(name)

    monkeypatch.setattr(benchmark_unidata.importlib, "import_module", fake_import)
    monkeypatch.setattr(benchmark_unidata.importlib.metadata, "version", lambda _: "test")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "benchmark",
            "--backend",
            "whisper",
            "--model-dir",
            str(model_dir),
            "--input-sha256",
            digest,
            "--output",
            str(root / "result.json"),
        ],
    )
    benchmark_unidata.main()
    raw = (root / "result.json").read_text()
    result = json.loads(raw)
    assert len(result["results"]) == 5
    assert all(item["word_errors"] == 1 for item in result["results"])
    assert "hello" not in raw


def test_changed_audio_is_rejected_before_model_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, model_dir, digest = _fixture(tmp_path)
    (root / "sample-0.flac").write_bytes(b"changed")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "benchmark",
            "--backend",
            "whisper",
            "--model-dir",
            str(model_dir),
            "--input-sha256",
            digest,
            "--output",
            str(root / "result.json"),
        ],
    )
    with pytest.raises(SystemExit, match="Benchmark setup failed"):
        benchmark_unidata.main()
    assert not (root / "result.json").exists()


def test_incorrect_purpose_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, model_dir, _ = _fixture(tmp_path)
    manifest_path = root / "benchmark-inputs.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["purpose"] = "commercial evaluation"
    raw = json.dumps(manifest).encode()
    manifest_path.write_bytes(raw)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "benchmark",
            "--backend",
            "whisper",
            "--model-dir",
            str(model_dir),
            "--input-sha256",
            hashlib.sha256(raw).hexdigest(),
            "--output",
            str(root / "result.json"),
        ],
    )
    with pytest.raises(SystemExit, match="Benchmark setup failed"):
        benchmark_unidata.main()
    assert not (root / "result.json").exists()
