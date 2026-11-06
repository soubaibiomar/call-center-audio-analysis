"""Guard the offline benchmark's labels, ranking metrics and normalization."""

from scripts.benchmark_upgrade_asr import normalize
from scripts.benchmark_upgrade_llm_quality import CASES
from scripts.benchmark_upgrade_retrieval import DOCUMENTS, QUERIES, metrics
from scripts.summarize_upgrade_benchmarks import aggregate_asr


def test_normalization_preserves_punctuation_and_canonicalizes_accents():
    assert normalize("  E\u0301TÉ\n  Oui! ") == "été oui!"
    assert normalize("NO refund.") != normalize("NO refund")


def test_missing_relevant_document_does_not_receive_credit():
    assert metrics([0, 2, 3], 1) == {"top1": 0, "recall5": 0, "reciprocal_rank": 0}
    assert metrics([0, 2, 3], 2)["reciprocal_rank"] == 0.5


def test_reranking_cannot_change_candidate_recall():
    rank = [3, 2, 1, 0, 4]
    for relevant in range(6):
        assert metrics(rank, relevant)["recall5"] == metrics(rank[::-1], relevant)["recall5"]


def test_fixed_fixtures_cover_languages_and_valid_document_ids():
    assert len(DOCUMENTS) == len(set(DOCUMENTS)) == 12
    assert len(QUERIES) == 18
    assert {language for language, _, _ in QUERIES} == {"en", "fr", "ar"}
    assert all(0 <= relevant < len(DOCUMENTS) for _, _, relevant in QUERIES)
    assert len(CASES) == 9
    for language in ("en", "fr", "ar"):
        assert {label for lang, _, label in CASES if lang == language} == {
            "resolved",
            "unresolved",
            "escalated",
        }


def test_asr_aggregation_weights_by_reference_words_and_flags_partial_runs():
    report = {
        "observations": [
            {
                "sample": "one",
                "word_errors": 1,
                "reference_words": 2,
                "char_errors": 1,
                "reference_chars": 10,
                "seconds": 1,
                "audio_seconds": 10,
            },
            {
                "sample": "two",
                "word_errors": 1,
                "reference_words": 8,
                "char_errors": 1,
                "reference_chars": 10,
                "seconds": 2,
                "audio_seconds": 10,
            },
        ],
        "repetitions": 2,
        "load_seconds": 5,
        "device": "cpu",
        "precision": "int8",
    }
    result = aggregate_asr(report)
    assert result["wer"] == 0.2
    assert result["rtf"] == 0.15
    assert result["complete"] is False
