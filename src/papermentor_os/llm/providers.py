from __future__ import annotations

import json
import socket
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from typing import Any
from urllib import error, request
from urllib.parse import urlparse

from pydantic import BaseModel

from papermentor_os.llm.config import ProviderConfig
from papermentor_os.llm.exceptions import LLMProviderError
from papermentor_os.llm.models import LLMMessage, LLMResponse, LLMUsage, MessageRole


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, messages: list[LLMMessage], config: ProviderConfig) -> LLMResponse:
        raise NotImplementedError

    def generate_structured(
        self,
        messages: list[LLMMessage],
        schema: type[BaseModel],
        config: ProviderConfig,
    ) -> LLMResponse:
        return self.generate(messages, config)

    def supports_json_schema(self) -> bool:
        return False

    def supports_tool_calling(self) -> bool:
        return False


@dataclass(slots=True)
class FakeProviderRequest:
    messages: list[LLMMessage]
    config: ProviderConfig
    schema_name: str | None = None


class FakeLLMProvider(BaseLLMProvider):
    def __init__(self, responses: list[str | Exception] | None = None) -> None:
        self._responses: deque[str | Exception] = deque(responses or [])
        self.requests: list[FakeProviderRequest] = []

    def queue_response(self, response: str | Exception) -> None:
        self._responses.append(response)

    def generate(self, messages: list[LLMMessage], config: ProviderConfig) -> LLMResponse:
        self.requests.append(FakeProviderRequest(messages=messages, config=config))
        response = self._pop_response()
        return LLMResponse(
            provider_id=config.provider_id,
            model_name=config.model_name,
            content=response,
        )

    def generate_structured(
        self,
        messages: list[LLMMessage],
        schema: type[BaseModel],
        config: ProviderConfig,
    ) -> LLMResponse:
        self.requests.append(
            FakeProviderRequest(messages=messages, config=config, schema_name=schema.__name__)
        )
        response = self._pop_response()
        return LLMResponse(
            provider_id=config.provider_id,
            model_name=config.model_name,
            content=response,
        )

    def _pop_response(self) -> str:
        if not self._responses:
            raise LLMProviderError("FakeLLMProvider has no queued response.")
        response = self._responses.popleft()
        if isinstance(response, Exception):
            if isinstance(response, LLMProviderError):
                raise response
            raise LLMProviderError(str(response)) from response
        return response


class OpenAICompatibleProvider(BaseLLMProvider):
    def supports_json_schema(self) -> bool:
        return True

    def generate(self, messages: list[LLMMessage], config: ProviderConfig) -> LLMResponse:
        if self._prefer_responses_api(config):
            payload = self._base_responses_payload(messages, config)
            return self._post_responses(payload, config)
        payload = self._base_payload(messages, config)
        return self._post_chat_completions(payload, config)

    def generate_structured(
        self,
        messages: list[LLMMessage],
        schema: type[BaseModel],
        config: ProviderConfig,
    ) -> LLMResponse:
        payload = self._base_payload(messages, config)
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": schema.__name__,
                "schema": schema.model_json_schema(),
            },
        }
        return self._post_chat_completions(payload, config)

    def _base_payload(self, messages: list[LLMMessage], config: ProviderConfig) -> dict[str, Any]:
        return {
            "model": config.model_name,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "messages": [message.model_dump(mode="json") for message in messages],
        }

    def _base_responses_payload(
        self,
        messages: list[LLMMessage],
        config: ProviderConfig,
    ) -> dict[str, Any]:
        instructions = "\n\n".join(
            message.content for message in messages if message.role == MessageRole.SYSTEM
        ).strip()
        input_messages = [
            {
                "role": message.role.value,
                "content": [
                    {
                        "type": "input_text",
                        "text": message.content,
                    }
                ],
            }
            for message in messages
            if message.role != MessageRole.SYSTEM
        ]
        if not input_messages:
            input_messages = [
                {
                    "role": MessageRole.USER.value,
                    "content": [
                        {
                            "type": "input_text",
                            "text": instructions or "请根据给定要求完成任务。",
                        }
                    ],
                }
            ]
            instructions = ""

        payload: dict[str, Any] = {
            "model": config.model_name,
            "temperature": config.temperature,
            "max_output_tokens": config.max_tokens,
            "input": input_messages,
        }
        if instructions:
            payload["instructions"] = instructions
        return payload

    def _post_chat_completions(
        self,
        payload: dict[str, Any],
        config: ProviderConfig,
    ) -> LLMResponse:
        if not config.base_url:
            raise LLMProviderError("OpenAICompatibleProvider requires base_url.")

        endpoint = self._build_endpoint(config.base_url, "chat/completions")
        headers = {
            "Content-Type": "application/json",
        }
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"

        raw_body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(endpoint, data=raw_body, headers=headers, method="POST")

        try:
            with request.urlopen(http_request, timeout=config.timeout) as response:
                raw_response = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise self._build_http_error(exc.code, detail) from exc
        except (error.URLError, TimeoutError, socket.timeout) as exc:
            raise self._build_network_error(exc) from exc

        content = self._extract_content(raw_response)
        usage = self._extract_chat_usage(raw_response)
        return LLMResponse(
            provider_id=config.provider_id,
            model_name=raw_response.get("model", config.model_name),
            content=content,
            finish_reason=self._extract_finish_reason(raw_response),
            raw_response=raw_response,
            usage=usage,
        )

    def _post_responses(
        self,
        payload: dict[str, Any],
        config: ProviderConfig,
    ) -> LLMResponse:
        if not config.base_url:
            raise LLMProviderError("OpenAICompatibleProvider requires base_url.")

        endpoint = self._build_endpoint(config.base_url, "responses")
        headers = {
            "Content-Type": "application/json",
        }
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"

        raw_body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(endpoint, data=raw_body, headers=headers, method="POST")

        try:
            with request.urlopen(http_request, timeout=config.timeout) as response:
                raw_response = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise self._build_http_error(exc.code, detail) from exc
        except (error.URLError, TimeoutError, socket.timeout) as exc:
            raise self._build_network_error(exc) from exc

        usage = self._extract_responses_usage(raw_response)
        return LLMResponse(
            provider_id=config.provider_id,
            model_name=raw_response.get("model", config.model_name),
            content=self._extract_responses_content(raw_response),
            finish_reason=self._extract_responses_finish_reason(raw_response),
            raw_response=raw_response,
            usage=usage,
        )

    def _extract_content(self, raw_response: dict[str, Any]) -> str:
        choices = raw_response.get("choices") or []
        if not choices:
            raise LLMProviderError(
                "Provider response did not contain choices.",
                category="invalid_response_shape",
            )

        message = (choices[0] or {}).get("message") or {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content
        if isinstance(content, list):
            parts = [
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            ]
            joined = "".join(parts).strip()
            if joined:
                return joined
        raise LLMProviderError(
            "Provider response did not contain textual content.",
            category="empty_output",
        )

    def _extract_finish_reason(self, raw_response: dict[str, Any]) -> str | None:
        choices = raw_response.get("choices") or []
        if not choices:
            return None
        finish_reason = (choices[0] or {}).get("finish_reason")
        return str(finish_reason) if finish_reason is not None else None

    def _extract_chat_usage(self, raw_response: dict[str, Any]) -> LLMUsage | None:
        usage = raw_response.get("usage") or {}
        if not isinstance(usage, dict):
            return None
        normalized_usage = {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
        }
        if all(value is None for value in normalized_usage.values()):
            return None
        return LLMUsage.model_validate(normalized_usage)

    def _extract_responses_content(self, raw_response: dict[str, Any]) -> str:
        output_text = raw_response.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text

        output_items = raw_response.get("output") or []
        parts: list[str] = []
        for item in output_items:
            if not isinstance(item, dict):
                continue
            for content_item in item.get("content") or []:
                if not isinstance(content_item, dict):
                    continue
                item_type = str(content_item.get("type") or "")
                if item_type not in {"output_text", "text"}:
                    continue
                text_value = content_item.get("text")
                if isinstance(text_value, str) and text_value:
                    parts.append(text_value)
                    continue
                if isinstance(text_value, dict):
                    nested_value = text_value.get("value")
                    if isinstance(nested_value, str) and nested_value:
                        parts.append(nested_value)
        joined = "".join(parts).strip()
        if joined:
            return joined
        raise LLMProviderError(
            "Provider response did not contain textual content.",
            category="empty_output",
        )

    def _build_http_error(self, status_code: int, detail: str) -> LLMProviderError:
        detail_text = detail.strip()
        message = f"Provider HTTP error {status_code}: {detail_text}"
        if status_code == 429:
            return LLMProviderError(
                message,
                category="rate_limit",
                retryable=True,
                status_code=status_code,
            )
        if status_code == 408:
            return LLMProviderError(
                message,
                category="network_timeout",
                retryable=True,
                status_code=status_code,
            )
        if 500 <= status_code <= 599:
            return LLMProviderError(
                message,
                category="server_error",
                retryable=True,
                status_code=status_code,
            )
        if status_code == 404:
            return LLMProviderError(
                message,
                category="endpoint_mismatch",
                status_code=status_code,
            )
        if status_code in {401, 403}:
            return LLMProviderError(
                message,
                category="auth_error",
                status_code=status_code,
            )
        return LLMProviderError(
            message,
            category="provider_http",
            status_code=status_code,
        )

    def _build_network_error(self, exc: Exception) -> LLMProviderError:
        message = str(exc)
        category = "network_timeout" if self._looks_like_timeout(exc, message) else "network_connect"
        return LLMProviderError(
            f"Provider request failed: {message}",
            category=category,
            retryable=True,
        )

    def _looks_like_timeout(self, exc: Exception, message: str) -> bool:
        lowered = message.lower()
        return isinstance(exc, (TimeoutError, socket.timeout)) or "timed out" in lowered

    def _extract_responses_finish_reason(self, raw_response: dict[str, Any]) -> str | None:
        finish_reason = raw_response.get("finish_reason")
        if finish_reason is not None:
            return str(finish_reason)
        status = raw_response.get("status")
        if status is not None:
            return str(status)
        return None

    def _extract_responses_usage(self, raw_response: dict[str, Any]) -> LLMUsage | None:
        usage = raw_response.get("usage") or {}
        if not isinstance(usage, dict):
            return None
        normalized_usage = {
            "prompt_tokens": usage.get("prompt_tokens", usage.get("input_tokens")),
            "completion_tokens": usage.get("completion_tokens", usage.get("output_tokens")),
            "total_tokens": usage.get("total_tokens"),
        }
        if all(value is None for value in normalized_usage.values()):
            return None
        return LLMUsage.model_validate(normalized_usage)

    def _prefer_responses_api(self, config: ProviderConfig) -> bool:
        if not config.base_url:
            return False
        normalized_model_name = (config.model_name or "").strip().lower()
        if normalized_model_name.startswith("deepseek-"):
            return False
        parsed = urlparse(config.base_url)
        hostname = (parsed.hostname or "").lower()
        path = parsed.path.rstrip("/")
        return hostname.endswith("volces.com") or path.endswith("/api/v3") or "/api/v3/" in path

    def _build_endpoint(self, base_url: str, suffix: str) -> str:
        normalized_base = base_url.rstrip("/")
        if normalized_base.endswith(f"/{suffix}"):
            return normalized_base
        return f"{normalized_base}/{suffix}"
