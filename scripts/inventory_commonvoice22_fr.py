"""Acquire a bounded, community-validated French Common Voice sample.

Only source-published votes are checked; no independent listening is implied.
Output contains private transcripts and speaker pseudonyms and must stay ignored.
"""

import argparse
import csv
import hashlib
import io
import json
import re
import tarfile
from datetime import date
from pathlib import Path

import httpx
from mutagen.mp3 import MP3

from src.datasets.manifest import Manifest

REPO = "fsicoli/common_voice_22_0"
SPLITS = ("train", "dev", "test")
MAX_CLIP = 1024 * 1024


def fetch_range(client: httpx.Client, url: str, limit: int) -> bytes:
    """Bound transfer even when the server ignores the requested range."""
    content = bytearray()
    with client.stream("GET", url, headers={"Range": f"bytes=0-{limit - 1}"}) as response:
        if response.status_code != 206 or not response.headers.get("content-range", "").startswith(
            "bytes 0-"
        ):
            raise ValueError("Source did not return a bounded range")
        for chunk in response.iter_bytes():
            content.extend(chunk)
            if len(content) > limit:
                raise ValueError("Source exceeded the transfer limit")
    return bytes(content)


def reviewed_clips(
    metadata: bytes, archive: bytes, count: int = 3
) -> list[tuple[dict[str, str], bytes]]:
    """Match source TSV rows and archive entries without extracting archive paths."""
    # A partial range can end in the middle of a UTF-8 code point or TSV row.
    if not metadata.endswith(b"\n"):
        metadata = metadata.rsplit(b"\n", 1)[0] + b"\n"
    text = metadata.decode("utf-8", errors="strict")
    candidates = {}
    for row in csv.DictReader(io.StringIO(text), delimiter="\t"):
        try:
            if (
                int(row["up_votes"]) >= 2
                and int(row["down_votes"]) == 0
                and row["client_id"]
                and row["sentence_id"]
                and row["sentence"]
                and row["locale"] == "fr"
            ):
                candidates[row["path"]] = row
        except (KeyError, TypeError, ValueError):
            continue
    selected = []
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        for member in tar:
            name = Path(member.name).name
            if name not in candidates or not member.isfile() or not 0 < member.size <= MAX_CLIP:
                continue
            stream = tar.extractfile(member)
            if stream is None:
                continue
            data = stream.read(MAX_CLIP + 1)
            if len(data) != member.size:
                raise ValueError("Incomplete audio member")
            selected.append((candidates.pop(name), data))
            if len(selected) == count:
                break
    if len(selected) != count:
        raise ValueError("Insufficient reviewed matching clips in bounded source range")
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retention-until", required=True, type=date.fromisoformat)
    args = parser.parse_args()
    today = date.today()
    root = (Path.cwd() / "data" / "datasets").resolve()
    output = args.output.resolve()
    if not output.is_relative_to(root) or output == root:
        parser.error("output must be a new directory inside data/datasets")
    if args.retention_until < today:
        parser.error("retention must not precede review")
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    source_index = []
    try:
        with httpx.Client(timeout=90, follow_redirects=True) as client:
            response = client.get("https://huggingface.co/api/datasets/" + REPO)
            response.raise_for_status()
            revision = response.json()["sha"]
            if not re.fullmatch(r"[a-f0-9]{40}", revision):
                raise ValueError("Invalid source revision")
            base = f"https://huggingface.co/datasets/{REPO}/resolve/{revision}"
            for split in SPLITS:
                metadata = fetch_range(client, f"{base}/transcript/fr/{split}.tsv", 6_000_000)
                archive = fetch_range(
                    client, f"{base}/audio/fr/{split}/fr_{split}_0.tar", 2_000_000
                )
                for index, (row, audio) in enumerate(reviewed_clips(metadata, archive)):
                    sample_id = f"cv22-fr-{split}-{index}"
                    filename = sample_id + ".mp3"
                    duration = float(MP3(io.BytesIO(audio)).info.length)
                    with (output / filename).open("xb") as target:
                        target.write(audio)

                    def digest(value: str) -> str:
                        return hashlib.sha256(value.encode("utf-8")).hexdigest()

                    rows.append(
                        {
                            "sample_id": sample_id,
                            "source_id": "common-voice-22-fr",
                            "source_version": revision,
                            "subset": split,
                            "conversation_id": "prompt-" + digest(row["sentence_id"]),
                            "speaker_ids": ["speaker-" + digest(row["client_id"])],
                            "audio_sha256": hashlib.sha256(audio).hexdigest(),
                            "duration_seconds": duration,
                            "languages": ["fr"],
                            "label_status": "human_verified",
                            "label_evidence_ref": "cv22-fr-published-community-votes",
                            "label_reviewer_ref": "common-voice-community",
                            "rights": {
                                "status": "approved",
                                "basis": "license",
                                "license_id": "CC0-1.0",
                                "terms_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                                "evidence_ref": "common-voice-22-fr-cc0-source-review",
                                "reviewer_ref": "project28-source-terms-review",
                                "reviewed_on": today.isoformat(),
                                "retention_until": args.retention_until.isoformat(),
                                "train": True,
                                "evaluate": True,
                            },
                        }
                    )
                    source_index.append(
                        {
                            "sample_id": sample_id,
                            "file": filename,
                            "source_path": row["path"],
                            "source_sentence_id": row["sentence_id"],
                            "source_client_id": row["client_id"],
                            "reference_text": row["sentence"],
                            "up_votes": int(row["up_votes"]),
                            "down_votes": int(row["down_votes"]),
                        }
                    )
        manifest = Manifest.model_validate_json(
            json.dumps({"schema_version": "1", "records": rows})
        )
        with (output / "manifest.json").open("x", encoding="utf-8") as target:
            target.write(manifest.model_dump_json(indent=2) + "\n")
        with (output / "source-index.json").open("x", encoding="utf-8") as target:
            json.dump(source_index, target, indent=2, ensure_ascii=False)
        print(json.dumps({"records": len(rows), "revision": revision, "output": str(output)}))
    except (httpx.HTTPError, ValueError, KeyError, IndexError, OSError, tarfile.TarError, EOFError):
        raise SystemExit("Intake failed; inspect the private output before retrying.") from None


if __name__ == "__main__":
    main()
