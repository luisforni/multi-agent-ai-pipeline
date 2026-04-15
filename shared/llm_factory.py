from __future__ import annotations

from typing import Any

from shared.config import settings


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    **kwargs: Any,
):
    provider = provider or settings.LLM_PROVIDER
    model = model or settings.get_model()

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=settings.OPENAI_API_KEY or None,
            **kwargs,
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=settings.ANTHROPIC_API_KEY or None,
            **kwargs,
        )

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model,
            temperature=temperature,
            api_key=settings.GROQ_API_KEY or None,
            **kwargs,
        )

    if provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=model,
            temperature=temperature,
            base_url=settings.OLLAMA_BASE_URL,
            **kwargs,
        )

    raise ValueError(
        f"Unknown LLM provider: {provider!r}. "
        "Valid options: openai, anthropic, groq, ollama"
    )


_CREWAI_PREFIX = {
    "openai": "openai",
    "anthropic": "anthropic",
    "groq": "groq",
    "ollama": "ollama",
}


def get_crewai_llm(
    provider: str | None = None,
    model: str | None = None,
) -> str:
    provider = provider or settings.LLM_PROVIDER
    model = model or settings.get_model()
    prefix = _CREWAI_PREFIX.get(provider, provider)
    return f"{prefix}/{model}"
