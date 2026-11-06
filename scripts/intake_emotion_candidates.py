"""Bounded evaluation-only public subsets; no training or source redistribution."""

import csv
import hashlib
import io
import json
from pathlib import Path

import requests
from huggingface_hub import HfApi

ROOT = Path(".local/step20-corpora")
ROOT.mkdir(exist_ok=True)
if (ROOT / "manifest.json").exists():
    raise FileExistsError(
        "Existing evaluation snapshot preserved; choose a new reviewed destination"
    )
CREMA_REV = "1658cd342dff90010aa843eaeebd53610a08b1dc"
MDER_REV = "4a9e6b02b78516ac50109cc2816386ac699aff95"
MDER_REPO = "FatimahEmadEldin/Moroccan-Arabic-Multimodal-Emotion-Recognition"
LIMIT = 40 * 1024 * 1024
used = 0
records = []


def fetch(url, limit=3 * 1024 * 1024):
    global used
    with requests.get(url, stream=True, timeout=40) as response:
        response.raise_for_status()
        data = bytearray()
        for block in response.iter_content(65536):
            data.extend(block)
            if len(data) > limit or used + len(data) > LIMIT:
                raise ValueError("Acquisition byte budget exceeded")
    used += len(data)
    return bytes(data)


base = f"https://raw.githubusercontent.com/CheyneyComputerScience/CREMA-D/{CREMA_REV}/"
summary = fetch(base + "processedResults/summaryTable.csv")
(ROOT / "crema-summary.csv").write_bytes(summary)
(ROOT / "crema-license.txt").write_bytes(fetch(base + "LICENSE.txt"))
rows = list(csv.DictReader(io.StringIO(summary.decode())))
map_labels = dict(N="neutral", H="happy", A="angry", S="sad")
for code, label in map_labels.items():
    selected = []
    speakers = set()
    for row in sorted(rows, key=lambda r: r["FileName"]):
        speaker = row["FileName"].split("_")[0]
        if row["VoiceVote"] != code or speaker in speakers:
            continue
        name = row["FileName"] + ".wav"
        pointer = fetch(base + "AudioWAV/" + name).decode()
        expected = pointer.split("oid sha256:")[1].splitlines()[0]
        data = fetch(
            f"https://media.githubusercontent.com/media/CheyneyComputerScience/CREMA-D/{CREMA_REV}/AudioWAV/{name}"
        )
        assert hashlib.sha256(data).hexdigest() == expected
        path = ROOT / name
        path.write_bytes(data)
        records.append(
            dict(
                id="crema-" + name,
                path=name,
                sha256=expected,
                source_revision=CREMA_REV,
                domain="acted",
                language="en",
                accent="unverified",
                truth=label,
                speaker_key="crema-" + speaker,
                label_provenance="source audio-majority VoiceVote",
                source_split="no project training; exploratory evaluation subset",
                license="ODbL-1.0 + DbCL-1.0",
            )
        )
        selected.append(name)
        speakers.add(speaker)
        if len(selected) == 4:
            break
    assert len(selected) == 4

base = f"https://huggingface.co/datasets/{MDER_REPO}/resolve/{MDER_REV}/"
metadata = fetch(base + "metadata.csv")
(ROOT / "mder-metadata.csv").write_bytes(metadata)
(ROOT / "mder-mirror-card.md").write_bytes(fetch(base + "README.md"))
files = {
    s.rfilename: s
    for s in HfApi().dataset_info(MDER_REPO, revision=MDER_REV, files_metadata=True).siblings
}
rows = list(csv.DictReader(io.StringIO(metadata.decode("utf-8-sig"))))
for label in map_labels.values():
    selected = []
    speakers = set()
    for row in sorted(rows, key=lambda r: r["file_name"]):
        if (
            row["emotion"].lower() != label
            or float(row["age"]) < 18
            or not 0.5 <= float(row["duration_s"]) <= 10
        ):
            continue
        if row["speaker_key"] in speakers:
            continue
        name = row["file_name"]
        expected = files[name].lfs.sha256
        data = fetch(base + name)
        assert hashlib.sha256(data).hexdigest() == expected
        local = "mder-" + Path(name).name
        (ROOT / local).write_bytes(data)
        records.append(
            dict(
                id=local,
                path=local,
                sha256=expected,
                source_revision=MDER_REV,
                domain="media",
                language="ary",
                accent="unverified",
                truth=label,
                speaker_key="mder-" + row["speaker_key"],
                label_provenance=(
                    "source published native-annotator majority; not independently reviewed"
                ),
                source_split="metadata.csv; not restricted to mirror test; no project training",
                license="Original Mendeley v1 CC-BY-4.0; mirror defers to original",
            )
        )
        selected.append(local)
        speakers.add(row["speaker_key"])
        if len(selected) == 4:
            break
    assert len(selected) == 4, (label, len(selected))
manifest = dict(
    purpose="local evaluation only; no training",
    retention_review_date="2026-11-28",
    permission_basis=(
        "CREMA-D ODbL/DbCL; original MDER-MA v1 CC BY 4.0; public benchmark review 2026-10-29"
    ),
    sources={
        "crema": "https://github.com/CheyneyComputerScience/CREMA-D",
        "mder_original": "https://data.mendeley.com/datasets/yzsw3ff6rn/1",
        "mder_mirror": MDER_REPO,
    },
    note=(
        "No real-call corpus. Media-source rights/privacy remain limited to stated "
        "source grant; no re-identification or redistribution."
    ),
    records=records,
)
with (ROOT / "manifest.json").open("x", encoding="utf8") as f:
    json.dump(manifest, f, indent=2)
print(
    json.dumps(
        dict(records=len(records), downloaded_bytes=used, manifest=str(ROOT / "manifest.json"))
    )
)
