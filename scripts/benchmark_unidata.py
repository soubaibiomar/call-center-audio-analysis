"""Evaluate the fixed UniData preview; references are unreviewed and noncommercial."""

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
import time
from datetime import date
from pathlib import Path

from scripts.benchmark_asr import model_fingerprint
from src.datasets.asr_benchmark import normalize


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("whisper", "qwen"), required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--input-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path("data/datasets/unidata-preview-research-20261028").resolve()
    if not args.output.resolve().is_relative_to(root) or args.output.exists():
        parser.error("output must be a new file inside the private dataset folder")
    model_dir = args.model_dir.resolve(strict=True)
    os.environ["HF_HUB_OFFLINE"] = "1"
    try:
        raw = (root / "benchmark-inputs.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != args.input_sha256:
            raise ValueError("Input manifest differs from frozen checksum")
        data = json.loads(raw)
        if (
            data["license"] != "CC-BY-NC-ND-4.0"
            or data["purpose"] != "non-commercial preliminary evaluation"
            or date.today() > date.fromisoformat(data["retention_until"])
        ):
            raise ValueError("Permission or retention is not current")
        records = data["records"]
        if len(records) != 5 or len({r["sample_id"] for r in records}) != 5:
            raise ValueError("Invalid benchmark set")
        for record in records:
            if record["label_review"] != "unverified_source_transcript":
                raise ValueError("Unexpected reference provenance")
            file = (root / record["filename"]).resolve(strict=True)
            if not file.is_relative_to(root):
                raise ValueError("Audio outside dataset root")
            digest = hashlib.sha256()
            with file.open("rb") as stream:
                for part in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(part)
            if digest.hexdigest() != record["audio_sha256"]:
                raise ValueError("Audio changed")
            if (
                hashlib.sha256(record["reference"].encode()).hexdigest()
                != record["reference_sha256"]
            ):
                raise ValueError("Reference changed")
        rapid = importlib.import_module("rapidfuzz.distance.Levenshtein")
        model_hash = model_fingerprint(model_dir)
        torch = None
        if args.backend == "whisper":
            whisper = importlib.import_module("faster_whisper")
            model = whisper.WhisperModel(str(model_dir), device="cpu", compute_type="int8")
        else:
            torch = importlib.import_module("torch")
            if not torch.cuda.is_available():
                raise ValueError("Qwen GPU backend unavailable")
            qwen = importlib.import_module("qwen_asr")
            soundfile = importlib.import_module("soundfile")
            torch.cuda.reset_peak_memory_stats()
            model = qwen.Qwen3ASRModel.from_pretrained(
                str(model_dir), dtype=torch.float16, device_map="cuda:0", max_new_tokens=256
            )
        results = []
        for record in records:
            start = time.perf_counter()
            try:
                file = root / record["filename"]
                if args.backend == "whisper":
                    segments, info = model.transcribe(str(file), beam_size=1, language=None)
                    text = " ".join(s.text.strip() for s in segments)
                    duration = float(info.duration)
                else:
                    if torch is None:
                        raise ValueError("Qwen runtime is unavailable")
                    samples, sample_rate = soundfile.read(str(file), dtype="float32")
                    if samples.ndim == 2:
                        samples = samples.mean(axis=1)
                    duration = len(samples) / sample_rate
                    texts = []
                    for offset in range(0, len(samples), 30 * sample_rate):
                        output = model.transcribe(
                            audio=(samples[offset : offset + 30 * sample_rate], sample_rate)
                        )
                        texts.append(output[0].text)
                    text = " ".join(texts)
                    torch.cuda.synchronize()
                elapsed = time.perf_counter() - start
                reference = normalize(record["reference"])
                hypothesis = normalize(text)
                words = reference.split()
                if not words or not reference or duration <= 0:
                    raise ValueError("Invalid benchmark record")
                results.append(
                    {
                        "sample_id": record["sample_id"],
                        "duration_seconds": duration,
                        "latency_seconds": elapsed,
                        "word_errors": rapid.distance(words, hypothesis.split()),
                        "reference_words": len(words),
                        "char_errors": rapid.distance(reference, hypothesis),
                        "reference_chars": len(reference),
                    }
                )
            except Exception as exc:
                # Do not print potentially sensitive transcript or path in errors.
                results.append(
                    {
                        "sample_id": record["sample_id"],
                        "failed": True,
                        "error_type": type(exc).__name__,
                    }
                )
        output = {
            "purpose": "non-commercial research; unreviewed references; provisional accuracy",
            "backend": args.backend,
            "backend_version": importlib.metadata.version(
                "faster-whisper" if args.backend == "whisper" else "qwen-asr"
            ),
            "model_dir_name": model_dir.name,
            "model_content_sha256": model_hash,
            "input_manifest_sha256": args.input_sha256,
            "normalization": "unicode-nfc-casefold-whitespace-v1-punctuation-retained",
            "qwen_chunk_seconds": 30 if args.backend == "qwen" else None,
            "device": "cpu-int8" if args.backend == "whisper" else "cuda-float16",
            "load_time_included": False,
            "peak_torch_allocated_bytes": torch.cuda.max_memory_allocated() if torch else None,
            "results": results,
        }
        with args.output.open("x", encoding="utf-8") as target:
            json.dump(output, target, indent=2)
            target.write("\n")
        failed = sum(bool(r.get("failed")) for r in results)
        print(f"Completed {len(results) - failed}/{len(records)} calls; results remain private.")
        if failed:
            raise SystemExit(1)
    except (ValueError, KeyError, OSError, ImportError):
        raise SystemExit(
            "Benchmark setup failed; inspect private inputs and local dependencies."
        ) from None


if __name__ == "__main__":
    main()
