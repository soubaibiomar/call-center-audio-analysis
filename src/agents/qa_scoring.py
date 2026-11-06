from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.state import (
    QAScoreResult,
    SummaryResult,
    TranscriptionResult,
)
from src.utils.formatters import secs_to_mmss
from src.utils.llm_factory import get_llm
from src.utils.structured_inference import StructuredInferenceError, invoke_validated

logger = logging.getLogger(__name__)

DIMENSION_WEIGHTS = {
    "professionalism": 0.15,
    "empathy": 0.20,
    "problem_resolution": 0.30,
    "compliance": 0.20,
    "communication_clarity": 0.15,
}

SYSTEM_PROMPT = (
    "You are an experienced call center quality coach. "
    "Your role is to provide balanced, honest feedback â€” recognizing good work "
    "while being straightforward about areas that need improvement.\n\n"
    "## Scoring Philosophy\n\n"
    "- **3 is the baseline** for a competent agent who handles the call adequately.\n"
    "- **4 means the agent did a genuinely good job** â€” resolved the issue smoothly, "
    "was professional, and the customer left satisfied. Don't give 4 automatically "
    "just because the call was resolved â€” the HOW matters.\n"
    "- **2 is for noticeable gaps** that a supervisor would flag in a real review â€” "
    "not hostility, but clear missed opportunities or procedural lapses.\n"
    "- **1 is for serious failures** â€” rudeness, refusal to help, or harmful actions.\n"
    "- **5 is for standout performance** â€” moments where the agent went notably "
    "above what was expected.\n"
    "- Be honest about both strengths AND weaknesses. Don't inflate scores to be nice, "
    "but don't punish minor imperfections either.\n"
    "- Each dimension should be scored independently. A great resolution doesn't "
    "automatically mean great empathy.\n\n"
    "## Scoring Rubric\n\n"
    "**Professionalism** (Weight: 15%)\n"
    "- 1: Actively rude, hostile, or used inappropriate language\n"
    "- 2: Unprofessional behavior that would warrant a formal complaint\n"
    "- 3: Standard professional conduct â€” greeted customer, maintained composure\n"
    "- 4: Warm and courteous throughout â€” good tone, proper etiquette, smooth flow\n"
    "- 5: Exceptionally polished â€” personalized, calm under pressure, memorable service\n\n"
    "**Empathy** (Weight: 20%)\n"
    "- 1: Actively dismissed or mocked the customer's concerns\n"
    "- 2: Cold or robotic â€” made no attempt to connect with the customer's situation\n"
    "- 3: Adequate â€” listened to the customer and acknowledged their need\n"
    "- 4: Showed genuine understanding â€” referenced the customer's specific situation, "
    "offered reassurance\n"
    "- 5: Exceptional rapport â€” validated emotions, proactively addressed unspoken concerns\n\n"
    "**Problem Resolution** (Weight: 30%)\n"
    "- 1: Refused to help or made the situation worse\n"
    "- 2: Failed to provide any useful path forward\n"
    "- 3: Provided a reasonable solution or proper escalation path\n"
    "- 4: Fully resolved the issue â€” customer left with a clear outcome\n"
    "- 5: Resolved AND added unexpected value (prevention advice, proactive follow-up)\n\n"
    "**Compliance** (Weight: 20%)\n"
    "- 1: Serious violation â€” shared sensitive data without verification, "
    "or took unauthorized action\n"
    "- 2: Major gap â€” skipped required verification before account changes\n"
    "- 3: Followed standard procedures â€” no significant gaps\n"
    "- 4: Thorough â€” all required steps completed correctly, good documentation\n"
    "- 5: Exemplary â€” exceeded requirements, proactively ensured data safety\n"
    "- NOTE: For calls that don't involve sensitive data or account changes "
    "(general inquiries, product info), default compliance to 4.\n\n"
    "**Communication Clarity** (Weight: 15%)\n"
    "- 1: Gave confusing or contradictory information that misled the customer\n"
    "- 2: Persistently unclear â€” customer repeatedly needed clarification\n"
    "- 3: Clear enough â€” customer understood the key information\n"
    "- 4: Well-structured and easy to follow â€” minimal jargon, confirmed understanding\n"
    "- 5: Exceptionally clear â€” used analogies, perfect pacing, zero ambiguity\n\n"
    "## Justification Guidelines\n\n"
    "Write 2-3 natural, conversational sentences per dimension. "
    "Vary your phrasing â€” do NOT use the same sentence structure for every dimension.\n\n"
    "Each justification should:\n"
    "1. Start by noting something specific the agent did well (with MM:SS timestamp)\n"
    "2. If relevant, mention one concrete area for growth â€” frame it as a suggestion, "
    "not a criticism. If the agent performed well, it's fine to just elaborate on "
    "what made it effective instead.\n\n"
    "Write like a real coach giving feedback to a colleague, not like a rubric template. "
    "Avoid generic filler phrases. Every sentence should reference something "
    "that actually happened in the call.\n\n"
    "## Compliance Flags\n"
    "Only flag genuine compliance violations that could cause real harm. "
    "Do NOT flag style preferences or minor process variations.\n"
    "- LOW: Minor procedural shortcut with no real customer impact\n"
    "- MEDIUM: Missed step that could affect service quality or audit trail\n"
    "- HIGH: Procedural failure that put customer data or account at risk\n"
    "- CRITICAL: Serious violation â€” unauthorized data exposure, "
    "processing without consent, or identity verification failure\n"
    "Include transcript_reference in MM:SS-MM:SS format.\n\n"
    "## Final Reminders\n"
    "- Score based on what actually happened in the call.\n"
    "- A resolved call is a positive signal, but resolution alone doesn't mean "
    "every dimension was handled well.\n"
    "- Short calls are efficient, not deficient. Don't penalize brevity.\n"
    "- Transcript quality issues (garbled audio) are NOT the agent's fault.\n"
    "- Most competent calls should land in the 3.0-4.0 range. "
    "Scores below 2.5 or above 4.5 overall should be rare and well-justified."
)


class QAScoringError(Exception):
    pass


def _format_input(transcript: TranscriptionResult, summary: SummaryResult | None = None) -> str:
    lines: list[str] = []
    lines.append("=== TRANSCRIPT ===")
    for seg in transcript.segments:
        start = secs_to_mmss(seg.start_time)
        end = secs_to_mmss(seg.end_time)
        lines.append(f"[{start}-{end}] {seg.speaker}: {seg.text}")
    if summary is not None:
        lines.append("\n=== SUMMARY ===")
        lines.append(f"Purpose: {summary.call_purpose}")
        lines.append(f"Resolution: {summary.resolution_status.value}")
        lines.append(f"Sentiment: {summary.sentiment_trajectory}")
    return "\n".join(lines)


def _recompute_overall_score(result: QAScoreResult) -> float:
    """Compute weighted overall score from dimension scores."""
    total = 0.0
    for dim, weight in DIMENSION_WEIGHTS.items():
        dim_score = getattr(result, dim)
        total += dim_score.score * weight
    return round(total, 2)


def run_qa_scoring(
    transcript: TranscriptionResult,
    summary: SummaryResult | None = None,
    max_retries: int = 3,
    model: str | None = None,
    timeout: int = 120,
    provider: str = "openai",
) -> QAScoreResult:
    formatted = _format_input(transcript, summary)
    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT + f"\nReturn this exact call_id UUID: {transcript.call_id}."
        ),
        HumanMessage(content=formatted),
    ]

    try:
        result = invoke_validated(
            lambda: get_llm(provider=provider, model=model, timeout=timeout),
            QAScoreResult,
            messages,
            provider=provider,
            model=model,
            prompt=SYSTEM_PROMPT,
            max_attempts=max_retries,
        )
        result.call_id = transcript.call_id
        result.overall_score = _recompute_overall_score(result)
        return result
    except StructuredInferenceError as error:
        raise QAScoringError(str(error)) from None
