"""Reproductions of confirmed STEP11 trust, lifecycle and reporting defects."""

import json
from unittest.mock import patch

import httpx
import pytest
from langchain_openai import ChatOpenAI

from scripts import benchmark_local_llm as benchmark
from src.agents.summarization import SummarizationError, run_summarization
from src.services.model_runs import capture_model_runs
from src.utils.llm_factory import get_llm
from tests.conftest import make_summary, make_transcription


@pytest.mark.parametrize(
    "metadata",
    [
        {"remote_model": "remote-model", "remote_host": "https://ollama.com"},
        {
            "remote_host": "https://remote.example.test",
            "model_info": {"general.architecture": "qwen2"},
        },
        {},
    ],
)
def test_local_adapter_rejects_remote_alias_or_unverifiable_weights(metadata):
    calls = []

    def respond(request):
        calls.append((request.url.path, json.loads(request.content)))
        return httpx.Response(200, json=metadata)

    client = httpx.Client(transport=httpx.MockTransport(respond))
    with patch("httpx.Client", return_value=client), patch("langchain_openai.ChatOpenAI") as sdk:
        with pytest.raises(ValueError, match="local weights"):
            get_llm("ollama", model="innocent-alias")
    assert calls == [("/api/show", {"model": "innocent-alias"})]
    sdk.assert_not_called()
    assert client.is_closed


@pytest.mark.parametrize("successful", [True, False])
def test_agent_releases_owned_sync_http_client(successful):
    def respond(request):
        if not successful:
            return httpx.Response(404, json={"error": "synthetic missing model"})
        return httpx.Response(
            200,
            json={
                "id": "fixture",
                "object": "chat.completion",
                "created": 0,
                "model": "qwen-test",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": make_summary().model_dump_json(),
                        },
                    }
                ],
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(respond))
    llm = ChatOpenAI(model="qwen-test", api_key="fixture", max_retries=0, http_client=client)
    with patch("src.agents.summarization.get_llm", return_value=llm):
        if successful:
            run_summarization(make_transcription(), provider="ollama", max_retries=1)
        else:
            with pytest.raises(SummarizationError):
                run_summarization(make_transcription(), provider="ollama", max_retries=1)
    try:
        assert client.is_closed
    finally:
        client.close()


def test_factory_failure_receipt_uses_selected_environment_model(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "qwen-selected:missing")
    with patch("src.agents.summarization.get_llm", side_effect=ValueError("safe config failure")):
        with capture_model_runs() as runs:
            with pytest.raises(SummarizationError):
                run_summarization(make_transcription(), provider="ollama", max_retries=1)
    assert runs[0].model_id == "qwen-selected:missing"


def test_rejected_model_setting_is_not_echoed_in_receipt(monkeypatch, caplog):
    monkeypatch.setenv("OLLAMA_MODEL", "SYNTHETIC PRIVATE CONTENT")
    with patch("src.agents.summarization.get_llm", side_effect=ValueError("invalid model")):
        with capture_model_runs() as runs:
            with pytest.raises(SummarizationError):
                run_summarization(make_transcription(), provider="ollama", max_retries=1)
    assert runs[0].model_id == "unresolved"
    assert "SYNTHETIC PRIVATE CONTENT" not in caplog.text + runs[0].model_dump_json()


def test_benchmark_returns_failure_exit_and_preserves_receipts(monkeypatch, tmp_path):
    class LocalInventory:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, url):
            body = (
                {
                    "models": [
                        {
                            "name": "qwen-fixture",
                            "digest": "synthetic",
                            "details": {"family": "qwen2"},
                        }
                    ]
                }
                if url.endswith("/api/tags")
                else {"models": []}
            )
            return httpx.Response(200, json=body)

    monkeypatch.setattr(benchmark.httpx, "Client", lambda **kwargs: LocalInventory())
    monkeypatch.setattr(benchmark, "FIXTURES", [("synthetic", "Synthetic fixture")])
    monkeypatch.setattr(
        benchmark, "run_summarization", lambda *a, **k: (_ for _ in ()).throw(ValueError())
    )
    monkeypatch.setattr(
        benchmark, "run_qa_scoring", lambda *a, **k: (_ for _ in ()).throw(ValueError())
    )
    # The test concerns process status/receipts, not GPU sampling.
    monkeypatch.setattr(
        benchmark.subprocess,
        "run",
        lambda *a, **k: type("Sample", (), {"returncode": 0, "stdout": "123\n"})(),
    )
    destination = tmp_path / "result"
    monkeypatch.setattr(
        "sys.argv", ["benchmark", "--output", str(destination), "--models", "qwen-fixture"]
    )
    with pytest.raises(SystemExit) as error:
        benchmark.main()
    assert error.value.code == 1
    results = json.loads((destination / "results.json").read_text())
    assert results["results"][0]["schema_valid_percent"] == 0
