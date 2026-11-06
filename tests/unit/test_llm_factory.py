"""Model selection remains explicit and provider-specific without network access."""

from unittest.mock import patch

import pytest

from src.utils.llm_factory import DEFAULT_MODELS, get_llm


@pytest.mark.parametrize(
    "configured,explicit,expected",
    [
        ("openai/gpt-oss-20b", None, "openai/gpt-oss-20b"),
        ("configured-model", "explicit-model", "explicit-model"),
        ("   ", None, DEFAULT_MODELS["groq"]),
    ],
)
def test_groq_model_selection(monkeypatch, configured, explicit, expected) -> None:
    monkeypatch.setenv("GROQ_MODEL", configured)
    monkeypatch.setenv("OPENAI_MODEL", "other-provider-model")
    with patch("langchain_groq.ChatGroq") as constructor:
        assert get_llm("groq", model=explicit, timeout=12) is constructor.return_value
    constructor.assert_called_once_with(model=expected, timeout=12)
