"""Exercise real report export with a Windows-compatible default text encoding."""

import builtins
import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock

from src.agents.report import compile_report
from src.services import pipeline
from tests.conftest import make_intake_result, make_qa_scores, make_summary, make_transcription


def test_json_download_is_utf8_on_windows(tmp_path, monkeypatch, db_engine) -> None:
    cid = uuid.uuid4()
    summary = make_summary(call_id=cid)
    summary.call_purpose = "Résumé — العربية \u2011"
    report = compile_report(
        make_intake_result(call_id=cid),
        make_transcription(call_id=cid),
        summary,
        make_qa_scores(call_id=cid),
        trace_id="synthetic",
    )
    source = tmp_path / "input.wav"
    source.write_bytes(b"synthetic workflow fixture")
    workflow = MagicMock()
    workflow.invoke.return_value = {"status": "completed", "report": report}

    def windows_open(path, mode="r", **kwargs):
        if "b" not in mode:
            kwargs.setdefault("encoding", "cp1252")
        return builtins.open(path, mode, **kwargs)

    monkeypatch.setattr(pipeline, "open", windows_open, raising=False)
    result = pipeline.process_call(source, None, None, workflow, db_engine, MagicMock())
    try:
        assert result.success
        exported = json.loads(Path(result.json_path).read_text(encoding="utf-8"))
        assert exported["summary"]["call_purpose"] == summary.call_purpose
        assert Path(result.pdf_path).read_bytes().startswith(b"%PDF-")
    finally:
        for path in (result.json_path, result.pdf_path):
            if path:
                Path(path).unlink(missing_ok=True)
