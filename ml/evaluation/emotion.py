"""Reproducible four-class metrics with abstention and explicit domain separation."""

import importlib
import math
from collections import Counter
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ml.emotion.contracts import LABELS, EmotionLabel


class EvaluationRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    record_id: str = Field(min_length=1)
    speaker_key: str = Field(min_length=1)
    source_revision: str = Field(min_length=1)
    domain: Literal["acted", "media", "real_call"]
    language: str
    accent: str = "unverified"
    noise: str
    truth: Literal["neutral", "happy", "angry", "sad"]
    probabilities: dict[str, float]
    emitted: EmotionLabel

    @model_validator(mode="after")
    def valid_distribution(self) -> "EvaluationRow":
        if (
            set(self.probabilities) != set(LABELS)
            or any(not math.isfinite(p) or not 0 <= p <= 1 for p in self.probabilities.values())
            or not math.isclose(sum(self.probabilities.values()), 1, abs_tol=1e-5)
        ):
            raise ValueError("Invalid four-class probability distribution")
        return self


def metrics(rows: list[EvaluationRow], *, bins: int = 10) -> dict[str, Any]:
    """ECE uses all raw predictions, not just accepted labels; fixed taxonomy F1."""
    if not rows or not 1 <= bins <= 100:
        raise ValueError("Nonempty rows and 1–100 calibration bins required")
    sklearn = importlib.import_module("sklearn.metrics")
    truth = [r.truth for r in rows]
    raw = [max(LABELS, key=lambda label: r.probabilities[label]) for r in rows]
    emitted = [r.emitted for r in rows]
    precision, recall, f1, support = sklearn.precision_recall_fscore_support(
        truth, raw, labels=list(LABELS), zero_division=0
    )
    _, _, operational_f1, _ = sklearn.precision_recall_fscore_support(
        truth, emitted, labels=list(LABELS), zero_division=0
    )
    reliability = []
    ece = 0.0
    for b in range(bins):
        selected = [
            i
            for i, r in enumerate(rows)
            if min(int(max(r.probabilities.values()) * bins), bins - 1) == b
        ]
        if not selected:
            continue
        confidence = sum(max(rows[i].probabilities.values()) for i in selected) / len(selected)
        accuracy = sum(raw[i] == truth[i] for i in selected) / len(selected)
        ece += len(selected) / len(rows) * abs(accuracy - confidence)
        reliability.append(dict(bin=b, n=len(selected), confidence=confidence, accuracy=accuracy))
    accepted = [i for i, r in enumerate(rows) if r.emitted != "Unknown"]
    counts: Counter[str] = Counter(truth)
    labels = [*LABELS, "Unknown"]
    return dict(
        n=len(rows),
        labels=labels,
        confusion_matrix=sklearn.confusion_matrix(truth, emitted, labels=labels).tolist(),
        raw_confusion_matrix=sklearn.confusion_matrix(truth, raw, labels=list(LABELS)).tolist(),
        macro_f1=float(sum(f1) / 4),
        operational_macro_f1=float(sum(operational_f1) / 4),
        per_class={
            label: dict(
                precision=float(precision[i]),
                recall=float(recall[i]),
                f1=float(f1[i]),
                support=int(support[i]),
            )
            for i, label in enumerate(LABELS)
        },
        missing_classes=[label for label in LABELS if not counts[label]],
        imbalance_ratio=max(counts.values()) / min(counts.values()),
        expected_calibration_error=ece,
        calibration_bins=bins,
        reliability=reliability,
        coverage=len(accepted) / len(rows),
        unknown_rate=1 - len(accepted) / len(rows),
        selective_accuracy=(
            sum(emitted[i] == truth[i] for i in accepted) / len(accepted) if accepted else None
        ),
    )


def evaluate(rows: list[EvaluationRow]) -> dict[str, Any]:
    if not rows or len({(r.record_id, r.noise) for r in rows}) != len(rows):
        raise ValueError("Empty evaluation or duplicate record/condition")
    domains = {}
    for domain in sorted({r.domain for r in rows}):
        group = [r for r in rows if r.domain == domain]
        slices = {}
        gaps = {}
        for axis in ("language", "accent", "noise"):
            slices[axis] = {
                value: metrics([r for r in group if getattr(r, axis) == value])
                for value in sorted({getattr(r, axis) for r in group})
            }
            eligible = [
                m["macro_f1"]
                for value, m in slices[axis].items()
                if m["n"] >= 4 and value not in {"unknown", "unverified"}
            ]
            gaps[axis] = max(eligible) - min(eligible) if len(eligible) >= 2 else None
        domains[domain] = dict(metrics=metrics(group), slices=slices, worst_slice_gaps=gaps)
    return dict(
        domains=domains,
        real_call_evaluation_available="real_call" in domains,
        note="Domains kept separate. Correlated noise variants are not independent samples. "
        "Unknown accents are not inferred from identities. No training or calibration fit.",
    )
