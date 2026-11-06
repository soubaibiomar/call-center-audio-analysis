"""Freeze a fresh Darija comparison and audit the prior source/audio mapping.

Local non-commercial evaluation only. No training or redistribution. Selection
excludes prior clip IDs, source-segment prefixes, reference hashes and audio hashes.
Segment prefixes do not establish speaker/episode independence.
"""

import concurrent.futures
import io
import json
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from scripts.intake_multilingual_benchmark import SOURCES, sha, viewer_rows

ROOT = Path(".local/darija-specialist-20261029")
EVIDENCE = Path("docs/benchmarks/evidence/darija-specialist-20261029")
PREVIOUS = Path(".local/multilingual-asr-20261029/manifest.json")
COUNT = 100


def prefix(value):
    return str(value).split("_", 1)[0]


def eligible(item, excluded_ids, excluded_groups, excluded_references):
    row = item["row"]
    return (
        2 <= row["duration"] <= 20
        and len(row["transcription"].split()) >= 3
        and row["seg_id"] not in excluded_ids
        and prefix(row["seg_id"]) not in excluded_groups
        and sha(row["transcription"].encode()) not in excluded_references
    )


def fetch_audio(item, revision):
    import soundfile as sf

    url = item["row"]["audio"][0]["src"]
    if (
        urlsplit(url).hostname != "datasets-server.huggingface.co"
        or revision not in urlsplit(url).path
    ):
        raise ValueError("Unpinned audio URL")
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()
            content = bytearray()
            for block in response.iter_bytes():
                content.extend(block)
                if len(content) > 4 * 1024 * 1024:
                    raise ValueError("Audio exceeds per-clip limit")
    samples, rate = sf.read(io.BytesIO(content), dtype="float32")
    if not 2 <= len(samples) / rate <= 20.1:
        raise ValueError("Audio duration mismatch")
    return bytes(content), len(samples) / rate, int(rate), list(samples.shape)


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if (ROOT / "manifest.json").exists():
        raise ValueError("Frozen intake already exists")
    old_raw = PREVIOUS.read_bytes()
    previous = json.loads(old_raw)
    old = [row for row in previous["records"] if row["language"] == "ary"]
    excluded_ids = {row["source_id"] for row in old}
    excluded_groups = {prefix(value) for value in excluded_ids}
    excluded_references = {row["reference_sha256"] for row in old}
    excluded_audio = {row["audio_sha256"] for row in old}
    source = SOURCES["ary"]
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        rows = viewer_rows(client, source)
    by_index = {item["row_idx"]: item for item in rows}
    for row in old:
        current = by_index[row["source_row"]]["row"]
        if current["seg_id"] != row["source_id"] or current["transcription"] != row["reference"]:
            raise ValueError("Prior source mapping differs")
    checks = []
    for row in old[:5]:
        audio, duration, rate, shape = fetch_audio(by_index[row["source_row"]], source["revision"])
        if sha(audio) != row["audio_sha256"]:
            raise ValueError("Prior audio mapping differs")
        checks.append(
            {
                "sample_id": row["sample_id"],
                "source_id": row["source_id"],
                "sha256_match": True,
                "duration": duration,
                "sample_rate": rate,
                "shape": shape,
            }
        )
    (EVIDENCE / "prior-mapping-audit.json").write_text(
        json.dumps(
            {
                "previous_manifest_sha256": sha(old_raw),
                "metadata_records_checked": len(old),
                "audio_checks": checks,
                "scope": "source mapping and bytes, not independent human transcript verification",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    candidates = [
        item for item in rows if eligible(item, excluded_ids, excluded_groups, excluded_references)
    ]
    candidates.sort(
        key=lambda item: sha(
            f"project28-darija-specialists-v1|{source['revision']}|{item['row_idx']}".encode()
        )
    )
    if len(candidates) < COUNT:
        raise ValueError("Insufficient disjoint candidates")
    # Freeze ranked selection before any baseline/specialist inference.
    (ROOT / "selection.json").write_text(
        json.dumps(
            {
                "seed": "project28-darija-specialists-v1",
                "source_revision": source["revision"],
                "ranked_rows": [item["row_idx"] for item in candidates],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    records = []
    transfer = 0
    rejected_audio_duplicates = 0
    seen_audio = set(excluded_audio)
    seen_references = set(excluded_references)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        # Only fetch a small surplus, never all candidates or the full dataset.
        selected = candidates[: COUNT + 12]
        for item, payload in zip(
            selected, pool.map(lambda item: fetch_audio(item, source["revision"]), selected)
        ):
            audio, duration, rate, shape = payload
            transfer += len(audio)
            if transfer > 128 * 1024 * 1024:
                raise ValueError("Intake transfer budget exceeded")
            audio_hash = sha(audio)
            ref = item["row"]["transcription"]
            ref_hash = sha(ref.encode())
            if audio_hash in seen_audio or ref_hash in seen_references:
                rejected_audio_duplicates += 1
                continue
            index = len(records)
            filename = f"ary-fresh-{index:03}.wav"
            (ROOT / filename).write_bytes(audio)
            records.append(
                {
                    "sample_id": f"ary-fresh-{index:03}",
                    "language": "ary",
                    "filename": filename,
                    "audio_sha256": audio_hash,
                    "reference": ref,
                    "reference_sha256": ref_hash,
                    "duration_seconds": duration,
                    "source_row": item["row_idx"],
                    "source_id": item["row"]["seg_id"],
                    "source_group": prefix(item["row"]["seg_id"]),
                    "original_sample_rate": rate,
                    "original_shape": shape,
                }
            )
            seen_audio.add(audio_hash)
            seen_references.add(ref_hash)
            if len(records) == COUNT:
                break
    if len(records) != COUNT:
        raise ValueError("Insufficient unique audio after exclusions")
    manifest = {
        "schema_version": "multilingual-asr-v1",
        "purpose": previous["purpose"],
        "reviewed_on": "2026-10-29",
        "retention_until": "2026-11-28",
        "sources": SOURCES,
        "records": records,
        "selection": (
            "hash rank; prior IDs/prefix groups/audio/reference hashes excluded; 100 unique clips"
        ),
        "previous_manifest_sha256": sha(old_raw),
    }
    raw = json.dumps(manifest, ensure_ascii=False, indent=2).encode()
    (ROOT / "manifest.json").write_bytes(raw)
    public = {key: value for key, value in manifest.items() if key != "records"}
    public["sources"] = {"ary": source}
    public.update(
        manifest_sha256=sha(raw),
        excluded_prior_clips=len(old),
        excluded_prior_groups=len(excluded_groups),
        rejected_duplicates=rejected_audio_duplicates,
        source_prefix_groups=len({row["source_group"] for row in records}),
        audio_bytes=sum((ROOT / row["filename"]).stat().st_size for row in records),
        records=[
            {key: value for key, value in row.items() if key not in ("reference", "filename")}
            for row in records
        ],
    )
    (EVIDENCE / "intake.json").write_text(json.dumps(public, indent=2), encoding="utf-8")
    print("Frozen fresh Darija clips", len(records), "manifest", sha(raw), flush=True)


if __name__ == "__main__":
    main()
