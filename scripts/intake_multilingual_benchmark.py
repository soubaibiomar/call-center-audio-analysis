"""Bounded, evaluation-only public ASR samples; no model training or redistribution.

Fetch 40 French community-validated Common Voice test clips, 40 FLEURS Arabic
test clips and 40 Casablanca Morocco test clips. Dataset viewer revisions are
checked. Audio and reference text remain in ignored local storage.
"""

import concurrent.futures
import hashlib
import io
import json
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx

ROOT = Path(".local/multilingual-asr-20261029")
EVIDENCE = Path("docs/benchmarks/evidence/multilingual-20261029")
COUNT = 40
SOURCES = {
    "fr": {
        "repo": "fsicoli/common_voice_22_0",
        "revision": "ae911de250fe9375d08e2daa2105b671d659d446",
        "config": "fr",
        "license": "CC0-1.0",
        "domain": "community-validated read speech",
    },
    "ar": {
        "repo": "google/fleurs",
        "revision": "70bb2e84b976b7e960aa89f1c648e09c59f894dd",
        "config": "ar_eg",
        "license": "CC-BY-4.0",
        "domain": "MSA read speech; Egyptian locale",
    },
    "ary": {
        "repo": "UBC-NLP/Casablanca",
        "revision": "8951b1b88e28c1107142ced57967b8d16350951d",
        "config": "Morocco",
        "license": "CC-BY-NC-ND-4.0",
        "domain": "Moroccan Darija broadcast speech",
    },
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def request(client, url, **kwargs):
    for attempt in range(4):
        try:
            response = client.get(url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError:
            if attempt == 3:
                raise
            time.sleep(attempt + 1)


def viewer_rows(client, source):
    rows = []
    total = 1
    while len(rows) < total:
        response = request(
            client,
            "https://datasets-server.huggingface.co/rows",
            params={
                "dataset": source["repo"],
                "config": source["config"],
                "split": "test",
                "offset": len(rows),
                "length": 100,
            },
        )
        if response.headers.get("x-revision") != source["revision"]:
            raise ValueError("Viewer revision differs from pinned source")
        data = response.json()
        total = data["num_rows_total"]
        if total > 3000 or not data["rows"]:
            raise ValueError("Metadata exceeds bounds or missing page")
        rows.extend(data["rows"])
    return rows


def main():
    import soundfile as sf

    from scripts.inventory_commonvoice22_fr import fetch_range, reviewed_clips

    ROOT.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if (ROOT / "manifest.json").exists():
        raise ValueError("Completed intake already exists")
    records = []
    with httpx.Client(follow_redirects=True, timeout=90) as client:
        source = SOURCES["fr"]
        base = f"https://huggingface.co/datasets/{source['repo']}/resolve/{source['revision']}"
        metadata = fetch_range(client, base + "/transcript/fr/test.tsv", 6_000_000)
        archive = fetch_range(client, base + "/audio/fr/test/fr_test_0.tar", 32_000_000)
        # Reuse the project's vote/provenance validator; do not infer independent review.
        clips = reviewed_clips(metadata, archive, COUNT)
        for index, (row, audio) in enumerate(clips):
            samples, rate = sf.read(io.BytesIO(audio), dtype="float32")
            filename = f"fr-{index:03}.mp3"
            (ROOT / filename).write_bytes(audio)
            records.append(
                {
                    "sample_id": f"fr-{index:03}",
                    "language": "fr",
                    "filename": filename,
                    "audio_sha256": sha(audio),
                    "reference": row["sentence"],
                    "reference_sha256": sha(row["sentence"].encode()),
                    "duration_seconds": len(samples) / rate,
                    "source_path": row["path"],
                    "source_id": row["sentence_id"],
                    "speaker_id_sha256": sha(row["client_id"].encode()),
                    "up_votes": int(row["up_votes"]),
                    "down_votes": int(row["down_votes"]),
                }
            )
        print("French reviewed test clips", len(clips), flush=True)
        for language in ("ar", "ary"):
            source = SOURCES[language]
            candidates = []
            for item in viewer_rows(client, source):
                row = item["row"]
                duration = row.get("duration", row.get("num_samples", 0) / 16000)
                if not 2 <= duration <= 20 or len(row["transcription"].split()) < 3:
                    continue
                rank = sha(
                    f"project28-multilingual-v1|{source['revision']}|{source['config']}|{item['row_idx']}".encode()
                )
                candidates.append((rank, item))
            selected = sorted(candidates, key=lambda item: item[0])[:COUNT]
            if len(selected) != COUNT:
                raise ValueError("Insufficient eligible test clips")

            def fetch_audio(pair):
                _, item = pair
                row = item["row"]
                url = row["audio"][0]["src"]
                if (
                    urlsplit(url).hostname != "datasets-server.huggingface.co"
                    or source["revision"] not in urlsplit(url).path
                ):
                    raise ValueError("Unpinned or untrusted audio URL")
                with httpx.Client(timeout=60, follow_redirects=True) as audio_client:
                    with audio_client.stream("GET", url) as response:
                        response.raise_for_status()
                        content = bytearray()
                        for block in response.iter_bytes():
                            content.extend(block)
                            if len(content) > 4 * 1024 * 1024:
                                raise ValueError("Clip exceeds download limit")
                return item, bytes(content)

            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
                for index, (item, audio) in enumerate(pool.map(fetch_audio, selected)):
                    row = item["row"]
                    samples, rate = sf.read(io.BytesIO(audio), dtype="float32")
                    duration = len(samples) / rate
                    if not 2 <= duration <= 20.1:
                        raise ValueError("Decoded duration outside intake bounds")
                    filename = f"{language}-{index:03}.wav"
                    (ROOT / filename).write_bytes(audio)
                    text = row["transcription"]
                    records.append(
                        {
                            "sample_id": f"{language}-{index:03}",
                            "language": language,
                            "filename": filename,
                            "audio_sha256": sha(audio),
                            "reference": text,
                            "reference_sha256": sha(text.encode()),
                            "duration_seconds": duration,
                            "source_row": item["row_idx"],
                            "source_id": row.get("seg_id", row.get("id")),
                        }
                    )
            print(language, "pinned test clips", len(selected), flush=True)
    total_bytes = sum((ROOT / row["filename"]).stat().st_size for row in records)
    manifest = {
        "schema_version": "multilingual-asr-v1",
        "purpose": "local non-commercial evaluation only; no training; no redistribution",
        "reviewed_on": "2026-10-29",
        "retention_until": "2026-11-28",
        "sources": SOURCES,
        "records": records,
        "selection": {
            "fr": (
                "first40 matching published test archive entries within a bounded32MB prefix; "
                "up_votes>=2/down_votes=0"
            ),
            "ar_ary": (
                "SHA256 rank across complete published test metadata; "
                "duration2..20s; >=3 reference words"
            ),
        },
    }
    raw = json.dumps(manifest, ensure_ascii=False, indent=2).encode()
    (ROOT / "manifest.json").write_bytes(raw)
    public = {key: value for key, value in manifest.items() if key != "records"}
    public.update(
        {
            "manifest_sha256": sha(raw),
            "audio_bytes": total_bytes,
            "records": [
                {
                    key: value
                    for key, value in row.items()
                    if key not in ("reference", "filename", "speaker_id_sha256")
                }
                for row in records
            ],
        }
    )
    (EVIDENCE / "intake.json").write_text(json.dumps(public, indent=2), encoding="utf-8")
    print(
        "Intake complete",
        len(records),
        "audio bytes",
        total_bytes,
        "manifest",
        sha(raw),
        flush=True,
    )


if __name__ == "__main__":
    main()
