import json
from urllib import error

from pydantic import BaseModel, ConfigDict, Field

from papermentor_os.llm import (
    LLMMessage,
    LLMProviderError,
    MessageRole,
    OpenAICompatibleProvider,
    ProviderConfig,
)


class DummyStructuredOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)


class _FakeHTTPResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload, ensure_ascii=False).encode("utf-8")

    def close(self) -> None:
        return None

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def test_openai_compatible_provider_uses_responses_api_for_ark_base_url(monkeypatch) -> None:
    provider = OpenAICompatibleProvider()
    captured: dict[str, object] = {}

    def _fake_urlopen(http_request, timeout):
        captured["url"] = http_request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(http_request.header_items())
        captured["body"] = json.loads(http_request.data.decode("utf-8"))
        return _FakeHTTPResponse(
            {
                "model": "doubao-seed-2-0-lite-260215",
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [
                            {
                                "type": "output_text",
                                "text": '{"summary":"ok"}',
                            }
                        ],
                    }
                ],
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 8,
                    "total_tokens": 20,
                },
            }
        )

    monkeypatch.setattr("papermentor_os.llm.providers.request.urlopen", _fake_urlopen)

    response = provider.generate(
        [
            LLMMessage(role=MessageRole.SYSTEM, content="你是论文评审助手。"),
            LLMMessage(role=MessageRole.USER, content="请输出结构化结论。"),
        ],
        ProviderConfig(
            provider_id="openai_compatible",
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key="sk-test",
            model_name="doubao-seed-2-0-lite-260215",
            timeout=12.0,
        ),
    )

    assert captured["url"] == "https://ark.cn-beijing.volces.com/api/v3/responses"
    assert captured["timeout"] == 12.0
    assert captured["headers"]["Authorization"] == "Bearer sk-test"
    assert captured["body"] == {
        "model": "doubao-seed-2-0-lite-260215",
        "temperature": 0.0,
        "max_output_tokens": 1200,
        "instructions": "你是论文评审助手。",
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "请输出结构化结论。",
                    }
                ],
            }
        ],
    }
    assert response.content == '{"summary":"ok"}'
    assert response.finish_reason == "completed"
    assert response.usage is not None
    assert response.usage.prompt_tokens == 12
    assert response.usage.completion_tokens == 8
    assert response.usage.total_tokens == 20


def test_openai_compatible_provider_uses_chat_completions_for_json_schema(monkeypatch) -> None:
    provider = OpenAICompatibleProvider()
    captured: dict[str, object] = {}

    def _fake_urlopen(http_request, timeout):
        captured["url"] = http_request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(http_request.header_items())
        captured["body"] = json.loads(http_request.data.decode("utf-8"))
        return _FakeHTTPResponse(
            {
                "model": "gpt-4.1-mini",
                "choices": [
                    {
                        "message": {
                            "content": '{"summary":"ok"}',
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 9,
                    "completion_tokens": 4,
                    "total_tokens": 13,
                },
            }
        )

    monkeypatch.setattr("papermentor_os.llm.providers.request.urlopen", _fake_urlopen)

    response = provider.generate_structured(
        [LLMMessage(role=MessageRole.USER, content="请输出结构化结论。")],
        DummyStructuredOutput,
        ProviderConfig(
            provider_id="openai_compatible",
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4.1-mini",
        ),
    )

    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["timeout"] == 20.0
    assert captured["headers"]["Authorization"] == "Bearer sk-test"
    assert captured["body"]["response_format"]["type"] == "json_schema"
    assert captured["body"]["response_format"]["json_schema"]["name"] == "DummyStructuredOutput"
    assert captured["body"]["messages"] == [
        {
            "role": "user",
            "content": "请输出结构化结论。",
        }
    ]
    assert response.content == '{"summary":"ok"}'
    assert response.finish_reason == "stop"
    assert response.usage is not None
    assert response.usage.prompt_tokens == 9
    assert response.usage.completion_tokens == 4
    assert response.usage.total_tokens == 13


def test_openai_compatible_provider_routes_deepseek_on_ark_to_chat_completions(
    monkeypatch,
) -> None:
    provider = OpenAICompatibleProvider()
    captured: dict[str, object] = {}

    def _fake_urlopen(http_request, timeout):
        captured["url"] = http_request.full_url
        captured["timeout"] = timeout
        captured["body"] = json.loads(http_request.data.decode("utf-8"))
        return _FakeHTTPResponse(
            {
                "model": "deepseek-r1-250528",
                "choices": [
                    {
                        "message": {
                            "content": '{"summary":"ok"}',
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 12,
                    "completion_tokens": 7,
                    "total_tokens": 19,
                    "prompt_tokens_details": {"cached_tokens": 0},
                    "completion_tokens_details": {"reasoning_tokens": 5},
                },
            }
        )

    monkeypatch.setattr("papermentor_os.llm.providers.request.urlopen", _fake_urlopen)

    response = provider.generate(
        [LLMMessage(role=MessageRole.USER, content="请输出结构化结论。")],
        ProviderConfig(
            provider_id="openai_compatible",
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key="sk-test",
            model_name="deepseek-r1-250528",
        ),
    )

    assert captured["url"] == "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    assert captured["timeout"] == 20.0
    assert captured["body"]["messages"] == [
        {
            "role": "user",
            "content": "请输出结构化结论。",
        }
    ]
    assert response.content == '{"summary":"ok"}'
    assert response.usage is not None
    assert response.usage.total_tokens == 19


def test_openai_compatible_provider_marks_rate_limit_as_retryable(monkeypatch) -> None:
    provider = OpenAICompatibleProvider()

    def _fake_urlopen(http_request, timeout):
        raise error.HTTPError(
            http_request.full_url,
            429,
            "Too Many Requests",
            hdrs=None,
            fp=_FakeHTTPResponse({"error": {"message": "rate limited"}}),
        )

    monkeypatch.setattr("papermentor_os.llm.providers.request.urlopen", _fake_urlopen)

    try:
        provider.generate(
            [LLMMessage(role=MessageRole.USER, content="hello")],
            ProviderConfig(
                provider_id="openai_compatible",
                base_url="https://api.openai.com/v1",
                api_key="sk-test",
                model_name="gpt-4.1-mini",
            ),
        )
    except LLMProviderError as error_detail:
        assert error_detail.category == "rate_limit"
        assert error_detail.retryable is True
        assert error_detail.status_code == 429
    else:
        raise AssertionError("expected provider error")


def test_openai_compatible_provider_marks_invalid_response_shape(monkeypatch) -> None:
    provider = OpenAICompatibleProvider()

    def _fake_urlopen(http_request, timeout):
        return _FakeHTTPResponse(
            {
                "model": "gpt-4.1-mini",
                "usage": {
                    "prompt_tokens": 9,
                    "completion_tokens": 4,
                    "total_tokens": 13,
                },
            }
        )

    monkeypatch.setattr("papermentor_os.llm.providers.request.urlopen", _fake_urlopen)

    try:
        provider.generate(
            [LLMMessage(role=MessageRole.USER, content="hello")],
            ProviderConfig(
                provider_id="openai_compatible",
                base_url="https://api.openai.com/v1",
                api_key="sk-test",
                model_name="gpt-4.1-mini",
            ),
        )
    except LLMProviderError as error_detail:
        assert error_detail.category == "invalid_response_shape"
        assert error_detail.retryable is False
    else:
        raise AssertionError("expected provider error")
