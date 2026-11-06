import pytest
from pydantic import ValidationError

from ml.emotion.contracts import LABELS
from ml.evaluation.emotion import EvaluationRow, evaluate, metrics


def row(i, label, **changes):
    scores = {name: 0.1 for name in LABELS}
    scores[label] = 0.7
    values = dict(
        record_id=str(i),
        speaker_key="speaker",
        source_revision="fixture",
        domain="acted",
        language="en",
        noise="clean",
        truth=label,
        probabilities=scores,
        emitted=label,
    )
    values.update(changes)
    return EvaluationRow(**values)


def test_perfect_classifier_and_known_calibration_error():
    result = metrics([row(i, label) for i, label in enumerate(LABELS)])
    assert result["macro_f1"] == 1 and result["operational_macro_f1"] == 1
    assert result["expected_calibration_error"] == pytest.approx(0.3)
    assert result["confusion_matrix"][4] == [0] * 5
    assert result["per_class"]["angry"]["support"] == 1


def test_majority_classifier_imbalance_and_abstention():
    rows = [
        row(i, label, probabilities=dict(neutral=1, happy=0, angry=0, sad=0), emitted="Unknown")
        for i, label in enumerate(LABELS)
    ]
    result = metrics(rows)
    assert result["macro_f1"] == pytest.approx(0.1)
    assert result["expected_calibration_error"] == pytest.approx(0.75)
    assert result["coverage"] == 0 and result["selective_accuracy"] is None
    assert result["operational_macro_f1"] == 0
    assert sum(r[4] for r in result["confusion_matrix"]) == 4


def test_domain_separation_and_missing_slices_are_not_zero_gap():
    result = evaluate([row(0, "neutral"), row(1, "sad", domain="media", language="ary")])
    assert set(result["domains"]) == {"acted", "media"}
    assert not result["real_call_evaluation_available"]
    assert result["domains"]["acted"]["worst_slice_gaps"]["accent"] is None
    assert result["domains"]["media"]["metrics"]["missing_classes"] == ["neutral", "happy", "angry"]


@pytest.mark.parametrize(
    "scores",
    [
        dict(neutral=1),
        dict(neutral=float("nan"), happy=0, angry=0, sad=0),
        dict(neutral=2, happy=0, angry=0, sad=-1),
    ],
)
def test_malformed_distributions_rejected(scores):
    with pytest.raises(ValidationError):
        row(0, "neutral", probabilities=scores)


def test_duplicate_and_empty_evaluation_rejected():
    with pytest.raises(ValueError):
        evaluate([])
    with pytest.raises(ValueError):
        evaluate([row(0, "neutral")] * 2)
    with pytest.raises(ValueError):
        metrics([row(0, "neutral")], bins=0)


def test_noise_gap_and_confidence_one_final_bin():
    good = [
        row(i, label, noise="clean", probabilities={name: float(name == label) for name in LABELS})
        for i, label in enumerate(LABELS)
    ]
    bad = [
        row(
            i,
            label,
            noise="noisy",
            probabilities=dict(neutral=1, happy=0, angry=0, sad=0),
            emitted="neutral",
        )
        for i, label in enumerate(LABELS)
    ]
    result = evaluate(good + bad)["domains"]["acted"]
    assert result["worst_slice_gaps"]["noise"] == pytest.approx(0.9)
    assert metrics(good)["reliability"][0]["bin"] == 9
    assert metrics(good)["expected_calibration_error"] == 0
