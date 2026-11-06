"""Behavioral guards for repairs exposed by the full strict type check."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy.dialects import sqlite
from sqlalchemy.schema import CreateIndex, CreateTable

from src.agents.qa_scoring import QAScoringError, run_qa_scoring
from src.agents.report import persist_report
from src.agents.summarization import SummarizationError, run_summarization
from src.database.connection import session_scope
from src.database.models import Base, CallRecord
from src.security.audit import AuditLogger
from src.services.history import list_calls
from tests.conftest import make_intake_result, make_qa_scores, make_summary, make_transcription


@pytest.mark.parametrize("agent", ["summary", "qa"])
@pytest.mark.parametrize("valid", [True, False])
def test_structured_provider_dictionary_is_validated(agent, valid, monkeypatch):
    transcript = make_transcription()
    model = make_summary() if agent == "summary" else make_qa_scores()
    payload = model.model_dump() if valid else {"call_id": str(transcript.call_id)}
    client = MagicMock()
    client.with_structured_output.return_value = client
    client.invoke.return_value = payload
    module = "summarization" if agent == "summary" else "qa_scoring"
    monkeypatch.setattr(f"src.agents.{module}.get_llm", lambda **kwargs: client)
    run = run_summarization if agent == "summary" else run_qa_scoring
    error = SummarizationError if agent == "summary" else QAScoringError
    if valid:
        result = run(transcript, max_retries=1)
        assert isinstance(result, type(model))
        assert result.call_id == transcript.call_id
        if agent == "qa":
            # All five fixture dimensions are 4; weights total 1, yielding 4.0.
            assert result.overall_score == 4.0
    else:
        with pytest.raises(error, match="Failed after 1 attempts"):
            run(transcript, max_retries=1)
    client.invoke.assert_called_once()


@pytest.mark.parametrize("payload", ["[]", '"text"', "42"])
def test_history_nonobject_json_does_not_break_listing(db_engine, payload):
    with session_scope(db_engine) as session:
        session.add(
            CallRecord(
                call_id="synthetic-malformed-json",
                status="completed",
                audio_filename="synthetic.wav",
                summary_json=payload,
                qa_scores_json=payload,
            )
        )
    rows = list_calls(db_engine)
    assert len(rows) == 1
    assert rows[0]["overall_score"] == "—"
    assert rows[0]["resolution_status"] == "—"


@pytest.mark.parametrize("operation", ["audit", "report"])
def test_missing_database_resource_is_explicit(operation):
    if operation == "audit":
        with pytest.raises(ValueError, match="engine or db_path"):
            AuditLogger()
    else:
        from src.agents.report import compile_report

        intake = make_intake_result()
        report = compile_report(
            intake,
            make_transcription(call_id=intake.call_id),
            make_summary(call_id=intake.call_id),
            make_qa_scores(call_id=intake.call_id),
            "test",
        )
        with pytest.raises(ValueError, match="engine or db_path"):
            persist_report(report)


def test_sqlite_schema_matches_pinned_upstream():
    expected = json.loads(
        (Path(__file__).parents[1] / "fixtures/sqlite-schema-upstream.json").read_text()
    )
    dialect = sqlite.dialect()
    actual = {
        table.name: {
            "table": str(CreateTable(table).compile(dialect=dialect)),
            "indexes": sorted(
                str(CreateIndex(index).compile(dialect=dialect)) for index in table.indexes
            ),
        }
        for table in Base.metadata.sorted_tables
    }
    assert actual == expected["schema"]
