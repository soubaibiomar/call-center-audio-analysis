import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ml.emotion.contracts import EmotionResult, EmotionSignal
from ml.emotion.service import EmotionService
from src.graph.state import (
    AudioInput,
    QADimensionScore,
    QAScoreResult,
    ResolutionStatus,
    SummaryResult,
)
from src.graph.workflow import compile_workflow
from src.utils.config import Config
from tests.conftest import make_wav_bytes


def _make_test_config() -> Config:
    return Config(
        openai_api_key="",
        langchain_api_key="",
        langchain_project="test",
        db_encryption_key="",
        db_path=Path("test.db"),
        llm_provider="openai",
        max_cost_per_call_usd=2.0,
        max_retries_per_node=3,
        llm_timeout_seconds=30,
        whisper_model_size="base",
        confidence_threshold=0.6,
        low_confidence_halt_ratio=0.4,
    )


@pytest.mark.integration
class TestPipelineEndToEnd:
    @pytest.mark.parametrize("emotion_enabled", [False, True])
    @patch("src.agents.qa_scoring.get_llm")
    @patch("src.agents.summarization.get_llm")
    @patch("src.agents.transcription._get_whisper_model")
    def test_full_pipeline_happy_path(
        self,
        mock_get_model: MagicMock,
        mock_summary_llm: MagicMock,
        mock_qa_llm: MagicMock,
        emotion_enabled: bool,
    ) -> None:
        # Mock faster-whisper model
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model

        seg1 = MagicMock()
        seg1.text = "Hello."
        seg1.start = 0.0
        seg1.end = 1.0
        seg1.avg_logprob = -0.1
        seg1.no_speech_prob = 0.05
        seg2 = MagicMock()
        seg2.text = "I need help with billing. The issue is resolved."
        seg2.start = 1.0
        seg2.end = 3.0
        seg2.avg_logprob = -0.15
        seg2.no_speech_prob = 0.05
        mock_info = MagicMock()
        mock_model.transcribe.return_value = (
            iter([seg1, seg2]),
            mock_info,
        )

        # Mock summarization LLM (get_llm returns the LLM directly)
        mock_sum = MagicMock()
        mock_summary_llm.return_value = mock_sum
        mock_sum.with_structured_output.return_value = mock_sum
        mock_sum.invoke.return_value = SummaryResult(
            call_id=uuid.uuid4(),
            call_purpose="Customer needs billing help.",
            key_discussion_points=["Billing"],
            action_items=[],
            resolution_status=ResolutionStatus.RESOLVED,
            sentiment_trajectory="Neutral -> Satisfied",
            entities=[],
        )

        # Mock QA LLM
        mock_qa = MagicMock()
        mock_qa_llm.return_value = mock_qa
        mock_qa.with_structured_output.return_value = mock_qa
        mock_qa.invoke.return_value = QAScoreResult(
            call_id=uuid.uuid4(),
            professionalism=QADimensionScore(score=4, justification="Good greeting."),
            empathy=QADimensionScore(score=4, justification="Acknowledged."),
            problem_resolution=QADimensionScore(score=4, justification="Resolved."),
            compliance=QADimensionScore(score=4, justification="OK."),
            communication_clarity=QADimensionScore(score=4, justification="Clear."),
            overall_score=4.0,
            compliance_flags=[],
        )

        config = _make_test_config()
        emotion = MagicMock(spec=EmotionService) if emotion_enabled else None
        if emotion is not None:
            emotion.analyze.return_value = EmotionResult(
                status="completed",
                signals=[
                    EmotionSignal(
                        start=0,
                        end=1,
                        speaker_id="fixture",
                        label="angry",
                        probabilities={"neutral": 0.01, "happy": 0.01, "angry": 0.97, "sad": 0.01},
                        confidence=0.97,
                    )
                ],
            )
        app = compile_workflow(config, emotion=emotion)

        audio = AudioInput(audio_data=make_wav_bytes(duration_seconds=1.0), filename="test.wav")
        result = app.invoke({"audio_input": audio})

        assert result["status"] == "completed"
        assert result["report"] is not None
        assert result["report"].qa_scores.overall_score == 4.0
        assert result["report"].qa_scores.compliance.score == 4
        assert result["report"].acoustic_emotion.status == (
            "completed" if emotion_enabled else "disabled"
        )
        if emotion_enabled:
            assert result["report"].acoustic_emotion.signals[0].label == "angry"

    def test_invalid_audio_routes_to_error(self) -> None:
        config = _make_test_config()
        app = compile_workflow(config)

        result = app.invoke(
            {"audio_input": AudioInput(audio_data=b"not audio", filename="bad.ogg")}
        )

        assert result["status"] == "failed"
        # Regression: the actual reason from intake.validation_error must be
        # surfaced to the user, not swallowed into a bare "Validation failed".
        assert result["error"] != "Validation failed"
        assert result["error"], "error message must not be empty"
        assert "Unsupported" in result["error"] or "format" in result["error"].lower()
