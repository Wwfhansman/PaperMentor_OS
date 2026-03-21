from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from papermentor_os.schemas.types import Dimension, Severity


class EvidenceAnchor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    anchor_id: str = Field(min_length=1)
    location_label: str = Field(min_length=1)
    quote: str = Field(min_length=1)


class ReviewFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: Dimension
    issue_title: str = Field(min_length=1)
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_anchor: EvidenceAnchor
    diagnosis: str = Field(min_length=1)
    why_it_matters: str = Field(min_length=1)
    next_action: str = Field(min_length=1)
    source_agent: str = Field(min_length=1)
    source_skill_version: str = Field(min_length=1)


class DimensionReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: Dimension
    score: float = Field(ge=0.0, le=10.0)
    summary: str = Field(min_length=1)
    findings: list[ReviewFinding] = Field(default_factory=list)
    debate_used: bool = False


class PriorityAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    severity: Severity
    dimension: Dimension
    why_it_matters: str = Field(min_length=1)
    next_action: str = Field(min_length=1)
    anchor_id: str = Field(min_length=1)


class StudentGuidance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    next_steps: list[str] = Field(default_factory=list)


class AdvisorView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quick_summary: str = Field(min_length=1)
    watch_points: list[str] = Field(default_factory=list)


class FinalReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_summary: str = Field(min_length=1)
    dimension_reports: list[DimensionReport] = Field(default_factory=list)
    priority_actions: list[PriorityAction] = Field(default_factory=list)
    student_guidance: StudentGuidance
    advisor_view: AdvisorView
    safety_notice: str = Field(min_length=1)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

