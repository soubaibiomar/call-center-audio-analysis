"""Recompute metrics from saved predictions without loading audio or neural models."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from ml.emotion.contracts import LABELS, operational_label
from ml.evaluation.emotion import EvaluationRow, evaluate, metrics


def rescore(path: Path) -> dict[str, Any]:
    if path.stat().st_size > 20 * 1024 * 1024:
        raise ValueError("Prediction file exceeds bounds")
    raw = path.read_bytes()
    records = [EvaluationRow.model_validate(row) for row in json.loads(raw)["records"]]
    result = evaluate(records)
    baselines: dict[str, Any] = {}
    for domain in sorted({r.domain for r in records}):
        group = [r for r in records if r.domain == domain]
        baselines[domain] = {}
        for name, scores in [
            ("uniform", {label: 0.25 for label in LABELS}),
            ("constant_neutral", {label: float(label == "neutral") for label in LABELS}),
        ]:
            values = [
                r.model_copy(
                    update={
                        "probabilities": scores,
                        "emitted": operational_label(scores, r.language),
                    }
                )
                for r in group
            ]
            baselines[domain][name] = metrics(values)
    result["descriptive_baselines"] = baselines
    result["prediction_file_sha256"] = hashlib.sha256(raw).hexdigest()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("predictions", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = rescore(args.predictions)
    with args.output.open("x", encoding="utf8") as f:
        json.dump(result, f, indent=2, allow_nan=False)
