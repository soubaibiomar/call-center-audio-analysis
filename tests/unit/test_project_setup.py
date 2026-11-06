"""Check non-destructive private configuration and value-free diagnostics."""

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_script(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup = load_script("check_project_setup")
keys = load_script("check_hardcoded_keys")


def test_environment_is_never_overwritten(tmp_path: Path) -> None:
    original = b"private configuration\r\n"
    (tmp_path / ".env").write_bytes(original)
    assert setup.ensure_environment(tmp_path) is False
    assert (tmp_path / ".env").read_bytes() == original


def test_environment_created_from_safe_template(tmp_path: Path) -> None:
    content = b"LLM_PROVIDER=openai\nOPENAI_API_KEY=\n"
    (tmp_path / ".env.project28.example").write_bytes(content)
    assert setup.ensure_environment(tmp_path) is True
    assert (tmp_path / ".env").read_bytes() == content


@pytest.mark.parametrize(
    "value,status", [(None, "MISSING"), ("  ", "MISSING"), ("your-key", "PLACEHOLDER")]
)
def test_missing_and_placeholder_credentials(value: str | None, status: str) -> None:
    assert setup.credential_status(value) == status


def test_diagnostic_does_not_serialize_credential(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_bytes((ROOT / "pyproject.toml").read_bytes())
    payload = "synthetic-value-must-not-be-disclosed"
    result = setup.inspect_setup(tmp_path, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": payload})
    assert result["selected_credential_ready"] is True
    assert payload not in json.dumps(result)
    assert result["credential_validity_tested"] is False


def test_guard_reports_location_without_matched_value(tmp_path: Path) -> None:
    payload = "sk-" + "synthetic-not-real"
    (tmp_path / "sample.py").write_text(f"token = '{payload}'\n", encoding="utf-8")
    findings = keys.check_source(tmp_path)
    assert findings == ["sample.py:1"]
    assert payload not in str(findings)


def test_guard_fails_closed_for_missing_source(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        keys.check_source(tmp_path / "absent")
