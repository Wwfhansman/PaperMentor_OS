from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from papermentor_os.schemas.types import Dimension, Discipline, PaperStage


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RunState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    FALLBACK_COMPLETED = "fallback_completed"


class WorkerRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    worker_id: str = Field(min_length=1)
    dimension: Dimension
    state: RunState = RunState.PENDING
    from_checkpoint: bool = False
    score: float | None = Field(default=None, ge=0.0, le=10.0)
    finding_count: int = Field(default=0, ge=0)
    summary: str | None = None
    review_backend: str | None = None
    structured_output_status: str | None = None
    fallback_used: bool = False
    llm_error_category: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ReviewRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    paper_id: str = Field(min_length=1)
    stage: PaperStage
    discipline: Discipline
    state: RunState = RunState.PENDING
    worker_sequence: list[str] = Field(default_factory=list)
    selected_worker_ids: list[str] = Field(default_factory=list)
    worker_runs: list[WorkerRun] = Field(default_factory=list)
    resumed_from_checkpoint: bool = False
    checkpoint_completed_worker_count: int = Field(default=0, ge=0)
    completed_worker_count: int = Field(default=0, ge=0)
    fallback_worker_count: int = Field(default=0, ge=0)
    failed_worker_count: int = Field(default=0, ge=0)
    started_at: datetime
    updated_at: datetime
    finished_at: datetime | None = None
    stop_after_worker_id: str | None = None

    def get_worker(self, worker_id: str) -> WorkerRun | None:
        for worker_run in self.worker_runs:
            if worker_run.worker_id == worker_id:
                return worker_run
        return None

    def refresh_counters(self, *, now: datetime | None = None) -> None:
        self.completed_worker_count = sum(
            worker_run.state in {RunState.COMPLETED, RunState.FALLBACK_COMPLETED}
            for worker_run in self.worker_runs
        )
        self.fallback_worker_count = sum(
            worker_run.state == RunState.FALLBACK_COMPLETED
            for worker_run in self.worker_runs
        )
        self.failed_worker_count = sum(
            worker_run.state == RunState.FAILED
            for worker_run in self.worker_runs
        )
        self.updated_at = now or utc_now()
