"""Protect legacy, shared-service and future API consumers with synthetic reports."""

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from services.api.analysis import analyze_call
from src.agents.report import compile_report
from src.services import pipeline
from src.services.analysis import AnalysisService
from src.services.contracts import AnalysisError, AnalysisRequest, PipelineResult
from tests.conftest import make_intake_result, make_qa_scores, make_summary, make_transcription


@pytest.fixture
def owned_exports(monkeypatch):
    paths = []
    monkeypatch.setattr(pipeline, "_temp_files", paths)
    yield paths
    for path in paths:
        Path(path).unlink(missing_ok=True)


@pytest.mark.parametrize("consumer", ["legacy", "shared", "api"])
@pytest.mark.parametrize("status", ["completed", "flagged_for_review"])
def test_summary_qa_report_contracts(consumer, status, tmp_path, db_engine, owned_exports) -> None:
    cid = uuid.uuid4()
    summary = make_summary(call_id=cid)
    qa = make_qa_scores(call_id=cid)
    qa.overall_score = 4.3
    report = compile_report(
        make_intake_result(call_id=cid),
        make_transcription(call_id=cid),
        summary,
        qa,
        trace_id="synthetic-compatibility",
    )
    report.status = status
    source = tmp_path / "input.wav"
    source.write_bytes(b"synthetic audio; graph is controlled by this contract fixture")
    workflow = MagicMock()
    workflow.invoke.return_value = {"status": status, "report": report}
    audit = MagicMock()
    service = AnalysisService(workflow, db_engine, audit)
    request = AnalysisRequest(source, "synthetic-caller", "test")
    if consumer == "legacy":
        result = pipeline.process_call(
            source, request.caller_id, "test", workflow, db_engine, audit
        )
        returned = result.report
    elif consumer == "shared":
        result = service.analyze(request)
        assert result.success
        returned = result.report
    else:
        returned = analyze_call(service, request)
    assert returned is report
    assert returned.summary == summary
    assert returned.qa_scores.overall_score == 4.3
    assert returned.status == status
    assert pipeline.PipelineResult is PipelineResult
    workflow.invoke.assert_called_once()
    supplied = workflow.invoke.call_args.args[0]["audio_input"]
    assert supplied.caller_id == request.caller_id
    assert supplied.department == "test"
    json_path = next(path for path in owned_exports if path.endswith(".json"))
    payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
    assert payload["summary"] == json.loads(summary.model_dump_json())
    assert payload["qa_scores"] == json.loads(qa.model_dump_json())
    assert payload["status"] == status
    assert any(Path(path).read_bytes().startswith(b"%PDF-") for path in owned_exports)


@pytest.mark.parametrize("state", [{"status": "failed", "error": "synthetic failure"}, {}])
def test_api_failure_never_returns_a_report(state, tmp_path, db_engine) -> None:
    source = tmp_path / "input.wav"
    source.write_bytes(b"synthetic")
    workflow = MagicMock()
    workflow.invoke.return_value = state
    service = AnalysisService(workflow, db_engine, MagicMock())
    with pytest.raises(AnalysisError):
        analyze_call(service, AnalysisRequest(source))


def test_missing_input_does_not_invoke_workflow(db_engine) -> None:
    workflow = MagicMock()
    result = AnalysisService(workflow, db_engine, MagicMock()).analyze(AnalysisRequest(None))
    assert not result.success
    assert result.error == "No file uploaded."
    assert result.report is None
    workflow.invoke.assert_not_called()


def test_unexpected_legacy_result_is_rejected(monkeypatch, db_engine) -> None:
    monkeypatch.setattr(pipeline, "process_call", lambda *args: object())
    service = AnalysisService(MagicMock(), db_engine, MagicMock())
    with pytest.raises(TypeError, match="unsupported result"):
        service.analyze(AnalysisRequest(None))


def test_service_imports_do_not_bootstrap_runtime(tmp_path) -> None:
    root = Path(__file__).resolve().parents[2]
    code = """
import os, sys
sys.dont_write_bytecode = True
def audit(event, args):
    if event in {'socket.connect', 'sqlite3.connect', 'subprocess.Popen', 'os.mkdir', 'os.remove'}:
        raise RuntimeError('Unexpected runtime setup: ' + event)
    if event == 'open' and args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
        raise RuntimeError('Unexpected write')
sys.addaudithook(audit)
import src.services.contracts
from src.services.analysis import AnalysisService
import services.api.analysis
AnalysisService(object(), object(), object())
for module in ['gradio', 'faster_whisper', 'sqlalchemy', 'src.utils.config', 'src.graph.workflow']:
    assert module not in sys.modules, module
print('Side-effect-free entrypoints verified')
"""
    env = {**os.environ, "PYTHONPATH": str(root), "PYTHONDONTWRITEBYTECODE": "1"}
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert "verified" in completed.stdout
