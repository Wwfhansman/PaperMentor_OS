import json

from pydantic import BaseModel, ConfigDict, Field

from papermentor_os.llm import (
    FakeLLMProvider,
    LLMClient,
    LLMMessage,
    LLMProviderError,
    LLMStructuredOutputError,
    MessageRole,
    ProviderConfig,
    StructuredOutputMode,
)


class DummyStructuredOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    count: int = Field(ge=0)


class StructuredFakeLLMProvider(FakeLLMProvider):
    def supports_json_schema(self) -> bool:
        return True


def _config(*, prompt_char_budget: int = 2000, max_retries: int = 1) -> ProviderConfig:
    return ProviderConfig(
        provider_id="fake",
        model_name="fake-topic-model",
        prompt_char_budget=prompt_char_budget,
        max_retries=max_retries,
    )


def test_llm_client_retries_after_provider_error() -> None:
    provider = FakeLLMProvider(
        responses=[
            LLMProviderError("transient timeout", category="network_timeout", retryable=True),
            '{"summary":"ok","count":1}',
        ]
    )
    sleep_calls: list[float] = []
    client = LLMClient(provider, sleep_fn=sleep_calls.append, random_fn=lambda: 0.0)

    response = client.generate(
        [LLMMessage(role=MessageRole.USER, content="test request")],
        _config(max_retries=1).model_copy(
            update={"retry_backoff_base_ms": 200, "retry_jitter_ms": 50}
        ),
    )

    assert response.content == '{"summary":"ok","count":1}'
    assert len(provider.requests) == 2
    assert sleep_calls == [0.2]
    assert response.runtime_stats is not None
    assert response.runtime_stats.request_attempts == 2
    assert response.runtime_stats.retry_count == 1
    assert response.runtime_stats.retry_sleep_ms == 200
    assert response.runtime_stats.prompt_char_count == len("test request")


def test_llm_client_does_not_retry_non_retryable_provider_error() -> None:
    provider = FakeLLMProvider(
        responses=[
            LLMProviderError("bad request", category="provider_http", retryable=False),
        ]
    )
    sleep_calls: list[float] = []
    client = LLMClient(provider, sleep_fn=sleep_calls.append, random_fn=lambda: 0.0)

    try:
        client.generate(
            [LLMMessage(role=MessageRole.USER, content="test request")],
            _config(max_retries=3).model_copy(
                update={"retry_backoff_base_ms": 200, "retry_jitter_ms": 50}
            ),
        )
    except LLMProviderError as error:
        assert error.category == "provider_http"
        assert error.runtime_stats is not None
        assert error.runtime_stats.request_attempts == 1
        assert error.runtime_stats.retry_sleep_ms == 0
    else:
        raise AssertionError("expected provider error")

    assert len(provider.requests) == 1
    assert sleep_calls == []


def test_llm_client_stops_retry_loop_when_cancelled_between_attempts() -> None:
    provider = FakeLLMProvider(
        responses=[
            LLMProviderError("transient timeout", category="network_timeout", retryable=True),
            '{"summary":"ok","count":1}',
        ]
    )
    sleep_calls: list[float] = []
    client = LLMClient(
        provider,
        sleep_fn=sleep_calls.append,
        random_fn=lambda: 0.0,
        cancel_check=lambda: len(provider.requests) >= 1,
        cancelled_error_factory=lambda: RuntimeError("cancelled"),
    )

    try:
        client.generate(
            [LLMMessage(role=MessageRole.USER, content="test request")],
            _config(max_retries=3).model_copy(
                update={"retry_backoff_base_ms": 200, "retry_jitter_ms": 50}
            ),
        )
    except RuntimeError as error:
        assert str(error) == "cancelled"
    else:
        raise AssertionError("expected cancellation error")

    assert len(provider.requests) == 1
    assert sleep_calls == []


def test_llm_client_parses_prompt_json_response() -> None:
    provider = FakeLLMProvider(
        responses=[
            "```json\n"
            + json.dumps({"summary": "structured ok", "count": 2}, ensure_ascii=False)
            + "\n```"
        ]
    )
    client = LLMClient(provider)

    response = client.generate_structured(
        [LLMMessage(role=MessageRole.USER, content="请输出结构化结果")],
        DummyStructuredOutput,
        _config(),
    )

    assert response.parsed.summary == "structured ok"
    assert response.parsed.count == 2
    assert "JSON 必须满足以下 schema" in provider.requests[0].messages[0].content
    assert response.raw.runtime_stats is not None
    assert response.raw.runtime_stats.request_attempts == 1


def test_llm_client_preserves_runtime_stats_on_structured_output_error() -> None:
    provider = FakeLLMProvider(responses=['{"summary": 123, "count": "bad"}'])
    client = LLMClient(provider)

    try:
        client.generate_structured(
            [LLMMessage(role=MessageRole.USER, content="请输出结构化结果")],
            DummyStructuredOutput,
            _config(),
        )
    except LLMStructuredOutputError as error:
        assert error.category == "structured_output_schema_mismatch"
        assert error.runtime_stats is not None
        assert error.runtime_stats.request_attempts == 1
        assert error.runtime_stats.retry_count == 0
    else:
        raise AssertionError("expected structured output error")


def test_llm_client_preserves_runtime_stats_on_provider_structured_error() -> None:
    provider = StructuredFakeLLMProvider(responses=[LLMProviderError("structured boom")])
    client = LLMClient(provider)

    try:
        client.generate_structured(
            [LLMMessage(role=MessageRole.USER, content="请输出结构化结果")],
            DummyStructuredOutput,
            _config(max_retries=0, prompt_char_budget=4000).model_copy(
                update={"structured_output_mode": StructuredOutputMode.PROVIDER_JSON_SCHEMA}
            ),
        )
    except LLMProviderError as error:
        assert error.category is None
        assert error.runtime_stats is not None
        assert error.runtime_stats.request_attempts == 1
        assert error.runtime_stats.retry_count == 0
    else:
        raise AssertionError("expected provider error")


def test_llm_client_applies_prompt_char_budget() -> None:
    provider = FakeLLMProvider(responses=['{"summary":"budgeted","count":1}'])
    client = LLMClient(provider)

    client.generate(
        [
            LLMMessage(role=MessageRole.SYSTEM, content="s" * 30),
            LLMMessage(role=MessageRole.USER, content="u" * 30),
        ],
        _config(prompt_char_budget=40),
    )

    total_chars = sum(len(message.content) for message in provider.requests[0].messages)
    assert total_chars <= 40


def test_llm_client_preserves_prompt_json_instruction_under_budget_pressure() -> None:
    provider = FakeLLMProvider(responses=['{"summary":"budgeted","count":1}'])
    client = LLMClient(provider)
    schema_instruction = client._build_prompt_json_instruction(DummyStructuredOutput)
    config = _config(prompt_char_budget=len(schema_instruction) + 24)

    client.generate_structured(
        [
            LLMMessage(role=MessageRole.SYSTEM, content="s" * 60),
            LLMMessage(role=MessageRole.USER, content="u" * 120),
        ],
        DummyStructuredOutput,
        config,
    )

    request_messages = provider.requests[0].messages
    assert request_messages[0].content == schema_instruction
    assert sum(len(message.content) for message in request_messages) <= config.prompt_char_budget
    assert len(request_messages) >= 2


def test_llm_client_raises_when_budget_cannot_fit_required_instruction() -> None:
    provider = FakeLLMProvider(responses=['{"summary":"ok","count":1}'])
    client = LLMClient(provider)
    schema_instruction = client._build_prompt_json_instruction(DummyStructuredOutput)

    try:
        client.generate_structured(
            [LLMMessage(role=MessageRole.USER, content="hello")],
            DummyStructuredOutput,
            _config(prompt_char_budget=len(schema_instruction) - 1),
        )
    except Exception as error:
        assert "required request instructions" in str(error)
    else:
        raise AssertionError("expected configuration error")
