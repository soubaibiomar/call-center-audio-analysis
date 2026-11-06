"""Controlled public-source intake tests; no network or real recordings."""

import hashlib
import json
import sys
from datetime import date
from unittest.mock import patch

import httpx
import pytest

from scripts import inventory_librispeech_sample
from src.datasets.manifest import Manifest
from src.datasets.split import plan_splits
from tests.conftest import make_wav_bytes


def test_public_intake_stays_pending_and_cannot_be_split(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    destination = tmp_path / "data" / "datasets" / "intake"
    audio = make_wav_bytes(duration_seconds=1)

    def respond(request):
        if request.url.host == "huggingface.co":
            return httpx.Response(200, json={"sha": "a" * 40})
        if request.url.path == "/first-rows":
            split = request.url.params["split"]
            index = {"train.100": 1, "validation": 2, "test": 3}[split]
            return httpx.Response(
                200,
                json={
                    "rows": [
                        {
                            "row": {
                                "speaker_id": index,
                                "chapter_id": index,
                                "id": str(index),
                                "text": "synthetic public reference",
                                "audio": [
                                    {"src": f"https://datasets-server.huggingface.co/audio/{index}"}
                                ],
                            }
                        }
                    ]
                },
            )
        return httpx.Response(200, content=audio)

    client = httpx.Client(transport=httpx.MockTransport(respond))
    monkeypatch.setattr(sys, "argv", ["intake", "--output", str(destination)])
    with patch("httpx.Client", return_value=client):
        inventory_librispeech_sample.main()
    manifest = Manifest.model_validate_json((destination / "manifest.json").read_bytes())
    assert len(manifest.records) == 3
    assert all(r.audio_sha256 == hashlib.sha256(audio).hexdigest() for r in manifest.records)
    assert all(r.rights.status == "pending" and not r.rights.train for r in manifest.records)
    assert all(r.label_status == "unreviewed" for r in manifest.records)
    with pytest.raises(ValueError, match="lacks current"):
        plan_splits(manifest, as_of=date.today(), seed="review")
    index = json.loads((destination / "source-index.json").read_text())
    assert len(index) == 3 and all((destination / item["file"]).exists() for item in index)


def test_public_intake_rejects_output_outside_ignored_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["intake", "--output", str(tmp_path / "unsafe")])
    with pytest.raises(SystemExit) as error:
        inventory_librispeech_sample.main()
    assert error.value.code == 2
    assert not (tmp_path / "unsafe").exists()
