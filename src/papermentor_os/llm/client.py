from __future__ import annotations

import json
import random
import time
from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from papermentor_os.llm.config import ProviderConfig, StructuredOutputMode
from papermentor_os.llm.exceptions import (
    LLMConfigurationError,
    LLMProviderError,
    LLMStructuredOutputError,
)
from papermentor_os.llm.models import LLMMessage, LLMResponse, LLMRuntimeStats, StructuredLLMResponse
from papermentor_os.llm.providers import BaseLLMProvider


SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMClient:
    def __init__(
        self,
        provider: BaseLLMProvider,
        *,
        sleep_fn: Callable[[float], None] | None = None,
        random_fn: Callable[[], float] | None = None,
        cancel_check: Callable[[], bool] | None = None,
        cancelled_error_factory: Callable[[], Exception] | None = None,
    ) -> None:
        self.provider = provider
        self.sleep_fn = sleep_fn or time.sleep
        self.random_fn = random_fn or random.random
        self.cancel_check = cancel_check
        self.cancelled_error_factory = cancelled_error_factory or (
            lambda: RuntimeError("LLM request was cancelled.")
        )

    def supports_json_schema(self) -> bool:
        return self.provider.supports_json_schema()

    def supports_tool_calling(self) -> bool:
        return self.provider.supports_tool_calling()

    def generate(self, messages: list[LLMMessage], config: ProviderConfig) -> LLMResponse:
        budgeted_messages = self._apply_prompt_budget(messages, config.prompt_char_budget)
        prompt_char_count = sum(len(message.content) for message in budgeted_messages)
        last_error: LLMProviderError | None = None
        total_retry_sleep_ms = 0
        for attempt in range(config.max_retries + 1):
            self._raise_if_cancelled()
            try:
                response = self.provider.generate(budgeted_messages, config)
                return response.model_copy(
                    update={
                        "runtime_stats": self._build_runtime_stats(
                            request_attempts=attempt + 1,
                            retry_sleep_ms=total_retry_sleep_ms,
                            prompt_char_count=prompt_char_count,
                            response=response,
                        )
                    }
                )
            except LLMProviderError as error:
                last_error = LLMProviderError(
                    str(error),
                    runtime_stats=self._build_runtime_stats(
                        request_attempts=attempt + 1,
                        retry_sleep_ms=total_retry_sleep_ms,
                        prompt_char_count=prompt_char_count,
                    ),
                    category=error.category,
                    retryable=error.retryable,
                    status_code=error.status_code,
                )
                if attempt == config.max_retries or not error.retryable:
                    break
                retry_delay_ms = self._compute_retry_delay_ms(config=config, attempt=attempt)
                if retry_delay_ms > 0:
                    self._sleep_with_cancel(retry_delay_ms / 1000)
                    total_retry_sleep_ms += retry_delay_ms
        if last_error is None:
            raise LLMProviderError(
                "LLM request failed without an explicit provider error.",
                category="provider_runtime",
            )
        raise last_error

    def generate_structured(
        self,
        messages: list[LLMMessage],
        schema: type[SchemaT],
        config: ProviderConfig,
    ) -> StructuredLLMResponse[SchemaT]:
        if (
            config.structured_output_mode == StructuredOutputMode.PROVIDER_JSON_SCHEMA
            and self.provider.supports_json_schema()
        ):
            budgeted_messages = self._apply_prompt_budget(messages, config.prompt_char_budget)
            raw_response = self._generate_structured_with_provider(
                budgeted_messages,
                schema,
                config,
            )
        else:
            if config.structured_output_mode == StructuredOutputMode.PROVIDER_JSON_SCHEMA:
                raise LLMConfigurationError(
                    "Provider JSON schema mode requested, but provider does not support it."
                )
            prompt_messages = self._apply_prompt_budget(
                [
                LLMMessage(
                    role="system",
                    content=self._build_prompt_json_instruction(schema),
                ),
                *messages,
                ],
                config.prompt_char_budget,
                preserve_prefix_count=1,
            )
            raw_response = self.generate(prompt_messages, config)

        parsed = self._parse_structured_response(raw_response, schema)
        return StructuredLLMResponse(raw=raw_response, parsed=parsed)

    def _generate_structured_with_provider(
        self,
        messages: list[LLMMessage],
        schema: type[SchemaT],
        config: ProviderConfig,
    ) -> LLMResponse:
        prompt_char_count = sum(len(message.content) for message in messages)
        last_error: LLMProviderError | None = None
        total_retry_sleep_ms = 0
        for attempt in range(config.max_retries + 1):
            self._raise_if_cancelled()
            try:
                response = self.provider.generate_structured(messages, schema, config)
                return response.model_copy(
                    update={
                        "runtime_stats": self._build_runtime_stats(
                            request_attempts=attempt + 1,
                            retry_sleep_ms=total_retry_sleep_ms,
                            prompt_char_count=prompt_char_count,
                            response=response,
                        )
                    }
                )
            except LLMProviderError as error:
                last_error = LLMProviderError(
                    str(error),
                    runtime_stats=self._build_runtime_stats(
                        request_attempts=attempt + 1,
                        retry_sleep_ms=total_retry_sleep_ms,
                        prompt_char_count=prompt_char_count,
                    ),
                    category=error.category,
                    retryable=error.retryable,
                    status_code=error.status_code,
                )
                if attempt == config.max_retries or not error.retryable:
                    break
                retry_delay_ms = self._compute_retry_delay_ms(config=config, attempt=attempt)
                if retry_delay_ms > 0:
                    self._sleep_with_cancel(retry_delay_ms / 1000)
                    total_retry_sleep_ms += retry_delay_ms
        if last_error is None:
            raise LLMProviderError(
                "Structured LLM request failed without an explicit provider error.",
                category="provider_runtime",
            )
        raise last_error

    def _apply_prompt_budget(
        self,
        messages: list[LLMMessage],
        prompt_char_budget: int,
        *,
        preserve_prefix_count: int = 0,
    ) -> list[LLMMessage]:
        if prompt_char_budget <= 0:
            raise LLMConfigurationError("prompt_char_budget must be greater than zero.")
        if preserve_prefix_count < 0:
            raise LLMConfigurationError("preserve_prefix_count must not be negative.")
        if preserve_prefix_count > len(messages):
            raise LLMConfigurationError("preserve_prefix_count cannot exceed message count.")

        total_chars = sum(len(message.content) for message in messages)
        if total_chars <= prompt_char_budget:
            return messages

        overflow = total_chars - prompt_char_budget
        trimmed_messages = [message.model_copy(deep=True) for message in messages]
        for index in range(len(trimmed_messages) - 1, preserve_prefix_count - 1, -1):
            if overflow <= 0:
                break
            content = trimmed_messages[index].content
            if len(content) <= overflow:
                overflow -= len(content)
                trimmed_messages[index] = trimmed_messages[index].model_copy(update={"content": ""})
                continue

            trimmed_messages[index] = trimmed_messages[index].model_copy(
                update={"content": content[:-overflow]}
            )
            overflow = 0

        if overflow > 0:
            raise LLMConfigurationError(
                "Prompt budget is too small to preserve required request instructions."
            )

        result = [message for message in trimmed_messages if message.content]
        if not result:
            raise LLMConfigurationError("Prompt budget removed all request content.")
        return result

    def _build_prompt_json_instruction(self, schema: type[BaseModel]) -> str:
        schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False, indent=2)
        return (
            "仅输出一个合法 JSON 对象，不要添加解释、前后缀或 Markdown 代码块。"
            f"JSON 必须满足以下 schema:\n{schema_json}"
        )

    def _parse_structured_response(
        self,
        raw_response: LLMResponse,
        schema: type[SchemaT],
    ) -> SchemaT:
        content = raw_response.content
        candidate = content.strip()
        if not candidate:
            raise LLMStructuredOutputError(
                "Structured response was empty.",
                runtime_stats=raw_response.runtime_stats,
                category="structured_output_empty",
            )

        extracted_json = self._extract_json_block(candidate)
        try:
            raw_data = json.loads(extracted_json)
        except json.JSONDecodeError as error:
            raise LLMStructuredOutputError(
                "Structured response was not valid JSON.",
                runtime_stats=raw_response.runtime_stats,
                category="structured_output_invalid_json",
            ) from error

        try:
            return schema.model_validate(raw_data)
        except ValidationError as error:
            raise LLMStructuredOutputError(
                "Structured response did not match schema.",
                runtime_stats=raw_response.runtime_stats,
                category="structured_output_schema_mismatch",
            ) from error

    def _extract_json_block(self, content: str) -> str:
        if content.startswith("```"):
            stripped = content.strip("`")
            first_brace = stripped.find("{")
            if first_brace >= 0:
                content = stripped[first_brace:]

        first_brace = content.find("{")
        if first_brace < 0:
            raise LLMStructuredOutputError(
                "Structured response did not contain a JSON object.",
                category="structured_output_missing_json_object",
            )

        depth = 0
        in_string = False
        escape = False
        for index, char in enumerate(content[first_brace:], start=first_brace):
            if escape:
                escape = False
                continue
            if char == "\\":
                escape = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return content[first_brace : index + 1]

        raise LLMStructuredOutputError(
            "Structured response JSON object was incomplete.",
            category="structured_output_incomplete_json",
        )

    def _compute_retry_delay_ms(self, *, config: ProviderConfig, attempt: int) -> int:
        if config.retry_backoff_base_ms <= 0:
            return 0
        jitter_ms = 0
        if config.retry_jitter_ms > 0:
            jitter_ms = int(self.random_fn() * config.retry_jitter_ms)
        return int(config.retry_backoff_base_ms * (2**attempt)) + jitter_ms

    def _build_runtime_stats(
        self,
        *,
        request_attempts: int,
        retry_sleep_ms: int,
        prompt_char_count: int,
        response: LLMResponse | None = None,
    ) -> LLMRuntimeStats:
        usage = response.usage if response is not None else None
        content = response.content if response is not None else ""
        return LLMRuntimeStats(
            request_attempts=request_attempts,
            retry_count=max(request_attempts - 1, 0),
            retry_sleep_ms=retry_sleep_ms,
            prompt_char_count=prompt_char_count,
            completion_char_count=len(content),
            prompt_tokens=usage.prompt_tokens if usage is not None else None,
            completion_tokens=usage.completion_tokens if usage is not None else None,
            total_tokens=usage.total_tokens if usage is not None else None,
        )

    def _raise_if_cancelled(self) -> None:
        if self.cancel_check is None:
            return
        if self.cancel_check():
            raise self.cancelled_error_factory()

    def _sleep_with_cancel(self, seconds: float) -> None:
        if seconds <= 0:
            return
        if self.cancel_check is None:
            self.sleep_fn(seconds)
            return

        remaining = seconds
        while remaining > 0:
            self._raise_if_cancelled()
            sleep_seconds = min(remaining, 0.05)
            self.sleep_fn(sleep_seconds)
            remaining -= sleep_seconds
        self._raise_if_cancelled()
