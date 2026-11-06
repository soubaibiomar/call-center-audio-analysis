"""Measure local Community-1 diarization on the fixed VoxConverse reference subset."""

import argparse
import hashlib
import importlib
import json
import os
import time
from dataclasses import asdict
from datetime import date
from pathlib import Path

from scripts.benchmark_asr import model_fingerprint
from src.agents.diarization import SpeakerTurn, load_community
from src.agents.diarization_metrics import evaluate_turns


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rttm(path: Path, expected_name: str) -> list[SpeakerTurn]:
    turns = []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 10 or fields[0] != "SPEAKER" or fields[1] != expected_name:
            raise ValueError("Unexpected RTTM format")
        start, duration = float(fields[3]), float(fields[4])
        turns.append(SpeakerTurn(start, start + duration, fields[7]))
    if len({t.speaker_id for t in turns}) != 2:
        raise ValueError("Two reference speakers are required")
    return turns


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    args = parser.parse_args()
    root = args.dataset.resolve(strict=True)
    if not args.output.resolve().is_relative_to(root) or args.output.exists():
        parser.error("output must be a new file inside the private dataset folder")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["PYANNOTE_METRICS_ENABLED"] = "0"
    try:
        raw = (root / "inventory.json").read_bytes()
        inventory = json.loads(raw)
        if inventory["revision"] != "7e3ea2807400b9ed79451e20513f7a50ac4fd846":
            raise ValueError("Unexpected dataset revision")
        if date.today() > date.fromisoformat(inventory["retention_until"]):
            raise ValueError("Dataset retention period expired")
        records = inventory["records"]
        if len(records) != 2 or {item["name"] for item in records} != {"wdvva", "lubpm"}:
            raise ValueError("Expected the fixed two-record reference set")
        for record in records:
            name = record["name"]
            if name not in {"wdvva", "lubpm"}:
                raise ValueError("Unexpected reference item")
            for suffix in (".wav", ".rttm"):
                if file_digest(root / (name + suffix)) != record["files"][suffix]["sha256"]:
                    raise ValueError("Input hash mismatch")
        torch = importlib.import_module("torch")
        model_hash = model_fingerprint(args.model_dir.resolve(strict=True))
        # pathlib sorts Windows paths case-insensitively and POSIX paths
        # case-sensitively; these are the two verified fingerprints of this snapshot.
        if model_hash not in {
            "84f2bff8c23a707d873fc7f5951dec224475bec7a673dd45a53380c04e608b15",
            "90258fe399a87a64586233dd81ea9ed01df831c29f23a886066c0b28e0aa0ecd",
        }:
            raise ValueError("Model content differs from the pinned local snapshot")
        if args.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA not available")
        if args.device == "cuda":
            torch.cuda.reset_peak_memory_stats()
        model = load_community(str(args.model_dir.resolve(strict=True)))
        model.pipeline.to(torch.device(args.device))
        outputs = []
        for record in records:
            name = record["name"]
            reference = read_rttm(root / (name + ".rttm"), name)
            start = time.perf_counter()
            turns = model.turns(str(root / (name + ".wav")))
            if args.device == "cuda":
                torch.cuda.synchronize()
            elapsed = time.perf_counter() - start
            metrics = evaluate_turns(reference, turns, duration=record["duration_seconds"])
            outputs.append(
                {
                    "sample": name,
                    "duration_seconds": record["duration_seconds"],
                    "latency_seconds": elapsed,
                    "hypothesis_speakers": len({turn.speaker_id for turn in turns}),
                    "metrics": asdict(metrics),
                    "role_accuracy": metrics.role_accuracy,
                    "role_coverage": metrics.role_coverage,
                }
            )
        result = {
            "model": "pyannote/speaker-diarization-community-1",
            "model_revision": "3533c8cf8e369892e6b79ff1bf80f7b0286a54ee",
            "model_content_sha256": model_hash,
            "dataset_inventory_sha256": hashlib.sha256(raw).hexdigest(),
            "device": args.device,
            "collar_seconds": 0.0,
            "skip_overlap": False,
            "peak_torch_allocated_bytes": torch.cuda.max_memory_allocated()
            if args.device == "cuda"
            else None,
            "records": outputs,
        }
        with args.output.open("x", encoding="utf-8") as target:
            json.dump(result, target, indent=2, allow_nan=False)
            target.write("\n")
        print("Completed local diarization evaluation on two reference recordings.")
    except (OSError, ValueError, KeyError, ImportError, RuntimeError):
        raise SystemExit(
            "Diarization benchmark failed; inspect local inputs and runtime."
        ) from None


if __name__ == "__main__":
    main()
