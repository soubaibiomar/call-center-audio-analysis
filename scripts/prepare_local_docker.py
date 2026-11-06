"""Create ignored local Compose settings and a password without replacing user files."""

from __future__ import annotations

import secrets
from collections.abc import Callable
from pathlib import Path


def prepare(root: Path, cache: Path) -> list[str]:
    if not cache.is_dir():
        raise FileNotFoundError("Hugging Face cache is missing; no model download attempted")
    private = root / ".local"
    private.mkdir(exist_ok=True)
    created = []
    files: dict[Path, Callable[[], str]] = {
        private / "postgres_password": lambda: secrets.token_urlsafe(32),
        root / ".env.docker": lambda: (
            f"PROJECT28_HF_CACHE_DIR={cache.as_posix()}\n"
            "PROJECT28_APP_PORT=7861\nPROJECT28_POSTGRES_PORT=5433\n"
        ),
    }
    for path, content in files.items():
        try:
            with path.open("x", encoding="utf-8") as output:
                output.write(content())
        except FileExistsError:
            continue
        created.append(path.relative_to(root).as_posix())
    return created


if __name__ == "__main__":
    workspace = Path(__file__).resolve().parents[1]
    prepare(workspace, Path.home() / ".cache" / "huggingface" / "hub")
    print("Local Docker settings ready; existing files preserved and secret values omitted.")
