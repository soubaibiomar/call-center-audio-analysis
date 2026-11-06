"""LLM provider factory supporting multiple backends.

Supported providers:
- openai: GPT-4o (default, paid)
- gemini: Gemini 2.0 Flash (free tier: 15 RPM, 1500 RPD)
- groq: configured Groq-hosted model
- ollama: cached local Qwen through the OpenAI-compatible endpoint
"""

from __future__ import annotations

import os
import re
from urllib.parse import urlsplit

from langchain_core.language_models.chat_models import BaseChatModel

# Default models per provider
DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "gemini": "gemini-2.0-flash",
    "groq": "llama-3.3-70b-versatile",
    "ollama": "qwen2.5-coder:7b",
}


class LocalModelPolicyError(ValueError):
    """Metadata cannot establish that inference uses local model weights."""


def resolve_model_name(provider: str, model: str | None = None) -> str:
    """One selection rule shared by construction and failure observations."""
    configured = os.environ.get(f"{provider.upper()}_MODEL", "").strip()
    return model or configured or DEFAULT_MODELS.get(provider, "unknown")


def require_local_model(endpoint: str, model: str, timeout: int) -> None:
    """Inspect metadata only; never send a transcript to a remote-backed alias."""
    import httpx

    with httpx.Client(trust_env=False, follow_redirects=False, timeout=min(timeout, 10)) as client:
        response = client.post(endpoint.removesuffix("/v1") + "/api/show", json={"model": model})
        response.raise_for_status()
        metadata = response.json()
    if (
        not isinstance(metadata, dict)
        or metadata.get("remote_model")
        or metadata.get("remote_host")
        or not isinstance(metadata.get("model_info"), dict)
        or not metadata["model_info"]
        or not isinstance(metadata.get("details"), dict)
        or metadata["details"].get("format") != "gguf"
    ):
        raise LocalModelPolicyError("Verified local weights are required for the Ollama provider")


def get_llm(
    provider: str = "openai",
    model: str | None = None,
    timeout: int = 120,
) -> BaseChatModel:
    """Create an LLM client for the given provider.

    Args:
        provider: One of "openai", "gemini", "groq", "ollama"
        model: Explicit model override. Otherwise reads the provider-specific
            environment variable (for example GROQ_MODEL), then uses its default.
        timeout: Request timeout in seconds
    """
    if provider not in DEFAULT_MODELS:
        raise ValueError("Unsupported LLM provider")
    model_name = resolve_model_name(provider, model)

    if provider == "ollama":
        import httpx
        from langchain_openai import ChatOpenAI
        from pydantic import SecretStr

        endpoint = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/")
        parsed = urlsplit(endpoint)
        if (
            parsed.scheme != "http"
            or parsed.hostname
            not in {"localhost", "127.0.0.1", "::1", "ollama", "host.docker.internal"}
            or parsed.path != "/v1"
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Configure a credential-free local Ollama /v1 endpoint")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}", model_name):
            raise ValueError("Invalid local model identifier")
        if isinstance(timeout, bool) or not 0 < timeout <= 600:
            raise ValueError("Local model timeout must be between 0 and 600 seconds")
        require_local_model(endpoint, model_name, timeout)
        return ChatOpenAI(
            model=model_name,
            base_url=endpoint,
            api_key=SecretStr("ollama"),
            timeout=timeout,
            temperature=0,
            max_completion_tokens=2048,
            max_retries=0,
            extra_body={"reasoning_effort": "none"},
            http_client=httpx.Client(trust_env=False, follow_redirects=False),
            http_async_client=httpx.AsyncClient(trust_env=False, follow_redirects=False),
        )

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=model_name, timeout=timeout)

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(model=model_name, timeout=timeout)

    # Default: OpenAI
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=model_name, timeout=timeout)
