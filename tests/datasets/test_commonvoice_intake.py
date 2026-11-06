"""Check that public intake selects only source-reviewed and bounded material."""

import io
import tarfile

import httpx
import pytest

from scripts.inventory_commonvoice22_fr import fetch_range, reviewed_clips


def test_selects_only_reviewed_matching_clips() -> None:
    header = "path\tclient_id\tsentence_id\tsentence\tup_votes\tdown_votes\tlocale\n"
    rows = "".join(
        f"{name}.mp3\tspeaker-{name}\tsentence-{name}\tHello\t{votes}\t{down}\tfr\n"
        for name, votes, down in [("a", 2, 0), ("b", 3, 0), ("c", 2, 0), ("d", 1, 0), ("e", 2, 1)]
    )
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w") as archive:
        for name in "abcde":
            info = tarfile.TarInfo(f"source/{name}.mp3")
            info.size = 1
            archive.addfile(info, io.BytesIO(b"x"))
    clips = reviewed_clips((header + rows).encode(), output.getvalue())
    assert [row["path"] for row, _ in clips] == ["a.mp3", "b.mp3", "c.mp3"]
    with pytest.raises(ValueError, match="Insufficient"):
        reviewed_clips((header + rows).encode(), output.getvalue(), count=4)


def test_rejects_server_ignoring_range() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b"x"))
    )
    with client, pytest.raises(ValueError, match="bounded range"):
        fetch_range(client, "https://example.org/test", 10)
