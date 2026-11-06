"""Map static local Python imports, including nested/type-only edges, without imports."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import TypedDict


class ImportMap(TypedDict):
    modules: dict[str, str]
    dependencies: dict[str, list[str]]
    cycles: list[list[str]]


def map_imports(root: Path) -> ImportMap:
    paths: dict[str, Path] = {}
    for boundary in ("src", "services"):
        for path in (root / boundary).rglob("*.py"):
            parts = list(path.relative_to(root).with_suffix("").parts)
            if parts[-1] == "__init__":
                parts.pop()
            paths[".".join(parts)] = path
    graph: dict[str, list[str]] = {}
    for module, path in sorted(paths.items()):
        found: set[str] = set()
        package = module if path.name == "__init__.py" else module.rpartition(".")[0]
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            candidates: list[str] = []
            if isinstance(node, ast.Import):
                candidates.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    prefix = package.split(".")[: len(package.split(".")) - node.level + 1]
                    base = ".".join([*prefix, *([base] if base else [])])
                candidates.append(base)
                candidates.extend(f"{base}.{alias.name}" for alias in node.names)
            found.update(candidate for candidate in candidates if candidate in paths)
        graph[module] = sorted(found)

    index: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    active: set[str] = set()
    cycles = []

    def visit(module: str) -> None:
        index[module] = low[module] = len(index)
        stack.append(module)
        active.add(module)
        for dependency in graph[module]:
            if dependency not in index:
                visit(dependency)
                low[module] = min(low[module], low[dependency])
            elif dependency in active:
                low[module] = min(low[module], index[dependency])
        if low[module] == index[module]:
            component = []
            while True:
                member = stack.pop()
                active.remove(member)
                component.append(member)
                if member == module:
                    break
            if len(component) > 1 or module in graph[module]:
                cycles.append(sorted(component))

    for module in graph:
        if module not in index:
            visit(module)
    return {
        "modules": {name: path.relative_to(root).as_posix() for name, path in paths.items()},
        "dependencies": graph,
        "cycles": sorted(cycles),
    }


if __name__ == "__main__":
    print(json.dumps(map_imports(Path(__file__).resolve().parents[1]), indent=2))
