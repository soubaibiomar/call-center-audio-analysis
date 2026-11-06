"""Aggregate recorded execution receipts; never substitute missing measurements."""

import json
import math
import statistics
from pathlib import Path

ROOT = Path("docs/benchmarks/evidence/upgrade-20261029")


def aggregate_asr(report):
    rows = report["observations"]
    if not rows or any(row["reference_words"] <= 0 for row in rows):
        raise ValueError("Nonempty measured references required")
    return {
        "complete": len(rows) == 3 * report["repetitions"],
        "observations": len(rows),
        "unique_calls": len({row["sample"] for row in rows}),
        "wer": sum(row["word_errors"] for row in rows)
        / sum(row["reference_words"] for row in rows),
        "cer": sum(row["char_errors"] for row in rows)
        / sum(row["reference_chars"] for row in rows),
        "rtf": sum(row["seconds"] for row in rows) / sum(row["audio_seconds"] for row in rows),
        "p50_call_seconds": statistics.median(row["seconds"] for row in rows),
        "load_seconds": report["load_seconds"],
        "sampled_whole_gpu_peak_mib": report.get("sampled_whole_gpu_peak_mib"),
        "device": report["device"],
        "precision": report["precision"],
    }


def main():
    summary = {"asr": {}, "llm": {}, "retrieval": None}
    for file in ROOT.glob("asr-*.json"):
        if file.name == "asr-execution.json":
            continue
        summary["asr"][file.stem] = aggregate_asr(json.loads(file.read_text()))
    for model in json.loads((ROOT / "llm-quality.json").read_text())["models"]:
        rows = model["rows"]
        latencies = sorted(row["seconds"] for row in rows)
        summary["llm"][model["model"]] = {
            "complete": len(rows) == 18,
            "observations": len(rows),
            "schema_valid": sum(row["schema_valid"] for row in rows),
            "correct_resolution": sum(row["correct_resolution"] for row in rows),
            "p50_seconds": statistics.median(latencies),
            "p95_seconds": latencies[math.ceil(0.95 * len(latencies)) - 1],
            "mean_seconds": statistics.mean(latencies),
        }
    retrieval = ROOT / "retrieval.json"
    if retrieval.exists():
        report = json.loads(retrieval.read_text())
        rows = report["observations"]
        summary["retrieval"] = {
            "complete": len(rows) == 36,
            "unique_queries": len({row["query"] for row in rows}),
            "dense_top1": statistics.mean(row["dense"]["top1"] for row in rows),
            "reranked_top1": statistics.mean(row["reranked"]["top1"] for row in rows),
            "dense_mrr5": statistics.mean(row["dense"]["reciprocal_rank"] for row in rows),
            "reranked_mrr5": statistics.mean(row["reranked"]["reciprocal_rank"] for row in rows),
            "recall5": statistics.mean(row["dense"]["recall5"] for row in rows),
            "p50_dense_seconds": statistics.median(row["dense_seconds"] for row in rows),
            "p50_reranked_total_seconds": statistics.median(
                row["dense_seconds"] + row["rerank_additional_seconds"] for row in rows
            ),
        }
    (ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
