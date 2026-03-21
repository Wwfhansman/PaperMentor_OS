from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from papermentor_os.schemas.debate import DebateCase, DebateResolution
from papermentor_os.schemas.report import FinalReport


class ReviewTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    debate_candidates: list[DebateCase] = Field(default_factory=list)
    debate_resolutions: list[DebateResolution] = Field(default_factory=list)


class DebugReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report: FinalReport
    trace: ReviewTrace

