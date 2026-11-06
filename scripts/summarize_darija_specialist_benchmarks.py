"""Matched fresh-Darija comparisons with reproducible paired error intervals."""

import json
import math
import random
from pathlib import Path

from scripts.summarize_multilingual_benchmarks import aggregate

ROOT = Path("docs/benchmarks/evidence/darija-specialist-20261029")
MODELS = {
    "small-base": "Whisper Small base",
    "small-darija": "Whisper Small / DVoice Darija",
    "turbo-base": "Whisper Turbo base",
    "qwen-base": "Qwen3-ASR 1.7B base BF16",
    "moulsot": "MoulSot v0.3 BF16",
}


def paired_interval(base, candidate, groups, iterations=5000, seed=20261029):
    """Candidate-minus-base WER points; paired resampling of source-prefix groups.

    Prefixes do not prove episode/speaker independence. The interval describes
    sampling variation on this source, not a population or production guarantee.
    """
    left = {row["sample"]: row for row in base}
    right = {row["sample"]: row for row in candidate}
    if set(left) != set(right) or not left or iterations < 100:
        raise ValueError("Matched samples and >=100 resamples required")
    grouped = {}
    for key, row in left.items():
        other = right[key]
        words = row["normalized_reference_words"]
        if words <= 0 or words != other["normalized_reference_words"]:
            raise ValueError("Reference denominators differ")
        group = groups[key]
        values = grouped.setdefault(group, [0, 0, 0])
        values[0] += words
        values[1] += row["normalized_word_errors"]
        values[2] += other["normalized_word_errors"]
    values = list(grouped.values())
    rng = random.Random(seed)
    differences = []
    for _ in range(iterations):
        draw = rng.choices(values, k=len(values))
        words = sum(value[0] for value in draw)
        differences.append(100 * sum(value[2] - value[1] for value in draw) / words)
    differences.sort()
    return {
        "candidate_minus_baseline_wer_points": 100
        * sum(value[2] - value[1] for value in values)
        / sum(value[0] for value in values),
        "ci95_points": [
            differences[math.floor(0.025 * iterations)],
            differences[math.ceil(0.975 * iterations) - 1],
        ],
        "resampling_groups": len(values),
        "resamples": iterations,
        "seed": seed,
        "assumption": (
            "source-prefix groups treated as independent; "
            "episode/speaker independence is unverified"
        ),
    }


def main():
    intake = json.loads((ROOT / "intake.json").read_bytes())
    expected = {row["sample_id"] for row in intake["records"]}
    groups = {row["sample_id"]: row["source_group"] for row in intake["records"]}
    models = {}
    observations = {}
    for key in MODELS:
        raw = json.loads((ROOT / (key + ".json")).read_bytes())
        rows = raw["observations"]
        if (
            raw["manifest_sha256"] != intake["manifest_sha256"]
            or len(rows) != len(expected)
            or {row["sample"] for row in rows} != expected
        ):
            raise ValueError("Incomplete or unmatched frozen sample")
        if raw["whisper_temperature_policy"] != "fixed0":
            raise ValueError("Primary comparison requires the explicit fixed-zero policy")
        observations[key] = rows
        models[key] = {
            "name": MODELS[key],
            "metrics": aggregate(rows),
            "precision": raw["precision"],
            "peak_gpu_mib": raw["sampled_whole_gpu_peak_mib"],
            "load_seconds": raw["load_seconds"],
            "backend_version": raw["backend_version"],
            "silence_control": raw.get("silence_control"),
            "qwen_parameter_dtype_counts": raw.get("qwen_parameter_dtype_counts"),
        }
    if models["qwen-base"]["precision"] != models["moulsot"]["precision"]:
        raise ValueError("Qwen comparison precision differs")
    pairs = {}
    for base, candidate in [
        ("small-base", "small-darija"),
        ("qwen-base", "moulsot"),
        ("turbo-base", "moulsot"),
    ]:
        pair = paired_interval(observations[base], observations[candidate], groups)
        pair["candidate_to_baseline_inference_time_ratio"] = (
            models[candidate]["metrics"]["rtf"] / models[base]["metrics"]["rtf"]
        )
        pairs[f"{candidate}_vs_{base}"] = pair
    summary = {
        "manifest_sha256": intake["manifest_sha256"],
        "models": models,
        "paired_comparisons": pairs,
    }
    (ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = [
        "| Model | Word error | Character error | Median clip seconds | RTF | Peak GPU MiB |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key, row in models.items():
        m = row["metrics"]
        lines.append(
            f"| {MODELS[key]} | {m['wer']:.2%} | {m['cer']:.2%} | "
            f"{m['p50_seconds']:.3f} | {m['rtf']:.4f} | {row['peak_gpu_mib']} |"
        )
    lines += [
        "",
        "Candidate-minus-baseline word error differences; negative favors the candidate.",
        "",
        "| Comparison | Difference, percentage points | Conditional paired 95% interval |",
        "|---|---:|---:|",
    ]
    for key, pair in pairs.items():
        low, high = pair["ci95_points"]
        lines.append(
            f"| {key} | {pair['candidate_minus_baseline_wer_points']:.2f} | "
            f"[{low:.2f}, {high:.2f}] |"
        )
    (ROOT / "tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
