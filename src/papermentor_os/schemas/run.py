from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from papermentor_os.llm import ReviewLLMConfig
from papermentor_os.orchestrator.checkpoint import ReviewCheckpoint
from papermentor_os.orchestrator.run_state import ReviewRun
from papermentor_os.schemas.report import FinalReport
from papermentor_os.schemas.trace import ReviewTrace
from papermentor_os.schemas.types import Discipline, PaperStage


class ReviewRunError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    retryable: bool = False


class ReviewRunOwnershipSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_instance_id: str = Field(min_length=1)
    ownership_epoch: int = Field(default=1, ge=1)
    ownership_token: str = Field(min_length=1)
    lease_expires_at: datetime | None = None
    last_heartbeat_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReviewRunOwnership(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_instance_id: str | None = None
    lease_expires_at: datetime | None = None
    last_heartbeat_at: datetime | None = None
    lease_active: bool = False
    stale_lease: bool = False
    claimable: bool = False
    owned_by_current_instance: bool = False


class ReviewRunEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence_id: int = Field(ge=1)
    event_type: str = Field(min_length=1)
    run: ReviewRun
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AsyncReviewAcceptedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    status_url: str = Field(min_length=1)
    events_url: str = Field(min_length=1)
    run: ReviewRun
    ownership: ReviewRunOwnership | None = None


class ReviewRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run: ReviewRun
    report: FinalReport | None = None
    trace: ReviewTrace | None = None
    error: ReviewRunError | None = None
    ownership: ReviewRunOwnership | None = None


class ReviewRunClaimResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    claimed: bool = False
    previous_owner_instance_id: str | None = None
    resume_started: bool = False
    resume_reason: str | None = None
    run: ReviewRun
    ownership: ReviewRunOwnership | None = None


class ReviewRunRequestSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(min_length=1)
    stage: PaperStage
    discipline: Discipline
    llm: ReviewLLMConfig | None = None
    resume_uses_server_llm_credentials: bool = False
    auto_resume_supported: bool = False
    auto_resume_reason: str | None = None


class ReviewRunEventsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    events: list[ReviewRunEvent] = Field(default_factory=list)


class ReviewRunSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run: ReviewRun
    report: FinalReport | None = None
    trace: ReviewTrace | None = None
    error: ReviewRunError | None = None
    events: list[ReviewRunEvent] = Field(default_factory=list)
    ownership: ReviewRunOwnershipSnapshot | None = None
    request: ReviewRunRequestSnapshot | None = None
    checkpoint: ReviewCheckpoint | None = None
