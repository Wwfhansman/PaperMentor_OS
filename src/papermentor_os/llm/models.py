from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: MessageRole
    content: str = Field(min_length=1)


class LLMUsage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class LLMRuntimeStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_attempts: int = Field(default=0, ge=0)
    retry_count: int = Field(default=0, ge=0)
    retry_sleep_ms: int = Field(default=0, ge=0)
    prompt_char_count: int = Field(default=0, ge=0)
    completion_char_count: int = Field(default=0, ge=0)
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class LLMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    content: str = Field(min_length=1)
    finish_reason: str | None = None
    raw_response: dict[str, Any] | None = None
    usage: LLMUsage | None = None
    runtime_stats: LLMRuntimeStats | None = None


SchemaT = TypeVar("SchemaT", bound=BaseModel)


@dataclass(slots=True)
class StructuredLLMResponse(Generic[SchemaT]):
    raw: LLMResponse
    parsed: SchemaT
