"""Score locally prepared diarization annotations without publishing their contents."""

import argparse
import hashlib
import importlib.metadata
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from src.agents.diarization import Role, SpeakerTurn
from src.agents.diarization_metrics import evaluate_turns


def read_annotation(path: Path) -> tuple[list[SpeakerTurn], dict[str, Role]]:
    """Read JSON turns and optional per-speaker roles from a trusted local file."""
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) - {"turns", "roles"}:
        raise ValueError("Invalid annotation object")
    if not isinstance(data.get("turns"), list) or not isinstance(data.get("roles", {}), dict):
        raise ValueError("Invalid annotation fields")
    turns = []
    for item in data["turns"]:
        if not isinstance(item, dict) or set(item) != {"start", "end", "speaker_id"}:
            raise ValueError("Invalid turn")
        if not isinstance(item["speaker_id"], str):
            raise ValueError("Invalid speaker")
        turns.append(SpeakerTurn(float(item["start"]), float(item["end"]), item["speaker_id"]))
    roles = data.get("roles", {})
    if any(
        not isinstance(k, str) or v not in {"Agent", "Customer", "Unknown"}
        for k, v in roles.items()
    ):
        raise ValueError("Invalid roles")
    return turns, cast(dict[str, Role], roles)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--hypothesis", type=Path, required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--collar", type=float, default=0.0)
    parser.add_argument("--skip-overlap", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        reference, ref_roles = read_annotation(args.reference)
        hypothesis, hyp_roles = read_annotation(args.hypothesis)
        metrics = evaluate_turns(
            reference,
            hypothesis,
            duration=args.duration,
            collar=args.collar,
            skip_overlap=args.skip_overlap,
            reference_roles=ref_roles,
            hypothesis_roles=hyp_roles,
        )
        result = {
            "schema_version": "1",
            "reference_sha256": hashlib.sha256(args.reference.read_bytes()).hexdigest(),
            "hypothesis_sha256": hashlib.sha256(args.hypothesis.read_bytes()).hexdigest(),
            "pyannote_metrics_version": importlib.metadata.version("pyannote.metrics"),
            "duration_seconds": args.duration,
            "collar_seconds": args.collar,
            "skip_overlap": args.skip_overlap,
            "metrics": asdict(metrics),
            "role_accuracy": metrics.role_accuracy,
            "role_coverage": metrics.role_coverage,
        }
        with args.output.open("x", encoding="utf-8") as out:
            json.dump(result, out, indent=2, allow_nan=False)
            out.write("\n")
        print("Diarization metrics written; verify source permissions and reference quality.")
    except (ValueError, TypeError, KeyError, OSError, RuntimeError):
        raise SystemExit(
            "Diarization evaluation failed; inspect private inputs and runtime."
        ) from None


if __name__ == "__main__":
    main()
