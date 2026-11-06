from src.graph.analysis_nodes import (
    classify_intent,
    classify_resolution,
    collect_review,
    decide_review,
)
from tests.conftest import make_transcription


def test_evidence_is_timestamped_and_intent_is_not_invented():
    result = collect_review(make_transcription())
    assert result.intent == "unknown"
    assert all(item.end_seconds > item.start_seconds for item in result.evidence)


def test_no_segments_requires_review():
    transcript = make_transcription()
    transcript.segments = []
    result = collect_review(transcript)
    assert result.needs_human_review
    assert "missing_evidence" in result.reasons


def test_supported_intent_resolution_and_unsupported_summary_review():
    transcript = make_transcription()
    transcript.segments[0].text = "Billing. The issue is resolved."
    review = classify_resolution(classify_intent(collect_review(transcript)))
    assert review.intent == "billing" and review.intent_evidence
    assert review.resolution == "resolved" and review.resolution_evidence
    assert decide_review(review, "unresolved", False).needs_human_review
    assert "critical_compliance" in decide_review(review, "resolved", True).reasons


def test_pii_is_redacted_before_analysis_provider_calls(monkeypatch):
    from src.graph import workflow
    from tests.conftest import make_qa_scores, make_summary
    from tests.integration.test_pipeline_end_to_end import _make_test_config

    transcript = make_transcription()
    secret = "person@example.com"
    transcript.full_text = secret
    transcript.segments[0].text = secret
    clean = workflow.pii_redaction_node({"transcription": transcript})
    observed = []

    def summarize(value, **kwargs):
        observed.append(value.model_dump_json())
        return make_summary()

    def score(value, **kwargs):
        observed.append(value.model_dump_json())
        return make_qa_scores()

    monkeypatch.setattr(workflow, "run_summarization", summarize)
    monkeypatch.setattr(workflow, "run_qa_scoring", score)
    workflow.summarize_and_qa_node(clean, _make_test_config())
    assert len(observed) == 2 and all(secret not in value for value in observed)


def test_application_graph_disables_remote_tracing():
    from langsmith.run_helpers import get_tracing_context

    from src.graph.workflow import PrivateWorkflow

    class Graph:
        def invoke(self, value):
            assert get_tracing_context()["enabled"] is False
            return {"status": "completed"}

    assert PrivateWorkflow(Graph()).invoke({})["status"] == "completed"
