"""Exercise real diagnostic subprocess boundaries without Docker or model access."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "Test-Project28Environment.ps1"
PWSH = shutil.which("pwsh")
pytestmark = pytest.mark.skipif(
    sys.platform != "win32" or PWSH is None, reason="Windows and PowerShell 7.2+ are required"
)


def ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def run_check(expression: str) -> dict[str, Any]:
    command = f". {ps_quote(str(SCRIPT))} -LibraryOnly; {expression} | ConvertTo-Json -Depth 5"
    result = subprocess.run(
        [str(PWSH), "-NoLogo", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
        check=True,
    )
    data: dict[str, Any] = json.loads(result.stdout)
    return data


def test_missing_executable_is_explicit() -> None:
    result = run_check("Invoke-ToolCheck project28-definitely-nonexistent-executable")
    assert result["status"] == "MISSING"
    assert result["exit_code"] is None


def test_nonzero_exit_retains_failure_detail() -> None:
    result = run_check(
        f"Invoke-ToolCheck {ps_quote(sys.executable)} "
        "-Arguments @('-c', 'import sys; sys.stderr.write(\"probe failed\"); sys.exit(7)')"
    )
    assert result["status"] == "FAILED"
    assert result["exit_code"] == 7
    assert result["stderr"] == "probe failed"


def test_subprocess_arguments_are_literal() -> None:
    result = run_check(
        f"Invoke-ToolCheck {ps_quote(sys.executable)} "
        "-Arguments @('-c', 'import sys; print(sys.argv[1])', 'space & literal argument')"
    )
    assert result["status"] == "PASS"
    assert result["stdout"] == "space & literal argument"


def test_timeout_is_bounded_and_not_reported_as_success() -> None:
    result = run_check(
        f"Invoke-ToolCheck {ps_quote(sys.executable)} "
        "-Arguments @('-c', 'import time; time.sleep(30)') -TimeoutSeconds 1"
    )
    assert result["status"] == "TIMEOUT"
    assert result["exit_code"] is None
    assert result["elapsed_ms"] < 10000


def test_profile_path_is_redacted_in_captured_output() -> None:
    result = run_check(
        f"Invoke-ToolCheck {ps_quote(sys.executable)} "
        "-Arguments @('-c', 'import os; "
        'print(os.environ.get("USERPROFILE", os.path.expanduser("~")))\')'
    )
    assert result["status"] == "PASS"
    assert result["stdout"] == "<USERPROFILE>"
    assert "<USERPROFILE>" in result["path"]
    assert "<USERPROFILE>" in result["executable"]


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        ("PASS", "PASS", "PASS"),
        ("FAILED", "PASS", "UNVERIFIED"),
        ("PASS", "FAILED", "UNVERIFIED"),
    ],
)
def test_unavailable_service_evidence_is_not_claimed_as_preserved(
    before: str, after: str, expected: str
) -> None:
    result = run_check(
        f"Test-ServiceContinuity -Before @{{status='{before}'; stdout=''}} "
        f"-After @{{status='{after}'; stdout=''}}"
    )
    assert result["status"] == expected


def test_service_restart_is_detected() -> None:
    result = run_check(
        "Test-ServiceContinuity -Before @{status='PASS'; stdout='id|/ollama|image|running|t1|0'} "
        "-After @{status='PASS'; stdout='id|/ollama|image|running|t2|1'}"
    )
    assert result["status"] == "CHANGED"


def test_timeout_includes_output_held_by_an_exited_process_child() -> None:
    program = (
        "import subprocess, sys; "
        "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(3)'], "
        "stdout=sys.stdout, stderr=sys.stderr)"
    )
    result = run_check(
        f"Invoke-ToolCheck {ps_quote(sys.executable)} "
        f"-Arguments @('-c', {ps_quote(program)}) -TimeoutSeconds 1"
    )
    assert result["status"] == "TIMEOUT"
    assert result["exit_code"] is None
    assert result["elapsed_ms"] < 2500
    assert result["output_capture_complete"] is False


def test_empty_docker_inventory_has_explicit_zero_counts() -> None:
    result = run_check(
        "function Invoke-ToolCheck { [pscustomobject]@{status='PASS'; stdout=''; exit_code=0} }; "
        "Get-ServiceSnapshot"
    )
    assert result["status"] == "PASS"
    assert result["container_count"] == 0
    assert result["running_count"] == 0
    assert result["ollama_count"] == 0


def test_unicode_output_survives_the_capture_boundary() -> None:
    program = (
        "import sys; sys.stdout.reconfigure(encoding='utf-8'); "
        "print('\u00e9tat \u2014 \u0645\u0631\u062d\u0628\u0627')"
    )
    result = run_check(
        f"Invoke-ToolCheck {ps_quote(sys.executable)} -Arguments @('-c', {ps_quote(program)})"
    )
    assert result["status"] == "PASS"
    assert result["stdout"] == "\u00e9tat \u2014 \u0645\u0631\u062d\u0628\u0627"
