"""Offline emotion probe; validates local provenance before loading neural weights."""

import argparse
import hashlib
import json
import time
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import numpy as np

from ml.emotion.contracts import MODEL_ID, REVISION, operational_label
from ml.emotion.model import Wav2VecEmotion
from ml.evaluation.emotion import EvaluationRow, evaluate
from src.utils.audio_preprocessing import decode_resample


def validate_manifest(path: Path) -> dict[str, Any]:
    if path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("Manifest exceeds bounds")
    manifest: dict[str, Any] = json.loads(path.read_text(encoding="utf8"))
    if manifest.get("purpose") != "local evaluation only; no training":
        raise ValueError("Evaluation purpose required")
    if date.fromisoformat(manifest["retention_review_date"]) < datetime.now(UTC).date():
        raise ValueError("Retention review overdue")
    if not manifest.get("permission_basis"):
        raise ValueError("Permission evidence required")
    records = manifest["records"]
    if not 0 < len(records) <= 128 or len({r["id"] for r in records}) != len(records):
        raise ValueError("Invalid record count or duplicate IDs")
    root = path.parent.resolve()
    for record in records:
        local = (root / record["path"]).resolve()
        if not local.is_relative_to(root) or local.stat().st_size > 3 * 1024 * 1024:
            raise ValueError("Unsafe audio path or size")
        if hashlib.sha256(local.read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError("Audio checksum mismatch")
        if not record.get("license") or not record.get("label_provenance"):
            raise ValueError("Missing label/license provenance")
    return manifest


def run(manifest_path: Path, model_path: Path, output: Path) -> None:
    manifest = validate_manifest(manifest_path)
    model = Wav2VecEmotion(model_path.resolve())
    rows = []
    timings = []
    preprocessing = []
    for record in manifest["records"]:
        path = manifest_path.parent / record["path"]
        prepared = decode_resample(path.read_bytes(), str(path))
        # Offline transfer probe only; runtime still abstains on ambiguous stereo.
        samples = prepared.samples.mean(axis=0).astype(np.float32)
        if not 8000 <= len(samples) <= 160000:
            raise ValueError("Decoded clip outside fixed window bounds; no truncation")
        seed = int(record["sha256"][:8], 16)
        sigma = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2))) / 10
        noise = np.random.default_rng(seed).normal(0, sigma, len(samples)).astype(np.float32)
        for condition, waveform in [("clean", samples), ("gaussian_20db", samples + noise)]:
            start = time.perf_counter()
            scores = model.predict(waveform)
            timings.append(time.perf_counter() - start)
            rows.append(
                EvaluationRow(
                    record_id=hashlib.sha256(record["id"].encode()).hexdigest()[:16],
                    speaker_key=hashlib.sha256(record["speaker_key"].encode()).hexdigest()[:16],
                    source_revision=record["source_revision"],
                    domain=record["domain"],
                    language=record["language"],
                    accent=record["accent"],
                    noise=condition,
                    truth=record["truth"],
                    probabilities=scores,
                    emitted=operational_label(scores, record["language"]),
                )
            )
        preprocessing.append(
            dict(
                record_id=rows[-1].record_id,
                original_channels=prepared.original_channels,
                seconds=len(samples) / 16000,
                noise_seed=seed,
            )
        )
    report = evaluate(rows)
    report.update(
        model_id=MODEL_ID,
        model_revision=REVISION,
        manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        records=[r.model_dump() for r in rows],
        preprocessing=preprocessing,
        inference_seconds_total=sum(timings),
        n_original_clips=len(manifest["records"]),
        ui_decision="NO_GO: no reviewed real Moroccan telephone evaluation",
        protocol="four-class evaluation only; no training, tuning or calibration fit",
    )
    with output.open("x", encoding="utf8") as f:
        json.dump(report, f, indent=2, allow_nan=False)
    print(
        json.dumps(
            dict(
                n_original_clips=len(manifest["records"]),
                n_predictions=len(rows),
                seconds=sum(timings),
                domains={
                    k: {
                        "macro_f1": v["metrics"]["macro_f1"],
                        "ece": v["metrics"]["expected_calibration_error"],
                    }
                    for k, v in report["domains"].items()
                },
            )
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.manifest, args.model, args.output)
