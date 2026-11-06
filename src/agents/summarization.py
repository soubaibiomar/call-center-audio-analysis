from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.state import SummaryResult, TranscriptionResult
from src.utils.formatters import secs_to_mmss
from src.utils.llm_factory import get_llm
from src.utils.structured_inference import StructuredInferenceError, invoke_validated

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a call center analyst. Analyze the following call "
    "transcript and produce a structured summary.\n\n"
    "## Output Fields\n"
    "- **call_purpose**: 1-2 sentences on why the customer called. "
    "Start with the customer's core need, not the agent's greeting.\n"
    "- **key_discussion_points**: 3-7 bullet points of substantive topics. "
    "Do NOT include greetings, hold music, or pleasantries.\n"
    "- **action_items**: Specific next steps with owner "
    "(agent/customer/system) and deadline if mentioned. "
    "If no action items were discussed, return an empty list.\n"
    "- **resolution_status**: 'resolved' (issue fully addressed), "
    "'unresolved' (issue still open), or 'escalated' (transferred to another team)\n"
    "- **sentiment_trajectory**: How customer sentiment changed "
    "across the call. Use format 'Start -> End' "
    '(e.g., "Frustrated -> Satisfied", "Neutral -> Neutral")\n'
    "- **entities**: Extract product names, account numbers, "
    "dates, monetary amounts, and reference numbers mentioned.\n\n"
    "## Quality Rules\n"
    "- Be factual. Only include information EXPLICITLY stated in the transcript.\n"
    "- Do NOT infer, assume, or hallucinate details.\n"
    "- If parts of the transcript are unclear or garbled, acknowledge "
    "the limitation rather than guessing the content.\n"
    "- For very short calls (<30 seconds), it is acceptable to have "
    "fewer discussion points and entities."
)


class SummarizationError(Exception):
    pass


def _format_transcript(transcript: TranscriptionResult) -> str:
    lines: list[str] = []
    for seg in transcript.segments:
        start = secs_to_mmss(seg.start_time)
        end = secs_to_mmss(seg.end_time)
        lines.append(f"[{start}-{end}] {seg.speaker}: {seg.text}")
    return "\n".join(lines)


def run_summarization(
    transcript: TranscriptionResult,
    max_retries: int = 3,
    model: str | None = None,
    timeout: int = 30,
    provider: str = "openai",
) -> SummaryResult:
    formatted = _format_transcript(transcript)
    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT + f"\nReturn this exact call_id UUID: {transcript.call_id}."
        ),
        HumanMessage(content=f"Transcript:\n\n{formatted}"),
    ]

    try:
        result = invoke_validated(
            lambda: get_llm(provider=provider, model=model, timeout=timeout),
            SummaryResult,
            messages,
            provider=provider,
            model=model,
            prompt=SYSTEM_PROMPT,
            max_attempts=max_retries,
        )
        result.call_id = transcript.call_id
        return result
    except StructuredInferenceError as error:
        raise SummarizationError(str(error)) from None
