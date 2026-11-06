"""Portable replacement for the original Bash source-key guard; never print matched values."""

from __future__ import annotations

import re
from pathlib import Path

PATTERN = re.compile(r"sk-[a-zA-Z0-9]")


def check_source(root: Path) -> list[str]:
    if not root.is_dir():
        raise FileNotFoundError("Expected source directory is missing")
    findings = []
    for path in sorted(root.rglob("*.py")):
        if path.is_symlink():
            raise OSError("Refusing source symlink")
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if PATTERN.search(line):
                findings.append(f"{path.relative_to(root).as_posix()}:{number}")
    return findings


def main() -> None:
    try:
        findings = check_source(Path("src"))
    except (OSError, UnicodeError):
        print("Source key scan could not complete")
        raise SystemExit(2) from None
    for location in findings:
        print(f"Possible API credential at {location}; value omitted")
    raise SystemExit(1 if findings else 0)


if __name__ == "__main__":
    main()
