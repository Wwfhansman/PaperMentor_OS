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


class OrchestrationTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: PaperStage
    discipline: Discipline
    worker_sequence: list[str] = Field(default_factory=list)
    total_findings: int = Field(ge=0)
    debate_candidate_dimensions: list[Dimension] = Field(default_factory=list)
    debated_dimensions: list[Dimension] = Field(default_factory=list)
    debate_judge_skill_version: str | None = None


class ReviewTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    worker_skills: list[WorkerSkillTrace] = Field(default_factory=list)
    worker_runs: list[WorkerExecutionTrace] = Field(default_factory=list)
    orchestration: OrchestrationTrace | None = None
    debate_candidates: list[DebateCase] = Field(default_factory=list)
    debate_resolutions: list[DebateResolution] = Field(default_factory=list)


class DebugReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report: FinalReport
    trace: ReviewTrace
