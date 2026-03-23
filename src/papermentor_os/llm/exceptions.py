from __future__ import annotations

from papermentor_os.llm.models import LLMRuntimeStats


class LLMError(Exception):
    """Base exception for the LLM abstraction layer."""

    def __init__(
        self,
        message: str,
        *,
        runtime_stats: LLMRuntimeStats | None = None,
        category: str | None = None,
    ) -> None:
        super().__init__(message)
        self.runtime_stats = runtime_stats
        self.category = category


class LLMConfigurationError(LLMError):
    """Raised when the LLM runtime is misconfigured."""


class LLMProviderError(LLMError):
    """Raised when a provider request fails."""

    def __init__(
        self,
        message: str,
        *,
        runtime_stats: LLMRuntimeStats | None = None,
        category: str | None = None,
        retryable: bool = False,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message, runtime_stats=runtime_stats, category=category)
        self.retryable = retryable
        self.status_code = status_code


class LLMStructuredOutputError(LLMError):
    """Raised when structured output cannot be parsed or validated."""
