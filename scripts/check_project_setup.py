"""Report pinned dependency and credential readiness without printing secret values."""

from __future__ import annotations

import importlib.metadata
import json
import os
import tomllib
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

PROVIDERS = {"openai": "OPENAI_API_KEY", "gemini": "GOOGLE_API_KEY", "groq": "GROQ_API_KEY"}


def credential_status(value: str | None) -> str:
    if not value or not value.strip():
        return "MISSING"
    if value.strip().lower().startswith(("your-", "placeholder", "changeme")):
        return "PLACEHOLDER"
    return "CONFIGURED_UNVERIFIED"


def ensure_environment(root: Path) -> bool:
    """Create a private local template exclusively; never replace existing configuration."""
    path = root / ".env"
    if path.exists():
        return False
    content = (root / ".env.project28.example").read_bytes()
    with path.open("xb") as output:
        output.write(content)
    return True


def inspect_setup(root: Path, environment: dict[str, str] | None = None) -> dict[str, Any]:
    values = {
        **dotenv_values(root / ".env"),
        **(os.environ if environment is None else environment),
    }
    provider = values.get("LLM_PROVIDER", "openai")
    credentials = {
        key: credential_status(values.get(key))
        for key in [*PROVIDERS.values(), "LANGCHAIN_API_KEY"]
    }
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = (
        project["project"]["dependencies"] + project["project"]["optional-dependencies"]["dev"]
    )
    pins = []
    for specification in dependencies:
        declared_name, expected = specification.split("==", 1)
        name = declared_name.split("[", 1)[0]
        actual: str | None
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual = None
        pins.append(
            {"package": name, "expected": expected, "actual": actual, "match": actual == expected}
        )
    required = PROVIDERS.get(str(provider))
    return {
        "provider": provider if provider in PROVIDERS or provider == "ollama" else "UNRECOGNIZED",
        "provider_supported_upstream": required is not None,
        "credentials": credentials,
        "selected_credential_ready": bool(
            required and credentials[required] == "CONFIGURED_UNVERIFIED"
        ),
        "pins": pins,
        "all_direct_dev_pins_match": all(pin["match"] for pin in pins),
        "model_download_performed": False,
        "credential_validity_tested": False,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    created = ensure_environment(root)
    result = inspect_setup(root)
    result["environment_created"] = created
    print(json.dumps(result, indent=2))
    if not result["all_direct_dev_pins_match"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
