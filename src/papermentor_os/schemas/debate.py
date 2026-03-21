from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from papermentor_os.schemas.types import Dimension


class DebateCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: Dimension
    trigger_reason: str = Field(min_length=1)
    should_trigger: bool = True
    score: float = Field(ge=0.0, le=10.0)
    confidence_floor: float = Field(ge=0.0, le=1.0)
    candidate_issue_titles: list[str] = Field(default_factory=list)
    recommended_action: str = Field(min_length=1)


class DebateResolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: Dimension
    trigger_reason: str = Field(min_length=1)
    resolution_summary: str = Field(min_length=1)
    adjusted_score: float = Field(ge=0.0, le=10.0)
    upheld_issue_titles: list[str] = Field(default_factory=list)
    dropped_issue_titles: list[str] = Field(default_factory=list)
    source_agent: str = Field(min_length=1)
    source_skill_version: str = Field(min_length=1)
