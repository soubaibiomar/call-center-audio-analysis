import pytest

from scripts.intake_unidata_benchmark import extract_reference


def test_extracts_turn_text_without_changing_content() -> None:
    assert (
        extract_reference("[Agent] [00:00:00]: Hello!\n[Caller] [00:00:03]: Yes.") == "Hello! Yes."
    )


def test_rejects_unknown_or_missing_reference_format() -> None:
    with pytest.raises(ValueError):
        extract_reference("[Agent] [00:00:00]: Hello\nUnparsed continuation")
    with pytest.raises(ValueError):
        extract_reference("")


def test_fixed_reference_removes_only_turn_prefixes() -> None:
    text = "[Caller] [00:01:12]: Oui, c'est exact.\n[Agent] [00:01:15]: Merci!"
    assert extract_reference(text) == "Oui, c'est exact. Merci!"
