"""Prepare the user-selected noncommercial UniData preview for provisional evaluation."""

import argparse
import csv
import hashlib
import io
import json
import re
from datetime import date
from pathlib import Path

import httpx

ROOT = Path("data/datasets/unidata-preview-research-20261028")
API = "https://www.kaggle.com/api/v1/datasets/"
SOURCE = "unidpro/call-center-audio"
RETAIN_UNTIL = date(2026, 11, 28)
LINE = re.compile(r"^\[[^\]]+\]\s*\[\d{2}:\d{2}:\d{2}\]:\s*(.*)$")


def extract_reference(transcript: str) -> str:
    """Remove source turn and time markers, but preserve spoken text and punctuation."""
    lines = transcript.splitlines()
    matched = [LINE.fullmatch(line.strip()) for line in lines if line.strip()]
    if not matched or any(match is None for match in matched):
        raise ValueError("Reference format is not fully understood")
    return " ".join(match.group(1) for match in matched if match is not None)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true", help="resume a partial private intake")
    args = parser.parse_args()
    if date.today() > RETAIN_UNTIL:
        raise SystemExit("The selected retention deadline has passed.")
    root = ROOT.resolve()
    root.mkdir(parents=True, exist_ok=args.resume)
    if (root / "benchmark-inputs.json").exists():
        raise SystemExit("A completed intake already exists; it will not be overwritten.")
    records = []
    try:
        with httpx.Client(timeout=120, follow_redirects=True) as client:
            view = client.get(API + "view/" + SOURCE)
            view.raise_for_status()
            if view.json()["currentVersionNumber"] != 1:
                raise ValueError("Source version changed")
            listing = client.get(API + "list/" + SOURCE)
            listing.raise_for_status()
            audio = sorted(
                (f for f in listing.json()["datasetFiles"] if f["name"].endswith(".flac")),
                key=lambda f: f["name"],
            )
            if len(audio) != 5 or sum(f["totalBytes"] for f in audio) > 50_000_000:
                raise ValueError("Unexpected preview inventory")
            response = client.get(
                API + "download/" + SOURCE, params={"fileName": "files/metainfo.csv"}
            )
            response.raise_for_status()
            rows = list(
                csv.DictReader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";")
            )
            by_id = {row["call_id"]: row for row in rows}
            if len(by_id) != 5:
                raise ValueError("Unexpected metadata inventory")
            for index, entry in enumerate(audio, 1):
                row = by_id[Path(entry["name"]).stem]
                reference = extract_reference(row["Transcription"])
                if not reference:
                    raise ValueError("Empty reference")
                name = f"sample-{index:02}.flac"
                digest = hashlib.sha256()
                size = 0
                path = root / name
                if path.exists():
                    if not args.resume or not path.is_file():
                        raise ValueError("Unexpected existing audio")
                    with path.open("rb") as existing:
                        for chunk in iter(lambda: existing.read(1024 * 1024), b""):
                            size += len(chunk)
                            digest.update(chunk)
                if size > entry["totalBytes"]:
                    raise ValueError("Unexpected audio length")
                if size < entry["totalBytes"]:
                    headers = {"Range": f"bytes={size}-"} if size else {}
                    with client.stream(
                        "GET",
                        API + "download/" + SOURCE,
                        params={"fileName": entry["name"]},
                        headers=headers,
                    ) as asset:
                        asset.raise_for_status()
                        if size and (
                            asset.status_code != 206
                            or not asset.headers.get("content-range", "").startswith(
                                f"bytes {size}-"
                            )
                        ):
                            raise ValueError("Source refused the resume range")
                        with path.open("ab" if path.exists() else "xb") as out:
                            for chunk in asset.iter_bytes():
                                size += len(chunk)
                                if size > entry["totalBytes"] or size > 25_000_000:
                                    raise ValueError("Unexpected audio length")
                                digest.update(chunk)
                                out.write(chunk)
                if size != entry["totalBytes"]:
                    raise ValueError("Incomplete audio")
                records.append(
                    {
                        "sample_id": f"sample-{index:02}",
                        "filename": name,
                        "audio_sha256": digest.hexdigest(),
                        "reference_sha256": hashlib.sha256(reference.encode("utf-8")).hexdigest(),
                        "reference": reference,
                        "label_review": "unverified_source_transcript",
                    }
                )
        manifest = {
            "source": SOURCE,
            "version": 1,
            "license": "CC-BY-NC-ND-4.0",
            "purpose": "non-commercial preliminary evaluation",
            "retention_until": RETAIN_UNTIL.isoformat(),
            "source_metadata_sha256": hashlib.sha256(response.content).hexdigest(),
            "records": records,
        }
        with (root / "benchmark-inputs.json").open("x", encoding="utf-8") as out:
            json.dump(manifest, out, ensure_ascii=False, indent=2)
            out.write("\n")
        print(f"Prepared {len(records)} restricted preview recordings and unreviewed references.")
    except (httpx.HTTPError, OSError, ValueError, KeyError):
        raise SystemExit("Preview intake failed; review the private partial output.") from None


if __name__ == "__main__":
    main()
