from __future__ import annotations

from enum import Enum
from loguru import logger

from config.settings import settings


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    CLAUDE = "claude"
    OPENAI = "openai"


LLM_FALLBACK_CHAIN: list[LLMProvider] = [
    LLMProvider.CLAUDE,
    LLMProvider.OPENAI,
    LLMProvider.OLLAMA,
]


def resolve_provider() -> LLMProvider:
    if settings.CLAUDE_API_KEY:
        return LLMProvider.CLAUDE
    if settings.OPENAI_API_KEY:
        return LLMProvider.OPENAI
    logger.info("No external API keys set — defaulting to Ollama for report generation.")
    return LLMProvider.OLLAMA


def get_available_providers() -> list[LLMProvider]:
    available: list[LLMProvider] = [LLMProvider.OLLAMA]
    if settings.CLAUDE_API_KEY:
        available.append(LLMProvider.CLAUDE)
    if settings.OPENAI_API_KEY:
        available.append(LLMProvider.OPENAI)
    return available


def resolve_with_fallback(preferred: LLMProvider | None = None) -> LLMProvider:
    if preferred is None:
        preferred = resolve_provider()
    for provider in LLM_FALLBACK_CHAIN:
        if provider == LLMProvider.CLAUDE and settings.CLAUDE_API_KEY:
            return LLMProvider.CLAUDE
        if provider == LLMProvider.OPENAI and settings.OPENAI_API_KEY:
            return LLMProvider.OPENAI
        if provider == LLMProvider.OLLAMA:
            return LLMProvider.OLLAMA
    return LLMProvider.OLLAMA
