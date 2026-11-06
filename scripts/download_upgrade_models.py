"""Explicitly invoked, pinned, resumable benchmark-only model downloads.

Run with the isolated ASR Python runtime, which supplies huggingface_hub/httpx.
No authentication values are logged; no application configuration is changed.
"""

import concurrent.futures
import hashlib
import json
import time
from pathlib import Path

import httpx
from huggingface_hub import HfApi

MODELS = {
    "turbo": (
        "dropbox-dash/faster-whisper-large-v3-turbo",
        "0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf",
    ),
    "qwen17": ("Qwen/Qwen3-ASR-1.7B", "7278e1e70fe206f11671096ffdd38061171dd6e5"),
    "reranker": ("BAAI/bge-reranker-v2-m3", "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"),
    "parakeet": ("nvidia/parakeet-tdt-0.6b-v3", "541d1f99c6b0c3cd0b11a95167540bb8edefd82b"),
    "moulsot": ("atlasia/moulsot.v0.3", "8ae8d752ab4218c84e59a7b2ce69becb30cc6393"),
    "darija-small": (
        "Anass-Srk/fine-tuned-whisper-small-darija",
        "d3c4fd5048c5f182dea49e4af8670037a699cfe6",
    ),
}
ROOT = Path(".local/model-upgrade-20261029")
CHUNK = 4 * 1024 * 1024


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def fetch_range_bytes(client, url, start, end, total):
    """Reject an ignored/mismatched Range before reading its potentially huge body."""
    with client.stream("GET", url, headers={"Range": f"bytes={start}-{end}"}) as response:
        if (
            response.status_code != 206
            or response.headers.get("content-range") != f"bytes {start}-{end}/{total}"
        ):
            raise ValueError("Invalid byte range")
        content = bytearray()
        for block in response.iter_bytes():
            content.extend(block)
            if len(content) > end - start + 1:
                raise ValueError("Oversized byte range")
    if len(content) != end - start + 1:
        raise ValueError("Incomplete byte range")
    return bytes(content)


def download(name, workers=16):
    repo, revision = MODELS[name]
    folder = ROOT / name
    folder.mkdir(parents=True, exist_ok=True)
    info = HfApi().model_info(repo, revision=revision, files_metadata=True)
    receipts = []
    for item in info.siblings:
        file = item.rfilename
        if "/" in file or file.startswith(".") or file.endswith((".nemo", ".gguf")):
            continue
        if name in ("moulsot", "darija-small") and file.endswith((".bin", ".pt", ".pth")):
            # Evaluation uses safetensors; optimizer/training pickles are unnecessary.
            continue
        target = folder / file
        expected = item.lfs.sha256 if item.lfs else None
        if target.exists():
            if target.stat().st_size != item.size or (expected and digest(target) != expected):
                raise ValueError(f"Existing file differs: {name}/{file}")
        else:
            url = f"https://huggingface.co/{repo}/resolve/{revision}/{file}"
            if item.size < CHUNK:
                with httpx.Client(follow_redirects=True, timeout=120) as client:
                    response = client.get(url)
                    response.raise_for_status()
                if len(response.content) != item.size:
                    raise ValueError("Incomplete small file")
                with target.open("xb") as output:
                    output.write(response.content)
            else:
                parts = ROOT / "parts" / name / file
                parts.mkdir(parents=True, exist_ok=True)

                def fetch(index):
                    start = index * CHUNK
                    end = min(item.size, start + CHUNK) - 1
                    part = parts / f"{index:05}.part"
                    if part.exists() and part.stat().st_size == end - start + 1:
                        return
                    for attempt in range(5):
                        try:
                            content = fetch_range_bytes(transfer_client, url, start, end, item.size)
                            part.write_bytes(content)
                            return
                        except (httpx.HTTPError, ValueError):
                            if attempt == 4:
                                raise
                            time.sleep(attempt + 1)

                count = (item.size + CHUNK - 1) // CHUNK
                # HTTPX Client is thread-safe; keep TLS connections alive across parts.
                with httpx.Client(
                    follow_redirects=True,
                    timeout=60,
                    limits=httpx.Limits(
                        max_connections=workers * 2, max_keepalive_connections=workers * 2
                    ),
                ) as transfer_client:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
                        for number, _ in enumerate(pool.map(fetch, range(count)), 1):
                            if number % 100 == 0:
                                print(name, file, number, "/", count, flush=True)
                with target.open("xb") as output:
                    for index in range(count):
                        output.write((parts / f"{index:05}.part").read_bytes())
        actual = digest(target)
        if expected and actual != expected:
            raise ValueError("Weight checksum mismatch")
        receipts.append(
            {"file": file, "size": target.stat().st_size, "sha256": actual, "lfs_sha256": expected}
        )
    (folder / "download-receipt.json").write_text(
        json.dumps({"repo": repo, "revision": revision, "files": receipts}, indent=2),
        encoding="utf-8",
    )
    print(name, "download verified", flush=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="+", choices=list(MODELS))
    parser.add_argument("--workers", type=int, choices=range(1, 33), default=16)
    args = parser.parse_args()
    for name in args.models:
        download(name, workers=args.workers)
