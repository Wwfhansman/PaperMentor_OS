from papermentor_os.llm import ReviewBackend, ReviewLLMConfig, StructuredOutputMode
from papermentor_os.reviewer_factory import build_chief_reviewer


def test_build_chief_reviewer_defaults_to_provider_json_schema_for_standard_openai() -> None:
    reviewer = build_chief_reviewer(
        ReviewLLMConfig(
            review_backend=ReviewBackend.MODEL_ONLY,
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4.1-mini",
        )
    )

    assert reviewer.topic_scope_agent.llm_config is not None
    assert (
        reviewer.topic_scope_agent.llm_config.structured_output_mode
        == StructuredOutputMode.PROVIDER_JSON_SCHEMA
    )
    assert reviewer.worker_run_policies["TopicScopeAgent"].prompt_char_budget == 3200
    assert reviewer.worker_run_policies["TopicScopeAgent"].cooldown_after_success_ms == 0


def test_build_chief_reviewer_defaults_to_prompt_json_for_ark() -> None:
    reviewer = build_chief_reviewer(
        ReviewLLMConfig(
            review_backend=ReviewBackend.MODEL_ONLY,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key="sk-test",
            model_name="glm-4-7-251222",
        )
    )

    assert reviewer.topic_scope_agent.llm_config is not None
    assert reviewer.topic_scope_agent.llm_config.structured_output_mode == StructuredOutputMode.PROMPT_JSON
    assert reviewer.worker_run_policies["TopicScopeAgent"].cooldown_after_success_ms == 200
    assert reviewer.worker_run_policies["LiteratureSupportAgent"].cooldown_after_failure_ms == 900


def test_build_chief_reviewer_respects_explicit_structured_output_mode() -> None:
    reviewer = build_chief_reviewer(
        ReviewLLMConfig(
            review_backend=ReviewBackend.MODEL_ONLY,
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4.1-mini",
            structured_output_mode=StructuredOutputMode.PROMPT_JSON,
        )
    )

    assert reviewer.topic_scope_agent.llm_config is not None
    assert reviewer.topic_scope_agent.llm_config.structured_output_mode == StructuredOutputMode.PROMPT_JSON
