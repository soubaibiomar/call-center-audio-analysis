# ruff: noqa: E402
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langsmith import tracing_context
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

from ml.emotion.contracts import EmotionResult, EmotionTurn
from ml.emotion.service import EmotionService
from services.knowledge.grounding import GroundedPolicyService, PolicyAnswer
from src.agents.diarization import Role
from src.agents.intake import run_intake
from src.agents.qa_scoring import QAScoringError, run_qa_scoring
from src.agents.report import compile_report
from src.agents.summarization import SummarizationError, run_summarization
from src.agents.transcription import run_transcription
from src.graph.analysis_nodes import (
    AnalysisReview,
    classify_intent,
    classify_resolution,
    collect_review,
    decide_review,
)
from src.graph.edges import route_after_intake, route_after_qa, route_after_transcription
from src.graph.state import (
    AudioInput,
    CallReport,
    IntakeResult,
    QAScoreResult,
    SummaryResult,
    TranscriptionResult,
)
from src.security.injection_detector import detect_injection
from src.security.pii_redactor import redact_pii
from src.services.model_runs import ModelRun, capture_model_runs
from src.utils.config import Config


class PipelineState(TypedDict, total=False):
    acoustic_emotion: EmotionResult
    policy_evidence: PolicyAnswer
    audio_input: AudioInput
    channel_roles: dict[int, Role]
    intake: IntakeResult
    transcription: TranscriptionResult
    summary: SummaryResult
    qa_scores: QAScoreResult
    report: CallReport
    model_runs: list[ModelRun]
    analysis_review: AnalysisReview
    error: str
    status: str


def intake_node(state: PipelineState) -> PipelineState:
    t0 = time.time()
    result = run_intake(state["audio_input"])
    logger.info(f"Intake completed in {time.time() - t0:.1f}s")
    return {"intake": result}


def transcription_node(
    state: PipelineState, config: Config, db_engine: Engine | None = None
) -> PipelineState:
    t0 = time.time()
    channel_args = {"channel_roles": state["channel_roles"]} if "channel_roles" in state else {}
    result = run_transcription(
        state["intake"],
        confidence_threshold=config.confidence_threshold,
        halt_ratio=config.low_confidence_halt_ratio,
        model_size=config.whisper_model_size,
        db_engine=db_engine,
        **channel_args,
    )
    logger.info(f"Transcription completed in {time.time() - t0:.1f}s")
    return {"transcription": result}


def injection_check_node(state: PipelineState) -> PipelineState:
    """Check transcript for prompt injection attempts before sending to LLM."""
    transcription = state["transcription"]
    result = detect_injection(transcription.full_text)
    if result.injection_detected:
        return {
            "status": "flagged_for_review",
            "error": (
                f"Prompt injection detected in transcript. "
                f"Patterns: {', '.join(result.matched_patterns)}"
            ),
        }
    return {}


def pii_redaction_node(state: PipelineState) -> PipelineState:
    """Redact PII from transcript text before sending to LLM."""
    transcription = state["transcription"]

    # Redact full text
    full_result = redact_pii(transcription.full_text)
    redacted_full = full_result.redacted_text

    # Redact each segment
    redacted_segments = []
    for seg in transcription.segments:
        seg_result = redact_pii(seg.text)
        redacted_segments.append(seg.model_copy(update={"text": seg_result.redacted_text}))

    redacted_transcription = transcription.model_copy(
        update={"full_text": redacted_full, "segments": redacted_segments}
    )
    return {"transcription": redacted_transcription}


def evidence_node(state: PipelineState) -> PipelineState:
    return {"analysis_review": collect_review(state["transcription"])}


def intent_node(state: PipelineState) -> PipelineState:
    return {"analysis_review": classify_intent(state["analysis_review"])}


def resolution_node(state: PipelineState) -> PipelineState:
    return {"analysis_review": classify_resolution(state["analysis_review"])}


def review_policy_node(state: PipelineState) -> PipelineState:
    if "summary" not in state or "qa_scores" not in state:
        return {}
    return {
        "analysis_review": decide_review(
            state["analysis_review"],
            state["summary"].resolution_status.value,
            any(flag.severity == "critical" for flag in state["qa_scores"].compliance_flags),
        )
    }


def summarize_and_qa_node(state: PipelineState, config: Config) -> PipelineState:
    """Run summarization first, then QA scoring with summary context.

    QA gets better accuracy when it can see the summary (resolution status,
    sentiment). The sequential LLM calls add minimal overhead since both
    are single-call operations and the total is still faster than the
    transcription step.
    """
    t0 = time.time()
    transcript = state["transcription"]
    errors: list[str] = []

    with capture_model_runs() as model_runs:
        # Step 1: Summarization
        summary_result = None
        try:
            summary_result = run_summarization(
                transcript,
                max_retries=config.max_retries_per_node,
                timeout=config.llm_timeout_seconds,
                provider=config.llm_provider,
            )
        except SummarizationError as e:
            errors.append(f"Summarization: {e}")

        # Step 2: QA scoring â€” now with summary context for better accuracy
        qa_result = None
        try:
            qa_result = run_qa_scoring(
                transcript,
                summary=summary_result,  # Pass summary for resolution/sentiment context
                max_retries=config.max_retries_per_node,
                timeout=config.llm_timeout_seconds,
                provider=config.llm_provider,
            )
        except QAScoringError as e:
            errors.append(f"QA Scoring: {e}")

    logger.info(f"Summarization + QA completed in {time.time() - t0:.1f}s")

    if errors or summary_result is None or qa_result is None:
        return {
            "error": "; ".join(errors) or "Analysis produced no result",
            "status": "failed",
            "model_runs": model_runs,
        }

    qa_result.policy_evidence = state.get("policy_evidence")
    return {"summary": summary_result, "qa_scores": qa_result, "model_runs": model_runs}


def report_node(state: PipelineState) -> PipelineState:
    report = compile_report(
        intake=state["intake"],
        transcription=state["transcription"],
        summary=state["summary"],
        qa_scores=state["qa_scores"],
        trace_id="",
        model_runs=state.get("model_runs", []),
    )
    report.analysis_review = state.get("analysis_review")
    report.policy_evidence = state.get("policy_evidence")
    report.acoustic_emotion = state.get("acoustic_emotion")
    return {"report": report, "status": "completed"}


def error_node(state: PipelineState) -> PipelineState:
    """Terminal node for failures. Surfaces the most specific error available.

    Failures originate in different places: intake stores its reason in
    ``intake.validation_error`` (the IntakeResult), while later nodes set
    ``state["error"]`` directly. The earlier shape was lost on the intake
    path, leaving users with a bare "Validation failed" message.
    """
    error = state.get("error")
    if not error:
        intake = state.get("intake")
        if intake is not None and getattr(intake, "validation_error", None):
            error = intake.validation_error
        else:
            error = "Validation failed (no detail captured)"
    logger.warning(f"Pipeline routed to error_step: {error}")
    return {"status": "failed", "error": error or "Validation failed (no detail captured)"}


def supervisor_review_node(state: PipelineState) -> PipelineState:
    report = compile_report(
        intake=state["intake"],
        transcription=state["transcription"],
        summary=state["summary"],
        qa_scores=state["qa_scores"],
        trace_id="",
        model_runs=state.get("model_runs", []),
    )
    report.analysis_review = state.get("analysis_review")
    report.policy_evidence = state.get("policy_evidence")
    report.acoustic_emotion = state.get("acoustic_emotion")
    report.status = "flagged_for_review"
    return {"report": report, "status": "flagged_for_review"}


def policy_evidence_node(
    state: PipelineState, service: GroundedPolicyService | None
) -> PipelineState:
    result = (
        service.answer(state["transcription"].full_text)
        if service
        else PolicyAnswer(status="abstain", reason="Knowledge retrieval not configured")
    )
    return {"policy_evidence": result}


def emotion_node(state: PipelineState, service: EmotionService | None) -> PipelineState:
    if service is None:
        return {"acoustic_emotion": EmotionResult(status="disabled")}
    try:
        turns = [
            EmotionTurn(
                start=seg.start_time,
                end=seg.end_time,
                speaker_id=seg.speaker_id,
                overlap=seg.speaker_overlap,
            )
            for seg in state["transcription"].segments
        ]
        result = service.analyze(
            Path(state["intake"].audio_path).read_bytes(), state["intake"].audio_path, turns
        )
    except Exception:
        result = EmotionResult(status="unavailable", reason="Emotion stage unavailable")
    return {"acoustic_emotion": result}


def build_workflow(
    config: Config,
    db_engine: Engine | None = None,
    knowledge: GroundedPolicyService | None = None,
    emotion: EmotionService | None = None,
) -> StateGraph:
    if not 1 <= config.max_retries_per_node <= 5 or not 0 < config.llm_timeout_seconds <= 600:
        raise ValueError("Analysis requires 1–5 attempts and a timeout within 1–600 seconds")
    workflow = StateGraph(PipelineState)

    # Node names must NOT clash with PipelineState keys
    workflow.add_node("intake_step", intake_node)
    workflow.add_node("transcribe_step", lambda s: transcription_node(s, config, db_engine))
    workflow.add_node("injection_check_step", injection_check_node)
    workflow.add_node("pii_redact_step", pii_redaction_node)
    workflow.add_node("emotion_step", lambda s: emotion_node(s, emotion))
    workflow.add_node("evidence_step", evidence_node)
    workflow.add_node("intent_step", intent_node)
    workflow.add_node("resolution_step", resolution_node)
    workflow.add_node("review_policy_step", review_policy_node)
    workflow.add_node("knowledge_step", lambda s: policy_evidence_node(s, knowledge))
    workflow.add_node("summarize_and_qa_step", lambda s: summarize_and_qa_node(s, config))
    workflow.add_node("report_step", report_node)
    workflow.add_node("error_step", error_node)
    workflow.add_node("supervisor_step", supervisor_review_node)

    # Set entry point
    workflow.set_entry_point("intake_step")

    # Conditional edges
    workflow.add_conditional_edges(
        "intake_step",
        lambda s: route_after_intake(s["intake"]),
        {"transcribe": "transcribe_step", "error": "error_step"},
    )
    workflow.add_conditional_edges(
        "transcribe_step",
        lambda s: route_after_transcription(s["transcription"]),
        {"summarize": "injection_check_step"},
    )
    # Injection check -> PII redaction -> parallel summarization + QA
    workflow.add_conditional_edges(
        "injection_check_step",
        lambda s: "error" if s.get("status") == "flagged_for_review" else "continue",
        {"error": "error_step", "continue": "pii_redact_step"},
    )
    workflow.add_edge("pii_redact_step", "emotion_step")
    workflow.add_edge("emotion_step", "evidence_step")
    workflow.add_edge("evidence_step", "intent_step")
    workflow.add_edge("intent_step", "resolution_step")
    workflow.add_edge("resolution_step", "knowledge_step")
    workflow.add_edge("knowledge_step", "summarize_and_qa_step")
    workflow.add_edge("summarize_and_qa_step", "review_policy_step")
    workflow.add_conditional_edges(
        "review_policy_step",
        lambda s: (
            "error"
            if s.get("status") == "failed" or "qa_scores" not in s
            else "supervisor_review"
            if s["analysis_review"].needs_human_review
            else route_after_qa(s["qa_scores"])
        ),
        {"report": "report_step", "supervisor_review": "supervisor_step", "error": "error_step"},
    )

    # Terminal edges
    workflow.add_edge("report_step", END)
    workflow.add_edge("error_step", END)
    workflow.add_edge("supervisor_step", END)

    return workflow


class PrivateWorkflow:
    """Application boundary prevents raw graph input from reaching remote tracers."""

    def __init__(self, graph: CompiledStateGraph) -> None:
        self.graph = graph

    def invoke(self, input: Any) -> Any:
        with tracing_context(enabled=False):
            return self.graph.invoke(input)


def compile_workflow(
    config: Config,
    db_engine: Engine | None = None,
    knowledge: GroundedPolicyService | None = None,
    emotion: EmotionService | None = None,
) -> PrivateWorkflow:
    workflow = build_workflow(config, db_engine, knowledge, emotion)
    return PrivateWorkflow(workflow.compile())
