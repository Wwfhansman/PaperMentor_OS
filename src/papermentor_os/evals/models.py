from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from papermentor_os.llm import ReviewBackend
from papermentor_os.schemas.types import Dimension


class BenchmarkExpectation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    expected_high_severity_dimensions: list[Dimension] = Field(default_factory=list)
    expected_priority_first_dimension: Dimension | None = None
    expected_debate_dimensions: list[Dimension] = Field(default_factory=list)
    expected_issue_titles: list[str] = Field(default_factory=list)


class BenchmarkCaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    expected_high_severity_dimensions: list[Dimension] = Field(default_factory=list)
    actual_high_severity_dimensions: list[Dimension] = Field(default_factory=list)
    high_severity_dimension_recall: float = Field(ge=0.0, le=1.0)
    expected_priority_first_dimension: Dimension | None = None
    actual_priority_first_dimension: Dimension | None = None
    priority_first_dimension_match: bool | None = None
    expected_debate_dimensions: list[Dimension] = Field(default_factory=list)
    actual_debate_dimensions: list[Dimension] = Field(default_factory=list)
    debate_dimension_recall: float = Field(ge=0.0, le=1.0)
    expected_issue_titles: list[str] = Field(default_factory=list)
    actual_issue_titles: list[str] = Field(default_factory=list)
    missing_issue_titles: list[str] = Field(default_factory=list)
    unexpected_issue_titles: list[str] = Field(default_factory=list)
    issue_title_recall: float = Field(ge=0.0, le=1.0)
    issue_title_false_positive_rate: float = Field(ge=0.0, le=1.0)
    llm_request_attempts: int = Field(default=0, ge=0)
    llm_retry_count: int = Field(default=0, ge=0)
    llm_fallback_count: int = Field(default=0, ge=0)
    llm_error_count: int = Field(default=0, ge=0)
    llm_error_categories: dict[str, int] = Field(default_factory=dict)
    llm_usage_observation_count: int = Field(default=0, ge=0)
    llm_prompt_tokens: int = Field(default=0, ge=0)
    llm_completion_tokens: int = Field(default=0, ge=0)
    llm_total_tokens: int = Field(default=0, ge=0)
    resumed_from_checkpoint: bool = False
    checkpoint_completed_worker_count: int = Field(default=0, ge=0)
    skipped_worker_count: int = Field(default=0, ge=0)
    passed: bool = False


class BenchmarkSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: str = Field(default="rule", min_length=1)
    review_backend: ReviewBackend = ReviewBackend.RULE_ONLY
    expectation_override_case_count: int = Field(default=0, ge=0)
    llm_provider_id: str | None = None
    llm_model_name: str | None = None
    elapsed_seconds: float = Field(default=0.0, ge=0.0)
    average_case_duration_ms: float = Field(default=0.0, ge=0.0)
    llm_request_attempts: int = Field(default=0, ge=0)
    llm_retry_count: int = Field(default=0, ge=0)
    llm_fallback_count: int = Field(default=0, ge=0)
    llm_error_count: int = Field(default=0, ge=0)
    llm_error_categories: dict[str, int] = Field(default_factory=dict)
    llm_usage_observation_count: int = Field(default=0, ge=0)
    llm_prompt_tokens: int = Field(default=0, ge=0)
    llm_completion_tokens: int = Field(default=0, ge=0)
    llm_total_tokens: int = Field(default=0, ge=0)
    resumed_case_count: int = Field(default=0, ge=0)
    checkpoint_completed_worker_count: int = Field(default=0, ge=0)
    skipped_worker_count: int = Field(default=0, ge=0)
    llm_input_cost_estimate_usd: float | None = Field(default=None, ge=0.0)
    llm_output_cost_estimate_usd: float | None = Field(default=None, ge=0.0)
    llm_total_cost_estimate_usd: float | None = Field(default=None, ge=0.0)
    total_cases: int = Field(ge=0)
    fully_passed_cases: int = Field(ge=0)
    high_severity_dimension_recall: float = Field(ge=0.0, le=1.0)
    priority_first_dimension_accuracy: float = Field(ge=0.0, le=1.0)
    debate_dimension_recall: float = Field(ge=0.0, le=1.0)
    issue_title_recall: float = Field(ge=0.0, le=1.0)
    issue_title_false_positive_rate: float = Field(ge=0.0, le=1.0)
    case_results: list[BenchmarkCaseResult] = Field(default_factory=list)


class BenchmarkComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_summaries: list[BenchmarkSummary] = Field(default_factory=list)
    gate_variant_id: str | None = None


PricePerKTokens = Annotated[float, Field(ge=0.0)]


class BenchmarkPricingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_price_per_1k_tokens_usd: PricePerKTokens
    output_price_per_1k_tokens_usd: PricePerKTokens


class BenchmarkThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_high_severity_dimension_recall: float | None = Field(default=None, ge=0.0, le=1.0)
    min_priority_first_dimension_accuracy: float | None = Field(default=None, ge=0.0, le=1.0)
    min_debate_dimension_recall: float | None = Field(default=None, ge=0.0, le=1.0)
    min_issue_title_recall: float | None = Field(default=None, ge=0.0, le=1.0)
    max_issue_title_false_positive_rate: float | None = Field(default=None, ge=0.0, le=1.0)


class BenchmarkGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    failed_checks: list[str] = Field(default_factory=list)
