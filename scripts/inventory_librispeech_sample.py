"""Acquire three small public LibriSpeech examples into an ignored private intake.

The source license is CC BY 4.0. Records remain pending and transcripts unreviewed;
this command does not grant training permission or create a test split.
"""

import argparse
import hashlib
import io
import json
import re
import wave
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from src.datasets.manifest import Manifest

DATASET = "openslr/librispeech_asr"
SPLITS = ("train.100", "validation", "test")
MAX_AUDIO_BYTES = 2 * 1024 * 1024


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = (Path.cwd() / "data" / "datasets").resolve()
    output = args.output.resolve()
    if not output.is_relative_to(root) or output == root:
        parser.error("output must be a new directory inside data/datasets")
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    source_index = []
    today = date.today().isoformat()
    try:
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            repo = client.get("https://huggingface.co/api/datasets/" + DATASET)
            repo.raise_for_status()
            revision = repo.json()["sha"]
            if not re.fullmatch(r"[a-f0-9]{40}", revision):
                raise ValueError("Invalid source revision")
            for index, split in enumerate(SPLITS):
                response = client.get(
                    "https://datasets-server.huggingface.co/first-rows",
                    params={"dataset": DATASET, "config": "clean", "split": split},
                )
                response.raise_for_status()
                row = response.json()["rows"][0]["row"]
                address = row["audio"][0]["src"]
                parsed = urlsplit(address)
                if parsed.scheme != "https" or parsed.hostname != "datasets-server.huggingface.co":
                    raise ValueError("Unexpected audio host")
                if parsed.username or parsed.password:
                    raise ValueError("Unexpected audio credentials")
                chunks = bytearray()
                with client.stream("GET", address) as audio:
                    audio.raise_for_status()
                    for chunk in audio.iter_bytes():
                        chunks.extend(chunk)
                        if len(chunks) > MAX_AUDIO_BYTES:
                            raise ValueError("Public example exceeds the 2 MiB limit")
                with wave.open(io.BytesIO(chunks), "rb") as clip:
                    duration = clip.getnframes() / clip.getframerate()
                sample_id = f"librispeech-{split.replace('.', '-')}-{index}"
                filename = sample_id + ".wav"
                with (output / filename).open("xb") as target:
                    target.write(chunks)
                rows.append(
                    {
                        "sample_id": sample_id,
                        "source_id": "openslr-librispeech",
                        "source_version": "hf-observed-" + revision,
                        "subset": split.replace(".", "-"),
                        "conversation_id": f"libri-chapter-{row['chapter_id']}",
                        "speaker_ids": [f"libri-speaker-{row['speaker_id']}"],
                        "audio_sha256": hashlib.sha256(chunks).hexdigest(),
                        "duration_seconds": duration,
                        "languages": ["en"],
                        "label_status": "unreviewed",
                        "rights": {
                            "status": "pending",
                            "basis": "license",
                            "license_id": "CC-BY-4.0",
                            "terms_url": "https://creativecommons.org/licenses/by/4.0/",
                            "evidence_ref": "source-card-" + today,
                            "reviewer_ref": "pending",
                            "reviewed_on": today,
                            "retention_until": today,
                            "train": False,
                            "evaluate": False,
                        },
                    }
                )
                source_index.append(
                    {
                        "sample_id": sample_id,
                        "file": filename,
                        "source_id": str(row["id"]),
                        "reference_text_unreviewed": row["text"],
                    }
                )
        manifest = Manifest.model_validate_json(
            json.dumps({"schema_version": "1", "records": rows})
        )
        with (output / "manifest.json").open("x", encoding="utf-8") as target:
            target.write(manifest.model_dump_json(indent=2) + "\n")
        with (output / "source-index.json").open("x", encoding="utf-8") as target:
            json.dump(source_index, target, indent=2)
        print(
            json.dumps(
                {
                    "records": len(rows),
                    "duration_seconds": sum(r["duration_seconds"] for r in rows),
                    "audio_bytes": sum((output / x["file"]).stat().st_size for x in source_index),
                    "speaker_ids": len({r["speaker_ids"][0] for r in rows}),
                    "status": "pending rights and human-label review",
                    "output": str(output),
                },
                indent=2,
            )
        )
    except (httpx.HTTPError, ValueError, KeyError, IndexError, OSError, wave.Error):
        raise SystemExit(
            "Public intake failed; inspect the private output and retry after review."
        ) from None


if __name__ == "__main__":
    main()
