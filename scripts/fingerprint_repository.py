"""Archive a clean, complete Project 28 upstream checkout without importing its code."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

UPSTREAM = "https://github.com/ANI-IN/Call-Center-Intelligence-System.git"


def git(repository: Path, *arguments: str) -> bytes:
    """Run a read-only Git query with bounded execution and no shell expansion."""
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        check=True,
        timeout=30,
    )
    return result.stdout


def inspect_python(content: bytes, filename: str) -> dict[str, Any]:
    """Parse imports and declarations without executing upstream startup code."""
    tree = ast.parse(content, filename=filename)
    declarations = []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            declarations.append(
                {
                    "name": node.name,
                    "kind": type(node).__name__,
                    "line": node.lineno,
                    "end_line": node.end_lineno,
                }
            )
        elif isinstance(node, ast.Import | ast.ImportFrom):
            imports.append({"line": node.lineno, "statement": ast.unparse(node)})
    return {
        "path": filename,
        "declarations": sorted(declarations, key=lambda item: item["line"]),
        "imports": sorted(imports, key=lambda item: item["line"]),
    }


def fingerprint(repository: Path, destination: Path) -> dict[str, Any]:
    """Require clean full history; archive committed blobs in a new external directory.

    SHA-256 describes Git blob bytes, not potentially CRLF-converted worktree bytes.
    Failures never delete a partial archive: callers can inspect it before retrying
    with a new destination. No checkout, fetch, reset or application import occurs.
    """
    repository = repository.resolve(strict=True)
    repository = Path(
        git(repository, "rev-parse", "--show-toplevel").decode("utf-8").strip()
    ).resolve(strict=True)
    destination = destination.resolve()
    if destination == repository or repository in destination.parents:
        raise ValueError("Archive destination must be outside the baseline checkout")
    if destination.exists():
        raise FileExistsError("Archive destination already exists; refusing to overwrite")
    if git(repository, "status", "--porcelain=v1", "--untracked-files=all").strip():
        raise ValueError("Baseline checkout must be clean, including untracked files")
    if git(repository, "rev-parse", "--is-shallow-repository").strip() != b"false":
        raise ValueError("Baseline must have complete, non-shallow history")
    remote = git(repository, "remote", "get-url", "origin").decode().strip()
    if remote != UPSTREAM:
        raise ValueError("Origin must match the approved public upstream URL exactly")
    head = git(repository, "rev-parse", "HEAD").decode().strip()
    branch = git(repository, "branch", "--show-current").decode().strip()
    entries = git(repository, "ls-tree", "-r", "-z", "--full-tree", head)
    files = []
    modules = []
    archive: dict[str, bytes] = {}
    for entry in entries.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split()
        if kind != "blob":
            raise ValueError("Submodules require a separate provenance capture")
        path = raw_path.decode("utf-8")
        # Repository paths are exported as JSON/text; never interpreted as output paths.
        content = git(repository, "cat-file", "blob", oid)
        files.append(
            {
                "path": path,
                "mode": mode,
                "git_blob": oid,
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
        if path.endswith(".py") and mode != "120000":
            modules.append(inspect_python(content, path))
        if path in {"LICENSE", "app.py", "README.md"} or path.startswith("src/ui/"):
            if mode != "120000":
                archive[path] = content
    if "LICENSE" not in archive:
        raise ValueError("Upstream license must be present before archiving")
    # Recheck before writing: do not label a concurrently modified checkout clean.
    if (
        git(repository, "rev-parse", "HEAD").decode().strip() != head
        or git(repository, "status", "--porcelain=v1", "--untracked-files=all").strip()
    ):
        raise ValueError("Baseline changed while it was being inspected")
    manifest = {
        "schema_version": 1,
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "remote": remote,
        "branch": branch,
        "head": head,
        "clean": True,
        "shallow": False,
        "tracked_file_count": len(files),
        "src_python_module_count": sum(f["path"].startswith("src/") for f in modules),
        "python_file_count": len(modules),
        "files": files,
    }
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in {"provenance.json": manifest, "python-symbols.json": modules}.items():
        (destination / name).write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    (destination / "tracked-tree.txt").write_text(
        "\n".join(f"{f['mode']} {f['git_blob']} {f['path']}" for f in files) + "\n",
        encoding="utf-8",
    )
    # JSON quotes paths in a single Markdown archive: no traversal or symlink following.
    evidence = [f"# Upstream source evidence\n\nCommit: `{head}`\n"]
    for path, content in sorted(archive.items()):
        evidence.append(f"\n## {json.dumps(path)}\n\n````text\n{content.decode('utf-8')}\n````\n")
    (destination / "source-evidence.md").write_text("".join(evidence), encoding="utf-8")
    (destination / "LICENSE.upstream.txt").write_bytes(archive["LICENSE"])
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    try:
        result = fingerprint(arguments.repository, arguments.destination)
    except (OSError, ValueError, subprocess.SubprocessError, SyntaxError) as error:
        parser.exit(
            1, f"Fingerprint failed ({type(error).__name__}); no baseline files modified.\n"
        )
    print(
        json.dumps(
            {key: result[key] for key in ("head", "tracked_file_count", "src_python_module_count")}
        )
    )


if __name__ == "__main__":
    main()
