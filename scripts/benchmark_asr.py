"""Run a private, validation-only ASR smoke test with cached local models."""

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
from datetime import date
from pathlib import Path

from src.datasets.asr_benchmark import QwenAdapter, Transcriber, WhisperAdapter, observe, summarize
from src.datasets.manifest import Manifest
from src.datasets.split import load_lock_verified, plan_splits


def model_fingerprint(directory: Path) -> str:
    """Hash names and bytes, including linked cache files, without loading them into memory."""
    digest = hashlib.sha256()
    for path in sorted(
        p
        for p in directory.rglob("*")
        if p.is_file() and ".cache" not in p.relative_to(directory).parts
    ):
        digest.update(path.relative_to(directory).as_posix().encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--lock-sha256", required=True)
    parser.add_argument("--backend", choices=("whisper", "qwen"), required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.dataset.resolve()
    if not root.is_relative_to((Path.cwd() / "data" / "datasets").resolve()):
        parser.error("dataset must reside under data/datasets")
    if not args.output.resolve().is_relative_to(root) or args.output.exists():
        parser.error("output must be a new file inside the dataset directory")
    model_dir = args.model_dir.resolve(strict=True)
    if not model_dir.is_dir():
        parser.error("model-dir must be a local model directory")
    os.environ["HF_HUB_OFFLINE"] = "1"
    try:
        raw = (root / "manifest.json").read_bytes()
        manifest = Manifest.model_validate_json(raw)
        lock = load_lock_verified((root / "split-lock.json").read_bytes(), args.lock_sha256)
        plan_splits(manifest, as_of=date.today(), seed=lock.seed, prior=lock)
        source = json.loads((root / "source-index.json").read_text(encoding="utf-8"))
        indexed = {row["sample_id"]: row for row in source}
        selected = [r for r in manifest.records if lock.assignments[r.sample_id] == "validation"]
        if not selected or len(indexed) != len(source):
            raise ValueError("Invalid source index")
        model_hash = model_fingerprint(model_dir)
        inputs = []
        for record in selected:
            if len(record.languages) != 1:
                raise ValueError("Code-switched inputs require span-level scoring")
            item = indexed[record.sample_id]
            file = (root / item["file"]).resolve(strict=True)
            if not file.is_relative_to(root) or not file.is_file():
                raise ValueError("Audio path outside dataset")
            if file_sha256(file) != record.audio_sha256:
                raise ValueError("Audio hash mismatch")
            if not isinstance(item["reference_text"], str) or not item["reference_text"].strip():
                raise ValueError("Missing reference")
            inputs.append((record, item, file))
        adapter: Transcriber
        if args.backend == "whisper":
            module = importlib.import_module("faster_whisper")
            model = module.WhisperModel(str(model_dir), device="cpu", compute_type="int8")
            adapter = WhisperAdapter(model)
        else:
            module = importlib.import_module("qwen_asr")
            torch = importlib.import_module("torch")
            model = module.Qwen3ASRModel.from_pretrained(
                str(model_dir), dtype=torch.float32, device_map="cpu", max_new_tokens=256
            )
            adapter = QwenAdapter(model)
        observations = []
        failed = 0
        for record, item, audio in inputs:
            try:
                observations.append(
                    observe(
                        adapter,
                        audio,
                        item["reference_text"],
                        record.languages[0],
                        record.duration_seconds,
                    )
                )
            except Exception:
                failed += 1
        result = {
            "schema_version": "1",
            "purpose": "validation smoke test; not telephone evaluation or model selection",
            "backend": args.backend,
            "model_dir_name": model_dir.name,
            "model_content_sha256": model_hash,
            "backend_version": importlib.metadata.version(
                "faster-whisper" if args.backend == "whisper" else "qwen-asr"
            ),
            "dataset_manifest_sha256": hashlib.sha256(raw).hexdigest(),
            "split_lock_sha256": args.lock_sha256,
            "partition": "validation",
            "sample_ids": [r.sample_id for r, _, _ in inputs],
            "audio_sha256": [r.audio_sha256 for r, _, _ in inputs],
            "reference_sha256": [
                hashlib.sha256(x["reference_text"].encode()).hexdigest() for _, x, _ in inputs
            ],
            "normalization": "unicode-nfc-casefold-whitespace-v1-punctuation-retained",
            "percentile_method": "nearest-rank",
            "device": "cpu",
            "load_time_included": False,
            "result": summarize(observations, len(inputs)),
        }
        with args.output.open("x", encoding="utf-8") as out:
            json.dump(result, out, indent=2)
            out.write("\n")
        print(
            f"Completed {len(inputs) - failed}/{len(inputs)} validation clips; "
            "details stored privately."
        )
        if failed:
            raise SystemExit(1)
    except (ValueError, KeyError, OSError, ImportError):
        raise SystemExit(
            "Benchmark setup failed; inspect private inputs and local dependencies."
        ) from None


if __name__ == "__main__":
    main()
