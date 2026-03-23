from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class StructuredOutputMode(str, Enum):
    PROVIDER_JSON_SCHEMA = "provider_json_schema"
    PROMPT_JSON = "prompt_json"


class ReviewBackend(str, Enum):
    RULE_ONLY = "rule_only"
    MODEL_ONLY = "model_only"
    MODEL_WITH_FALLBACK = "model_with_fallback"


class ProviderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    base_url: str | None = None
    api_key: str | None = None
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1200, gt=0)
    timeout: float = Field(default=20.0, gt=0.0)
    max_retries: int = Field(default=1, ge=0, le=5)
    retry_backoff_base_ms: int = Field(default=250, ge=0, le=10_000)
    retry_jitter_ms: int = Field(default=150, ge=0, le=10_000)
    prompt_char_budget: int = Field(default=12000, gt=0)
    structured_output_mode: StructuredOutputMode = StructuredOutputMode.PROMPT_JSON


class ReviewLLMConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_backend: ReviewBackend = ReviewBackend.RULE_ONLY
    provider_id: str = Field(default="openai_compatible", min_length=1)
    base_url: str | None = None
    api_key: str | None = None
    model_name: str | None = None
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1200, gt=0)
    timeout: float = Field(default=20.0, gt=0.0)
    max_retries: int = Field(default=1, ge=0, le=5)
    retry_backoff_base_ms: int = Field(default=250, ge=0, le=10_000)
    retry_jitter_ms: int = Field(default=150, ge=0, le=10_000)
    prompt_char_budget: int = Field(default=12000, gt=0)
    structured_output_mode: StructuredOutputMode | None = None
