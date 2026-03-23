from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from papermentor_os.llm.config import ProviderConfig, StructuredOutputMode


class WorkerRunPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeout: float | None = Field(default=None, gt=0.0)
    max_retries: int | None = Field(default=None, ge=0, le=5)
    retry_backoff_base_ms: int | None = Field(default=None, ge=0, le=10_000)
    retry_jitter_ms: int | None = Field(default=None, ge=0, le=10_000)
    prompt_char_budget: int | None = Field(default=None, gt=0)
    structured_output_mode: StructuredOutputMode | None = None
    cooldown_after_success_ms: int = Field(default=0, ge=0)
    cooldown_after_failure_ms: int = Field(default=0, ge=0)

    def apply_to_config(self, config: ProviderConfig | None) -> ProviderConfig | None:
        if config is None:
            return None

        update_payload: dict[str, object] = {}
        if self.timeout is not None:
            update_payload["timeout"] = self.timeout
        if self.max_retries is not None:
            update_payload["max_retries"] = self.max_retries
        if self.retry_backoff_base_ms is not None:
            update_payload["retry_backoff_base_ms"] = self.retry_backoff_base_ms
        if self.retry_jitter_ms is not None:
            update_payload["retry_jitter_ms"] = self.retry_jitter_ms
        if self.prompt_char_budget is not None:
            update_payload["prompt_char_budget"] = self.prompt_char_budget
        if self.structured_output_mode is not None:
            update_payload["structured_output_mode"] = self.structured_output_mode
        if not update_payload:
            return config
        return config.model_copy(update=update_payload)


DEFAULT_WORKER_RUN_POLICIES: dict[str, WorkerRunPolicy] = {
    "TopicScopeAgent": WorkerRunPolicy(prompt_char_budget=3200),
    "LogicChainAgent": WorkerRunPolicy(prompt_char_budget=3600),
    "LiteratureSupportAgent": WorkerRunPolicy(prompt_char_budget=3200),
    "NoveltyDepthAgent": WorkerRunPolicy(prompt_char_budget=3200),
    "WritingFormatAgent": WorkerRunPolicy(prompt_char_budget=2800),
}


def build_worker_run_policies(
    base_config: ProviderConfig | None,
) -> dict[str, WorkerRunPolicy]:
    policies = {
        worker_id: policy.model_copy(deep=True)
        for worker_id, policy in DEFAULT_WORKER_RUN_POLICIES.items()
    }
    if base_config is None:
        return policies

    if _is_ark_provider(base_config):
        for worker_id, policy in policies.items():
            success_cooldown = 200 if worker_id in {"TopicScopeAgent", "LogicChainAgent"} else 350
            failure_cooldown = 900 if worker_id in {"LiteratureSupportAgent", "NoveltyDepthAgent"} else 600
            policies[worker_id] = policy.model_copy(
                update={
                    "cooldown_after_success_ms": success_cooldown,
                    "cooldown_after_failure_ms": failure_cooldown,
                }
            )
    return policies


def _is_ark_provider(config: ProviderConfig) -> bool:
    base_url = (config.base_url or "").strip().lower()
    return "volces.com" in base_url or "/api/v3" in base_url
