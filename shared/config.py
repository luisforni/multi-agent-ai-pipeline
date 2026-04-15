from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    RESEARCHER_MAX_ITER: int = int(os.getenv("RESEARCHER_MAX_ITER", "5"))
    RESEARCHER_VERBOSE: bool = os.getenv("RESEARCHER_VERBOSE", "true").lower() == "true"

    SUMMARIZER_MAX_WORDS: int = int(os.getenv("SUMMARIZER_MAX_WORDS", "500"))
    SUMMARIZER_STYLE: str = os.getenv("SUMMARIZER_STYLE", "bullets")

    CONTENT_FORMAT: str = os.getenv("CONTENT_FORMAT", "blog")
    CONTENT_LANGUAGE: str = os.getenv("CONTENT_LANGUAGE", "en")

    RESEARCHER_URL: str = os.getenv("RESEARCHER_URL", "http://localhost:9001")
    SUMMARIZER_URL: str = os.getenv("SUMMARIZER_URL", "http://localhost:9002")
    CONTENT_GENERATOR_URL: str = os.getenv("CONTENT_GENERATOR_URL", "http://localhost:9003")

    ORCHESTRATOR_PORT: int = int(os.getenv("ORCHESTRATOR_PORT", "9000"))
    RESEARCHER_PORT: int = int(os.getenv("RESEARCHER_PORT", "9001"))
    SUMMARIZER_PORT: int = int(os.getenv("SUMMARIZER_PORT", "9002"))
    CONTENT_GENERATOR_PORT: int = int(os.getenv("CONTENT_GENERATOR_PORT", "9003"))

    _PROVIDER_DEFAULTS: dict[str, str] = {
        "openai": "gpt-4o",
        "anthropic": "claude-opus-4-6",
        "groq": "llama-3.3-70b-versatile",
        "ollama": "llama3.1",
    }

    @classmethod
    def get_model(cls) -> str:
        if cls.LLM_MODEL:
            return cls.LLM_MODEL
        return cls._PROVIDER_DEFAULTS.get(cls.LLM_PROVIDER, "gpt-4o")


settings = Settings()
