from __future__ import annotations

from abc import ABC, abstractmethod

from papermentor_os.llm.exceptions import LLMConfigurationError, LLMProviderError, LLMStructuredOutputError
from papermentor_os.llm.models import LLMRuntimeStats
from papermentor_os.schemas.paper import PaperPackage
from papermentor_os.schemas.report import DimensionReport
from papermentor_os.schemas.trace import WorkerExecutionMetadata
from papermentor_os.skills.loader import SkillBundle


class BaseReviewAgent(ABC):
    agent_name: str
    skill_version: str

    @abstractmethod
    def review(self, paper: PaperPackage, skill_bundle: SkillBundle | None = None) -> DimensionReport:
        raise NotImplementedError

    def resolve_skill_version(self, skill_bundle: SkillBundle | None) -> str:
        if skill_bundle is None:
            return self.skill_version
        return skill_bundle.primary_rubric_version(self.skill_version)

    def build_execution_metadata(self) -> WorkerExecutionMetadata:
        return WorkerExecutionMetadata()

    def classify_llm_error(self, error: Exception) -> str:
        return f"error:{error.__class__.__name__}"

    def categorize_llm_error(self, error: Exception) -> str:
        if isinstance(error, LLMConfigurationError):
            return "configuration"
        if isinstance(error, LLMStructuredOutputError):
            return error.category or "structured_output"
        if isinstance(error, LLMProviderError):
            return error.category or "provider_runtime"
        return "runtime"

    def build_llm_execution_metadata(self) -> WorkerExecutionMetadata:
        runtime_stats = self._get_llm_runtime_stats()
        return WorkerExecutionMetadata(
            review_backend=getattr(self, "last_effective_backend", "rule_only"),
            llm_provider_id=getattr(self, "last_llm_provider_id", None),
            llm_model_name=getattr(self, "last_llm_model_name", None),
            llm_finish_reason=getattr(self, "last_llm_finish_reason", None),
            llm_error_category=getattr(self, "last_llm_error_category", None),
            structured_output_status=getattr(self, "last_structured_output_status", "not_requested"),
            fallback_used=getattr(self, "last_fallback_used", False),
            llm_request_attempts=runtime_stats.request_attempts if runtime_stats is not None else 0,
            llm_retry_count=runtime_stats.retry_count if runtime_stats is not None else 0,
            llm_prompt_tokens=runtime_stats.prompt_tokens if runtime_stats is not None else None,
            llm_completion_tokens=runtime_stats.completion_tokens if runtime_stats is not None else None,
            llm_total_tokens=runtime_stats.total_tokens if runtime_stats is not None else None,
        )

    def capture_llm_runtime_stats(self, runtime_stats: LLMRuntimeStats | None) -> None:
        setattr(self, "last_llm_runtime_stats", runtime_stats)

    def _get_llm_runtime_stats(self) -> LLMRuntimeStats | None:
        value = getattr(self, "last_llm_runtime_stats", None)
        if isinstance(value, LLMRuntimeStats):
            return value
        return None
