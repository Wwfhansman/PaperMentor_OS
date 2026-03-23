from __future__ import annotations

import ipaddress
import os
from urllib.parse import urlparse
from collections.abc import Callable

from papermentor_os.agents.literature_support import LiteratureSupportAgent
from papermentor_os.agents.logic_chain import LogicChainAgent
from papermentor_os.agents.novelty_depth import NoveltyDepthAgent
from papermentor_os.agents.topic_scope import TopicScopeAgent
from papermentor_os.agents.writing_format import WritingFormatAgent
from papermentor_os.llm import (
    LLMClient,
    LLMConfigurationError,
    OpenAICompatibleProvider,
    ProviderConfig,
    ReviewBackend,
    ReviewLLMConfig,
    StructuredOutputMode,
)
from papermentor_os.orchestrator.checkpoint import WorkerCheckpoint
from papermentor_os.orchestrator.chief_reviewer import ChiefReviewer, ReviewRunCancelledError
from papermentor_os.orchestrator.run_state import ReviewRun
from papermentor_os.runtime import build_worker_run_policies


def build_chief_reviewer(
    llm_config: ReviewLLMConfig | None = None,
    *,
    run_update_hook: Callable[[ReviewRun], None] | None = None,
    worker_checkpoint_hook: Callable[[WorkerCheckpoint], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> ChiefReviewer:
    normalized_llm_config = _normalize_llm_config(llm_config)
    if normalized_llm_config is None or normalized_llm_config.review_backend == ReviewBackend.RULE_ONLY:
        return ChiefReviewer(
            run_update_hook=run_update_hook,
            worker_checkpoint_hook=worker_checkpoint_hook,
            cancel_check=cancel_check,
        )

    _validate_llm_config(normalized_llm_config)

    provider_config = ProviderConfig(
        provider_id=normalized_llm_config.provider_id,
        base_url=normalized_llm_config.base_url,
        api_key=normalized_llm_config.api_key,
        model_name=normalized_llm_config.model_name,
        temperature=normalized_llm_config.temperature,
        max_tokens=normalized_llm_config.max_tokens,
        timeout=normalized_llm_config.timeout,
        max_retries=normalized_llm_config.max_retries,
        retry_backoff_base_ms=normalized_llm_config.retry_backoff_base_ms,
        retry_jitter_ms=normalized_llm_config.retry_jitter_ms,
        prompt_char_budget=normalized_llm_config.prompt_char_budget,
        structured_output_mode=_resolve_structured_output_mode(normalized_llm_config),
    )
    worker_run_policies = build_worker_run_policies(provider_config)
    llm_client = LLMClient(
        OpenAICompatibleProvider(),
        cancel_check=cancel_check,
        cancelled_error_factory=lambda: ReviewRunCancelledError(
            "review run cancelled during llm retry/backoff"
        ),
    )
    review_backend = normalized_llm_config.review_backend

    return ChiefReviewer(
        topic_scope_agent=TopicScopeAgent(
            llm_client=llm_client,
            llm_config=provider_config,
            review_backend=review_backend,
        ),
        logic_chain_agent=LogicChainAgent(
            llm_client=llm_client,
            llm_config=provider_config,
            review_backend=review_backend,
        ),
        literature_support_agent=LiteratureSupportAgent(
            llm_client=llm_client,
            llm_config=provider_config,
            review_backend=review_backend,
        ),
        novelty_depth_agent=NoveltyDepthAgent(
            llm_client=llm_client,
            llm_config=provider_config,
            review_backend=review_backend,
        ),
        writing_format_agent=WritingFormatAgent(
            llm_client=llm_client,
            llm_config=provider_config,
            review_backend=review_backend,
        ),
        worker_run_policies=worker_run_policies,
        run_update_hook=run_update_hook,
        worker_checkpoint_hook=worker_checkpoint_hook,
        cancel_check=cancel_check,
    )


def _normalize_llm_config(llm_config: ReviewLLMConfig | None) -> ReviewLLMConfig | None:
    if llm_config is None:
        return None

    normalized_payload = llm_config.model_dump(mode="python")
    for field_name in ("provider_id", "base_url", "api_key", "model_name"):
        normalized_payload[field_name] = _normalize_optional_text(normalized_payload.get(field_name))
    normalized_payload["provider_id"] = normalized_payload["provider_id"] or "openai_compatible"
    return ReviewLLMConfig.model_validate(normalized_payload)


def _validate_llm_config(llm_config: ReviewLLMConfig) -> None:
    if llm_config.provider_id != "openai_compatible":
        raise LLMConfigurationError("llm.provider_id currently only supports `openai_compatible`.")
    if not llm_config.base_url:
        raise LLMConfigurationError("llm.base_url is required when llm review is enabled.")
    if not llm_config.model_name:
        raise LLMConfigurationError("llm.model_name is required when llm review is enabled.")

    parsed_base_url = urlparse(llm_config.base_url)
    if parsed_base_url.scheme not in {"http", "https"} or not parsed_base_url.netloc:
        raise LLMConfigurationError("llm.base_url must be a valid http(s) URL.")
    if parsed_base_url.username or parsed_base_url.password:
        raise LLMConfigurationError("llm.base_url must not embed credentials.")
    if not _private_llm_base_urls_allowed() and _is_private_hostname(parsed_base_url.hostname):
        raise LLMConfigurationError(
            "llm.base_url must not target localhost or a private network unless "
            "`PAPERMENTOR_OS_ALLOW_PRIVATE_LLM_BASE_URLS=1` is set."
        )


def _resolve_structured_output_mode(llm_config: ReviewLLMConfig) -> StructuredOutputMode:
    if llm_config.structured_output_mode is not None:
        return llm_config.structured_output_mode

    if not llm_config.base_url:
        return StructuredOutputMode.PROVIDER_JSON_SCHEMA

    parsed_base_url = urlparse(llm_config.base_url)
    hostname = (parsed_base_url.hostname or "").lower()
    path = parsed_base_url.path.rstrip("/")
    if hostname.endswith("volces.com") or path.endswith("/api/v3") or "/api/v3/" in path:
        return StructuredOutputMode.PROMPT_JSON

    return StructuredOutputMode.PROVIDER_JSON_SCHEMA


def _normalize_optional_text(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _private_llm_base_urls_allowed() -> bool:
    flag = os.getenv("PAPERMENTOR_OS_ALLOW_PRIVATE_LLM_BASE_URLS", "")
    return flag.strip().lower() in {"1", "true", "yes", "on"}


def _is_private_hostname(hostname: str | None) -> bool:
    if not hostname:
        return True

    normalized_hostname = hostname.strip().lower()
    if normalized_hostname in {"localhost", "localhost.localdomain"}:
        return True
    if normalized_hostname.endswith(".local"):
        return True

    try:
        parsed_ip = ipaddress.ip_address(normalized_hostname)
    except ValueError:
        return False

    return bool(
        parsed_ip.is_private
        or parsed_ip.is_loopback
        or parsed_ip.is_link_local
        or parsed_ip.is_multicast
        or parsed_ip.is_reserved
        or parsed_ip.is_unspecified
    )
