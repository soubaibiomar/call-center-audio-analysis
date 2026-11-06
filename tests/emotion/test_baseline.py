import io
import wave
from unittest.mock import Mock

import numpy as np
import pytest

from ml.emotion.contracts import EmotionTurn
from ml.emotion.service import EmotionService
from src.graph.workflow import emotion_node


def audio(channels: int = 1, silence: bool = False) -> bytes:
    samples = (
        np.zeros(32000) if silence else 0.1 * np.sin(np.arange(32000) * 2 * np.pi * 220 / 16000)
    )
    frames = np.repeat((samples * 32767).astype("<i2")[:, None], channels, axis=1)
    out = io.BytesIO()
    with wave.open(out, "wb") as f:
        f.setnchannels(channels)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(frames.tobytes())
    return out.getvalue()


SCORES = dict(neutral=0.8, happy=0.1, angry=0.05, sad=0.05)


def test_probabilities_timestamps_and_pilot_label():
    predict = Mock(return_value=SCORES)
    result = EmotionService(predict, language="en").analyze(
        audio(), "a.wav", [EmotionTurn(start=0, end=1, speaker_id="s1")]
    )
    signal = result.signals[0]
    assert result.status == "completed" and signal.label == "neutral"
    assert signal.start == 0 and signal.end == 1 and signal.probabilities == SCORES
    assert signal.confidence == 0.8 and signal.calibrated is False
    assert "HR" in result.disclaimer and signal.model_revision
    assert predict.call_args.args[0].size == 16000


@pytest.mark.parametrize(
    "language,scores",
    [("unknown", SCORES), ("fr", SCORES), ("en", dict(neutral=0.4, happy=0.3, angry=0.2, sad=0.1))],
)
def test_uncertainty_retains_distribution(language, scores):
    result = EmotionService(lambda x: scores, language=language).analyze(
        audio(), "a.wav", [EmotionTurn(start=0, end=1, speaker_id="s1")]
    )
    assert result.signals[0].label == "Unknown"
    assert result.signals[0].probabilities == scores


@pytest.mark.parametrize(
    "turn",
    [
        EmotionTurn(start=0, end=1, overlap=True, speaker_id="s1"),
        EmotionTurn(start=0, end=1),
        EmotionTurn(start=0, end=0.2, speaker_id="s1"),
        EmotionTurn(start=0, end=3, speaker_id="s1"),
    ],
)
def test_unsafe_turn_preserved_without_model_call(turn):
    predict = Mock()
    result = EmotionService(predict).analyze(audio(), "a.wav", [turn])
    predict.assert_not_called()
    assert result.signals[0].label == "Unknown" and result.signals[0].start == turn.start


def test_detects_overlapping_speakers_and_stereo_and_silence():
    predict = Mock()
    service = EmotionService(predict)
    turns = [
        EmotionTurn(start=0, end=1, speaker_id="a"),
        EmotionTurn(start=0.5, end=1.5, speaker_id="b"),
    ]
    assert all(s.label == "Unknown" for s in service.analyze(audio(), "a.wav", turns).signals)
    for data in [audio(channels=2), audio(silence=True)]:
        assert service.analyze(data, "a.wav", turns[:1]).signals[0].label == "Unknown"
    predict.assert_not_called()


@pytest.mark.parametrize(
    "scores", [dict(neutral=1), dict(neutral=float("nan"), happy=0, angry=0, sad=0)]
)
def test_invalid_probabilities_fail_closed(scores):
    result = EmotionService(lambda x: scores).analyze(
        audio(), "a.wav", [EmotionTurn(start=0, end=1, speaker_id="s")]
    )
    assert result.status == "unavailable" and not result.signals


def test_disabled_never_reads_audio():
    assert emotion_node({}, None)["acoustic_emotion"].status == "disabled"


def test_bounds_and_private_error():
    service = EmotionService(Mock(side_effect=RuntimeError("private transcript")))
    assert (
        service.analyze(audio(), "a.wav", [EmotionTurn(start=0, end=1, speaker_id="s")]).reason
        == "Emotion processing failed"
    )
    assert service.analyze(b"bad", "a.wav", []).status == "unavailable"
    assert (
        service.analyze(b"", "a.wav", [EmotionTurn(start=0, end=1)] * 121).status == "unavailable"
    )


def test_model_integrity_rejected_before_optional_runtime_import(tmp_path):
    from ml.emotion.model import Wav2VecEmotion

    (tmp_path / "pytorch_model.bin").write_bytes(b"changed")
    with pytest.raises(ValueError, match="integrity"):
        Wav2VecEmotion(tmp_path)
