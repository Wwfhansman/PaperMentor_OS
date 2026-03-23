from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from papermentor_os.schemas.report import DimensionReport
from papermentor_os.schemas.trace import WorkerExecutionMetadata, WorkerSkillTrace
from papermentor_os.schemas.types import Dimension, Discipline, PaperStage


class WorkerCheckpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    worker_id: str = Field(min_length=1)
    dimension: Dimension
    report: DimensionReport
    execution_metadata: WorkerExecutionMetadata
    skill_trace: WorkerSkillTrace


class ReviewCheckpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_id: str = Field(min_length=1)
    stage: PaperStage
    discipline: Discipline
    completed_workers: list[WorkerCheckpoint] = Field(default_factory=list)

    def worker_ids(self) -> list[str]:
        return [item.worker_id for item in self.completed_workers]

    def get_worker(self, worker_id: str) -> WorkerCheckpoint | None:
        for item in self.completed_workers:
            if item.worker_id == worker_id:
                return item
        return None
