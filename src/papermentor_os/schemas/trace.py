from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from papermentor_os.schemas.debate import DebateCase, DebateResolution
from papermentor_os.schemas.report import FinalReport
from papermentor_os.schemas.types import Dimension, Discipline, PaperStage


class WorkerSkillTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    worker_id: str = Field(min_length=1)
    rubric_skills: list[str] = Field(default_factory=list)
    policy_skills: list[str] = Field(default_factory=list)
    output_schema_skills: list[str] = Field(default_factory=list)
    domain_skills: list[str] = Field(default_factory=list)


class WorkerExecutionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_backend: str = Field(default="rule_only", min_length=1)
    llm_provider_id: str | None = None
    llm_model_name: str | None = None
    llm_finish_reason: str | None = None
    llm_error_category: str | None = None
    structured_output_status: str = Field(default="not_requested", min_length=1)
    fallback_used: bool = False
    llm_request_attempts: int = Field(default=0, ge=0)
    llm_retry_count: int = Field(default=0, ge=0)
    llm_prompt_tokens: int | None = Field(default=None, ge=0)
    llm_completion_tokens: int | None = Field(default=None, ge=0)
    llm_total_tokens: int | None = Field(default=None, ge=0)


class WorkerExecutionTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    worker_id: str = Field(min_length=1)
    dimension: Dimension
    score: float = Field(ge=0.0, le=10.0)
    finding_count: int = Field(ge=0)
    high_severity_count: int = Field(ge=0)
    debate_candidate: bool = False
    debate_used: bool = False
    summary: str = Field(min_length=1)
    review_backend: str = Field(default="rule_only", min_length=1)
    llm_provider_id: str | None = None
    llm_model_name: str | None = None
    llm_finish_reason: str | None = None
    llm_error_category: str | None = None
    structured_output_status: str = Field(default="not_requested", min_length=1)
    fallback_used: bool = False
    llm_request_attempts: int = Field(default=0, ge=0)
    llm_retry_count: int = Field(default=0, ge=0)
    llm_prompt_tokens: int | None = Field(default=None, ge=0)
    llm_completion_tokens: int | None = Field(default=None, ge=0)
    llm_total_tokens: int | None = Field(default=None, ge=0)


class OrchestrationTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: PaperStage
    discipline: Discipline
    worker_sequence: list[str] = Field(default_factory=list)
    resumed_from_checkpoint: bool = False
    checkpoint_completed_worker_count: int = Field(default=0, ge=0)
    resumed_worker_ids: list[str] = Field(default_factory=list)
    skipped_worker_ids: list[str] = Field(default_factory=list)
    resume_start_worker_id: str | None = None
    total_findings: int = Field(ge=0)
    debate_candidate_dimensions: list[Dimension] = Field(default_factory=list)
    debated_dimensions: list[Dimension] = Field(default_factory=list)
    debate_judge_skill_version: str | None = None


class DebateResolutionTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: Dimension
    trigger_reason: str = Field(min_length=1)
    candidate_issue_titles: list[str] = Field(default_factory=list)
    recommended_action: str = Field(min_length=1)
    confidence_floor: float = Field(ge=0.0, le=1.0)
    pre_debate_score: float = Field(ge=0.0, le=10.0)
    adjusted_score: float = Field(ge=0.0, le=10.0)
    score_delta: float
    decision_policy_summary: str = Field(min_length=1)
    upheld_finding_count: int = Field(ge=0)
    dropped_finding_count: int = Field(ge=0)
    resolution_summary: str = Field(min_length=1)
    upheld_issue_titles: list[str] = Field(default_factory=list)
    dropped_issue_titles: list[str] = Field(default_factory=list)
    dropped_issue_reasons: dict[str, str] = Field(default_factory=dict)
    source_agent: str = Field(min_length=1)
    source_skill_version: str = Field(min_length=1)
    worker_review_backend: str = Field(default="rule_only", min_length=1)
    worker_llm_provider_id: str | None = None
    worker_llm_model_name: str | None = None
    worker_llm_finish_reason: str | None = None
    worker_llm_error_category: str | None = None
    worker_structured_output_status: str = Field(default="not_requested", min_length=1)
    worker_fallback_used: bool = False
    worker_llm_request_attempts: int = Field(default=0, ge=0)
    worker_llm_retry_count: int = Field(default=0, ge=0)
    worker_llm_prompt_tokens: int | None = Field(default=None, ge=0)
    worker_llm_completion_tokens: int | None = Field(default=None, ge=0)
    worker_llm_total_tokens: int | None = Field(default=None, ge=0)


class ReviewTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    worker_skills: list[WorkerSkillTrace] = Field(default_factory=list)
    worker_runs: list[WorkerExecutionTrace] = Field(default_factory=list)
    orchestration: OrchestrationTrace | None = None
    debate_candidates: list[DebateCase] = Field(default_factory=list)
    debate_resolutions: list[DebateResolution] = Field(default_factory=list)
    debate_resolution_traces: list[DebateResolutionTrace] = Field(default_factory=list)


class DebugReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report: FinalReport
    trace: ReviewTrace
