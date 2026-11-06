"""Typed observational signals, never statements about a person's mental state."""

from typing import Literal, cast

from pydantic import BaseModel, Field, model_validator

EmotionLabel = Literal["neutral", "happy", "angry", "sad", "Unknown"]

LABELS = ("neutral", "happy", "angry", "sad")
DISCLAIMER = (
    "Experimental acoustic pattern classification, not a person's true feelings. "
    "Probabilities are uncalibrated and must not determine HR or QA scores."
)
MODEL_ID = "superb/wav2vec2-base-superb-er"
REVISION = "441a7599c3b22107314dcbd9166621c5c83f2cc5"


class EmotionTurn(BaseModel):
    start: float = Field(ge=0, allow_inf_nan=False)
    end: float = Field(gt=0, allow_inf_nan=False)
    speaker_id: str | None = None
    overlap: bool = False

    @model_validator(mode="after")
    def ordered(self) -> "EmotionTurn":
        if self.end <= self.start:
            raise ValueError("Turn end must follow start")
        return self


class EmotionSignal(EmotionTurn):
    label: EmotionLabel = "Unknown"
    probabilities: dict[str, float] = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    reason: str | None = None
    calibrated: Literal[False] = False
    model_id: str = MODEL_ID
    model_revision: str = REVISION


class EmotionResult(BaseModel):
    status: Literal["disabled", "completed", "unavailable"]
    signals: list[EmotionSignal] = Field(default_factory=list)
    reason: str | None = None
    disclaimer: str = DISCLAIMER
    language: str = "unknown"
    model_id: str = MODEL_ID
    model_revision: str = REVISION
    cache_policy: str = "Model weights in process; no audio or prediction result cache"


def operational_label(scores: dict[str, float], language: str) -> EmotionLabel:
    """Existing STEP_19 pilot policy; input distribution must already be validated."""
    ranked = sorted(scores, key=lambda name: scores[name], reverse=True)
    if language != "en" or scores[ranked[0]] < 0.7 or scores[ranked[0]] - scores[ranked[1]] < 0.15:
        return "Unknown"
    return cast(EmotionLabel, ranked[0])
