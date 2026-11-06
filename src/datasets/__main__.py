"""Run metadata validation and make a new local lock without loading recordings."""

import argparse
from datetime import date
from pathlib import Path

from src.datasets.manifest import Manifest
from src.datasets.split import load_lock_verified, plan_splits


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--as-of", required=True, type=date.fromisoformat)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prior-lock", type=Path)
    parser.add_argument("--prior-sha256")
    args = parser.parse_args()
    if bool(args.prior_lock) != bool(args.prior_sha256):
        parser.error("--prior-lock and --prior-sha256 must be supplied together")
    try:
        manifest = Manifest.model_validate_json(args.manifest.read_bytes())
        prior = (
            load_lock_verified(args.prior_lock.read_bytes(), args.prior_sha256)
            if args.prior_lock
            else None
        )
        result = plan_splits(manifest, as_of=args.as_of, seed=args.seed, prior=prior)
    except ValueError:
        # Validation errors can include rejected, potentially sensitive input values.
        raise SystemExit(
            "Manifest or split validation failed; inspect the private inputs."
        ) from None
    with args.output.open("x", encoding="utf-8", newline="\n") as file:
        file.write(result.model_dump_json(indent=2) + "\n")
    print("Validated and wrote a new split lock; store the file and its hash privately.")


if __name__ == "__main__":
    main()
