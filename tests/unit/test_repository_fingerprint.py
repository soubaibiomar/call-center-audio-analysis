"""Exercise provenance capture using actual local Git repositories, without network."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "fingerprint_repository.py"
spec = importlib.util.spec_from_file_location("fingerprint_repository", SCRIPT)
assert spec is not None and spec.loader is not None
fingerprinter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fingerprinter)


def run_git(repository: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(repository), *arguments], check=True, capture_output=True)


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    repo = tmp_path / "baseline"
    repo.mkdir()
    run_git(repo, "init", "--initial-branch=main")
    run_git(repo, "config", "core.autocrlf", "false")
    run_git(repo, "remote", "add", "origin", fingerprinter.UPSTREAM)
    (repo / "LICENSE").write_bytes(b"MIT License\nCopyright Test\n")
    (repo / "app.py").write_bytes(b"raise RuntimeError('must never execute')\n")
    (repo / "src").mkdir()
    (repo / "src" / "sample.py").write_bytes(b"def greet():\n    return 'hello'\n")
    run_git(repo, "add", ".")
    run_git(
        repo,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-m",
        "Synthetic fixture",
    )
    return repo


def test_capture_hashes_committed_bytes_and_never_imports_app(repository: Path) -> None:
    output = repository.parent / "archive"
    manifest = fingerprinter.fingerprint(repository, output)
    assert manifest["tracked_file_count"] == 3
    assert manifest["src_python_module_count"] == 1
    assert manifest["clean"] is True and manifest["shallow"] is False
    app = next(f for f in manifest["files"] if f["path"] == "app.py")
    assert (
        app["sha256"] == hashlib.sha256(b"raise RuntimeError('must never execute')\n").hexdigest()
    )
    symbols = json.loads((output / "python-symbols.json").read_text(encoding="utf-8"))
    assert (
        next(f for f in symbols if f["path"] == "src/sample.py")["declarations"][0]["name"]
        == "greet"
    )
    assert "MIT License" in (output / "source-evidence.md").read_text(encoding="utf-8")
    assert (output / "LICENSE.upstream.txt").read_bytes() == b"MIT License\nCopyright Test\n"
    assert fingerprinter.git(repository, "status", "--porcelain=v1") == b""


@pytest.mark.parametrize("tracked", [True, False])
def test_reject_dirty_baseline(repository: Path, tracked: bool) -> None:
    (repository / ("app.py" if tracked else "untracked.txt")).write_text("dirty", encoding="utf-8")
    output = repository.parent / "archive"
    with pytest.raises(ValueError, match="clean"):
        fingerprinter.fingerprint(repository, output)
    assert not output.exists()


def test_preserve_existing_output(repository: Path) -> None:
    output = repository.parent / "archive"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    with pytest.raises(FileExistsError, match="overwrite"):
        fingerprinter.fingerprint(repository, output)
    assert sentinel.read_text(encoding="utf-8") == "preserve"


def test_reject_output_inside_baseline(repository: Path) -> None:
    with pytest.raises(ValueError, match="outside"):
        fingerprinter.fingerprint(repository, repository / "archive")


def test_subdirectory_cannot_bypass_baseline_write_protection(repository: Path) -> None:
    output = repository / "archive"
    with pytest.raises(ValueError, match="outside"):
        fingerprinter.fingerprint(repository / "src", output)
    assert not output.exists()
    assert fingerprinter.git(repository, "status", "--porcelain=v1") == b""


def test_capture_from_subdirectory_uses_complete_repository(repository: Path) -> None:
    output = repository.parent / "archive"
    manifest = fingerprinter.fingerprint(repository / "src", output)
    assert {f["path"] for f in manifest["files"]} == {"LICENSE", "app.py", "src/sample.py"}
    assert fingerprinter.git(repository, "status", "--porcelain=v1") == b""


def test_reject_unapproved_remote_without_exporting_it(repository: Path) -> None:
    run_git(repository, "remote", "set-url", "origin", "https://example.invalid/unapproved.git")
    with pytest.raises(ValueError, match="approved public"):
        fingerprinter.fingerprint(repository, repository.parent / "archive")


def test_reject_shallow_history(repository: Path) -> None:
    (repository / ".git" / "shallow").write_bytes(
        fingerprinter.git(repository, "rev-parse", "HEAD")
    )
    with pytest.raises(ValueError, match="non-shallow"):
        fingerprinter.fingerprint(repository, repository.parent / "archive")


def test_reject_missing_license_before_writing(repository: Path) -> None:
    run_git(repository, "rm", "LICENSE")
    run_git(
        repository,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-m",
        "Remove synthetic license",
    )
    output = repository.parent / "archive"
    with pytest.raises(ValueError, match="license"):
        fingerprinter.fingerprint(repository, output)
    assert not output.exists()
