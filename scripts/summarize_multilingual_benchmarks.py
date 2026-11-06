"""Aggregate complete pinned multilingual model executions, per language only."""

import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT = Path("docs/benchmarks/evidence/multilingual-20261029")
MODELS = {
    "tiny": "Whisper Tiny",
    "small": "Whisper Small",
    "turbo": "Whisper Turbo",
    "qwen06": "Qwen3-ASR 0.6B",
    "qwen17": "Qwen3-ASR 1.7B",
    "parakeet": "Parakeet TDT v3",
}
LANGUAGES = {"fr": "French", "ar": "Standard Arabic", "ary": "Moroccan Darija"}


def aggregate(rows):
    if not rows or any(row["normalized_reference_words"] <= 0 for row in rows):
        raise ValueError("Measured nonempty references required")
    times = sorted(row["seconds"] for row in rows)
    return {
        "clips": len(rows),
        "reference_words": sum(row["normalized_reference_words"] for row in rows),
        "wer": sum(row["normalized_word_errors"] for row in rows)
        / sum(row["normalized_reference_words"] for row in rows),
        "cer": sum(row["normalized_char_errors"] for row in rows)
        / sum(row["normalized_reference_chars"] for row in rows),
        "strict_wer": sum(row["word_errors"] for row in rows)
        / sum(row["reference_words"] for row in rows),
        "rtf": sum(row["seconds"] for row in rows) / sum(row["audio_seconds"] for row in rows),
        "p50_seconds": statistics.median(times),
        "p95_seconds": times[math.ceil(len(times) * 0.95) - 1],
        "audio_seconds": sum(row["audio_seconds"] for row in rows),
        "empty_transcripts": sum(
            row["hypothesis_sha256"] == hashlib.sha256(b"").hexdigest() for row in rows
        ),
    }


def main():
    intake = json.loads((ROOT / "intake.json").read_text(encoding="utf-8"))
    expected = {
        lang: {row["sample_id"] for row in intake["records"] if row["language"] == lang}
        for lang in LANGUAGES
    }
    summary = {
        "intake_manifest_sha256": intake["manifest_sha256"],
        "models": {},
        "unsupported": {"parakeet": ["ar", "ary"]},
    }
    for model in MODELS:
        report = json.loads((ROOT / (model + ".json")).read_text(encoding="utf-8"))
        if (
            report["manifest_sha256"] != intake["manifest_sha256"]
            or len(report["observations"]) != report["expected_observations"]
        ):
            raise ValueError("Incomplete observations or different manifest")
        metrics = {}
        for lang in ["fr"] if model == "parakeet" else LANGUAGES:
            rows = [row for row in report["observations"] if row["language"] == lang]
            if (
                len(rows) != len(expected[lang])
                or {row["sample"] for row in rows} != expected[lang]
            ):
                raise ValueError("Unmatched sample selection")
            metrics[lang] = aggregate(rows)
        summary["models"][model] = {
            "languages": metrics,
            "peak_gpu_mib": report["sampled_whole_gpu_peak_mib"],
            "load_seconds": report["load_seconds"],
            "version": report["backend_version"],
        }
    (ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = []
    for lang, title in LANGUAGES.items():
        lines += [
            f"## {title}",
            "",
            "| Model | Word error | Character error | Median clip seconds | RTF |",
            "|---|---:|---:|---:|---:|",
        ]
        for model, name in MODELS.items():
            row = summary["models"][model]["languages"].get(lang)
            if row is None:
                lines.append(f"| {name} | Not supported | — | — | — |")
            else:
                lines.append(
                    f"| {name} | {row['wer']:.2%} | {row['cer']:.2%} | "
                    f"{row['p50_seconds']:.3f} | {row['rtf']:.4f} |"
                )
        lines += [""]
    lines += [
        "## Model startup and memory",
        "",
        "GPU peak covers all tested languages for each model and includes whole-device usage.",
        "",
        "| Model | Cold model load seconds | Peak GPU MiB |",
        "|---|---:|---:|",
    ]
    for model, name in MODELS.items():
        row = summary["models"][model]
        lines.append(f"| {name} | {row['load_seconds']:.2f} | {row['peak_gpu_mib']} |")
    (ROOT / "tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
