from __future__ import annotations

from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from threading import Event, Lock, Thread
from uuid import uuid4
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Iterator

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX fallback
    fcntl = None

from papermentor_os.llm import ReviewLLMConfig
from papermentor_os.orchestrator import ChiefReviewer, ReviewRun, RunState, WorkerRun
from papermentor_os.orchestrator.checkpoint import ReviewCheckpoint, WorkerCheckpoint
from papermentor_os.orchestrator.chief_reviewer import ReviewRunCancelledError
from papermentor_os.orchestrator.run_state import utc_now
from papermentor_os.schemas.paper import PaperPackage
from papermentor_os.schemas.report import FinalReport
from papermentor_os.schemas.run import (
    AsyncReviewAcceptedResponse,
    ReviewRunClaimResponse,
    ReviewRunError,
    ReviewRunEvent,
    ReviewRunEventsResponse,
    ReviewRunRequestSnapshot,
    ReviewRunOwnership,
    ReviewRunOwnershipSnapshot,
    ReviewRunSnapshot,
    ReviewRunResponse,
)
from papermentor_os.schemas.trace import ReviewTrace
from papermentor_os.schemas.types import Discipline, PaperStage


@dataclass(slots=True)
class _RunRecord:
    run: ReviewRun
    report: FinalReport | None = None
    trace: ReviewTrace | None = None
    error: ReviewRunError | None = None
    events: list[ReviewRunEvent] = field(default_factory=list)
    ownership: ReviewRunOwnershipSnapshot | None = None
    request: ReviewRunRequestSnapshot | None = None
    checkpoint: ReviewCheckpoint | None = None


@dataclass(slots=True)
class _LocalExecutionControl:
    cancel_event: Event = field(default_factory=Event)
    lease_stop_event: Event = field(default_factory=Event)
    ownership_epoch: int | None = None


class ReviewRunClaimError(RuntimeError):
    def __init__(self, *, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class InMemoryReviewRunRegistry:
    def __init__(
        self,
        *,
        reviewer_builder: Callable[..., ChiefReviewer],
        trace_builder: Callable[[ChiefReviewer], ReviewTrace],
        error_mapper: Callable[[Exception], ReviewRunError],
        snapshot_dir: Path | None = None,
        max_workers: int = 4,
        retention_seconds: float | None = None,
        instance_id: str | None = None,
        lease_seconds: float = 30.0,
    ) -> None:
        self.reviewer_builder = reviewer_builder
        self.trace_builder = trace_builder
        self.error_mapper = error_mapper
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = Lock()
        self._runs: dict[str, _RunRecord] = {}
        self._local_execution_controls: dict[str, _LocalExecutionControl] = {}
        self._closed = False
        self.snapshot_dir = snapshot_dir
        self.retention_seconds = retention_seconds
        self.instance_id = instance_id or uuid4().hex
        self.lease_seconds = lease_seconds
        if self.snapshot_dir is not None:
            self.snapshot_dir.mkdir(parents=True, exist_ok=True)
            self._load_snapshots()
        with self._lock:
            self._prune_expired_runs_locked()

    def submit_docx(
        self,
        *,
        file_path: Path,
        stage: PaperStage,
        discipline: Discipline,
        llm_config: ReviewLLMConfig | None,
    ) -> AsyncReviewAcceptedResponse:
        with self._lock:
            if self._closed:
                raise RuntimeError("review run registry is closed")
        run_id = uuid4().hex
        initial_ownership_epoch = 1
        with self._lock:
            self._local_execution_controls[run_id] = _LocalExecutionControl(
                ownership_epoch=initial_ownership_epoch,
            )
        try:
            reviewer = self.reviewer_builder(
                llm_config,
                run_update_hook=self._build_run_update_hook(
                    run_id,
                    ownership_epoch=initial_ownership_epoch,
                ),
                worker_checkpoint_hook=self._build_worker_checkpoint_hook(
                    run_id,
                    ownership_epoch=initial_ownership_epoch,
                ),
                cancel_check=self._build_cancel_check(
                    run_id,
                    ownership_epoch=initial_ownership_epoch,
                ),
            )
        except Exception:
            with self._lock:
                self._local_execution_controls.pop(run_id, None)
            raise
        paper = reviewer.parser.parse_file(file_path, stage=stage, discipline=discipline)
        timestamp = utc_now()
        worker_dimensions = reviewer.worker_dimensions()
        initial_run = ReviewRun(
            run_id=run_id,
            paper_id=paper.paper_id,
            stage=paper.stage,
            discipline=paper.discipline,
            state=RunState.PENDING,
            worker_sequence=reviewer.worker_ids(),
            selected_worker_ids=reviewer.worker_ids(),
            worker_runs=[
                WorkerRun(worker_id=worker_id, dimension=dimension)
                for worker_id, dimension in worker_dimensions.items()
            ],
            started_at=timestamp,
            updated_at=timestamp,
        )
        initial_ownership = self._active_ownership(
            timestamp,
            ownership_epoch=initial_ownership_epoch,
        )
        request_snapshot = self._build_request_snapshot(
            file_path=file_path,
            stage=stage,
            discipline=discipline,
            llm_config=llm_config,
        )
        with self._lock:
            self._prune_expired_runs_locked()
            self._runs[run_id] = _RunRecord(
                run=initial_run,
                ownership=initial_ownership,
                request=request_snapshot,
                checkpoint=ReviewCheckpoint(
                    paper_id=paper.paper_id,
                    stage=paper.stage,
                    discipline=paper.discipline,
                ),
            )
            self._append_event_locked(run_id, "created", initial_run)
            self._persist_record_locked(run_id)

        self._executor.submit(
            self._execute_run,
            run_id,
            initial_ownership_epoch,
            reviewer,
            paper,
        )
        return AsyncReviewAcceptedResponse(
            run_id=run_id,
            status_url=f"/review/runs/{run_id}",
            events_url=f"/review/runs/{run_id}/events",
            run=initial_run.model_copy(deep=True),
            ownership=self._materialize_public_ownership(
                initial_ownership,
                run_state=initial_run.state,
            ),
        )

    def get_run(self, run_id: str) -> ReviewRunResponse | None:
        with self._lock:
            self._sync_record_from_snapshot_locked(run_id)
            self._prune_expired_runs_locked()
            record = self._runs.get(run_id)
            if record is None:
                return None
            public_run = self._materialize_public_run_locked(record)
            return ReviewRunResponse(
                run=public_run,
                report=record.report.model_copy(deep=True) if record.report is not None else None,
                trace=record.trace.model_copy(deep=True) if record.trace is not None else None,
                error=record.error.model_copy(deep=True) if record.error is not None else None,
                ownership=self._materialize_public_ownership(
                    record.ownership,
                    run_state=public_run.state,
                ),
            )

    def claim_run(self, run_id: str) -> ReviewRunClaimResponse | None:
        with self._lock:
            self._sync_record_from_snapshot_locked(run_id)
            self._prune_expired_runs_locked()
            record = self._runs.get(run_id)
            if record is None:
                return None
            if record.run.state in {RunState.COMPLETED, RunState.FAILED}:
                raise ReviewRunClaimError(
                    code="terminal_run",
                    message="cannot claim a completed or failed review run",
                )
            ownership = self._materialize_public_ownership(
                record.ownership,
                run_state=record.run.state,
            )
            if ownership is not None and ownership.owned_by_current_instance and ownership.lease_active:
                return ReviewRunClaimResponse(
                    run_id=run_id,
                    claimed=False,
                    previous_owner_instance_id=ownership.owner_instance_id,
                    resume_started=False,
                    resume_reason="current instance already owns the active lease",
                    run=record.run.model_copy(deep=True),
                    ownership=ownership,
                )
            if ownership is not None and ownership.lease_active:
                raise ReviewRunClaimError(
                    code="active_foreign_lease",
                    message="cannot claim review run while another instance still holds an active lease",
                )
            previous_owner_instance_id = record.ownership.owner_instance_id if record.ownership is not None else None
            next_ownership_epoch = self._next_ownership_epoch(record)
            record.ownership = self._active_ownership(ownership_epoch=next_ownership_epoch)
            self._append_event_locked(run_id, "ownership_claimed", record.run)
            self._persist_record_locked(run_id)
            resume_started = False
            resume_reason = self._auto_resume_reason_locked(record)
            if self._can_auto_resume_locked(record):
                self._executor.submit(
                    self._resume_claimed_run,
                    run_id,
                    next_ownership_epoch,
                )
                resume_started = True
                resume_reason = "resumed_from_source_with_checkpoint"
            return ReviewRunClaimResponse(
                run_id=run_id,
                claimed=True,
                previous_owner_instance_id=previous_owner_instance_id,
                resume_started=resume_started,
                resume_reason=resume_reason,
                run=record.run.model_copy(deep=True),
                ownership=self._materialize_public_ownership(
                    record.ownership,
                    run_state=record.run.state,
                ),
            )

    def get_events(
        self,
        run_id: str,
        *,
        after_sequence_id: int | None = None,
    ) -> ReviewRunEventsResponse | None:
        with self._lock:
            self._sync_record_from_snapshot_locked(run_id)
            self._prune_expired_runs_locked()
            record = self._runs.get(run_id)
            if record is None:
                return None
            events = record.events
            if after_sequence_id is not None:
                events = [event for event in events if event.sequence_id > after_sequence_id]
            return ReviewRunEventsResponse(
                run_id=run_id,
                events=[event.model_copy(deep=True) for event in events],
            )

    def close(self, *, wait: bool = True) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            for run_id in list(self._local_execution_controls):
                self._cancel_local_execution_locked(run_id)
        self._executor.shutdown(wait=wait, cancel_futures=True)

    def _execute_run(
        self,
        run_id: str,
        ownership_epoch: int,
        reviewer: ChiefReviewer,
        paper: PaperPackage,
    ) -> None:
        lease_stop_event = Event()
        with self._lock:
            control = self._local_execution_controls.setdefault(run_id, _LocalExecutionControl())
            control.cancel_event.clear()
            control.lease_stop_event.clear()
            control.ownership_epoch = ownership_epoch
            lease_stop_event = control.lease_stop_event
        lease_thread = Thread(
            target=self._renew_run_lease_until_stopped,
            args=(run_id, ownership_epoch, lease_stop_event),
            daemon=True,
        )
        lease_thread.start()
        try:
            report = reviewer.review_paper(paper, run_id=run_id)
            trace = self.trace_builder(reviewer)
            with self._lock:
                self._sync_record_from_snapshot_locked(run_id)
                record = self._runs[run_id]
                if not self._execution_branch_can_write_locked(record, ownership_epoch):
                    return
                if reviewer.last_review_run is not None:
                    record.run = reviewer.last_review_run.model_copy(deep=True)
                record.report = report.model_copy(deep=True)
                record.trace = trace.model_copy(deep=True)
                record.error = None
                self._append_event_locked(run_id, "completed", record.run)
                record.ownership = self._released_ownership(
                    ownership_epoch=ownership_epoch,
                )
                self._persist_record_locked(run_id)
        except ReviewRunCancelledError:
            return
        except Exception as error:  # pragma: no cover - exercised through integration behavior
            mapped_error = self.error_mapper(error)
            trace = self.trace_builder(reviewer)
            with self._lock:
                self._sync_record_from_snapshot_locked(run_id)
                record = self._runs[run_id]
                if not self._execution_branch_can_write_locked(record, ownership_epoch):
                    return
                if reviewer.last_review_run is not None:
                    record.run = reviewer.last_review_run.model_copy(deep=True)
                else:
                    record.run.state = RunState.FAILED
                record.trace = trace.model_copy(deep=True)
                record.error = mapped_error
                self._append_event_locked(run_id, "failed", record.run)
                record.ownership = self._released_ownership(
                    ownership_epoch=ownership_epoch,
                )
                self._persist_record_locked(run_id)
        finally:
            lease_stop_event.set()
            lease_thread.join(timeout=max(self.lease_seconds, 0.1))
            with self._lock:
                self._clear_local_execution_control_locked(run_id, ownership_epoch=ownership_epoch)

    def _build_run_update_hook(
        self,
        run_id: str,
        *,
        ownership_epoch: int,
    ) -> Callable[[ReviewRun], None]:
        def _handle(run: ReviewRun) -> None:
            with self._lock:
                self._sync_record_from_snapshot_locked(run_id)
                self._prune_expired_runs_locked()
                record = self._runs.get(run_id)
                if record is None:
                    return
                if not self._execution_branch_can_write_locked(record, ownership_epoch):
                    return
                record.run = run.model_copy(deep=True)
                record.ownership = self._active_ownership(
                    ownership_epoch=ownership_epoch,
                )
                self._append_event_locked(run_id, "updated", record.run)
                self._persist_record_locked(run_id)

        return _handle

    def _build_worker_checkpoint_hook(
        self,
        run_id: str,
        *,
        ownership_epoch: int,
    ) -> Callable[[WorkerCheckpoint], None]:
        def _handle(worker_checkpoint: WorkerCheckpoint) -> None:
            with self._lock:
                self._sync_record_from_snapshot_locked(run_id)
                record = self._runs.get(run_id)
                if record is None:
                    return
                if record.checkpoint is None:
                    return
                if not self._execution_branch_can_write_locked(record, ownership_epoch):
                    return
                record.checkpoint.completed_workers = [
                    item
                    for item in record.checkpoint.completed_workers
                    if item.worker_id != worker_checkpoint.worker_id
                ]
                record.checkpoint.completed_workers.append(worker_checkpoint)
                self._persist_record_locked(run_id)

        return _handle

    def _append_event_locked(
        self,
        run_id: str,
        event_type: str,
        run: ReviewRun,
    ) -> None:
        record = self._runs[run_id]
        record.events.append(
            ReviewRunEvent(
                sequence_id=len(record.events) + 1,
                event_type=event_type,
                run=run.model_copy(deep=True),
            )
        )

    def _materialize_public_run_locked(self, record: _RunRecord) -> ReviewRun:
        public_run = record.run.model_copy(deep=True)
        if (
            public_run.state == RunState.COMPLETED
            and record.report is None
            and record.error is None
        ):
            public_run.state = RunState.RUNNING
            public_run.finished_at = None
        return public_run

    def _persist_record_locked(self, run_id: str) -> None:
        if self.snapshot_dir is None:
            return
        record = self._runs[run_id]
        snapshot = ReviewRunSnapshot(
            run=record.run,
            report=record.report,
            trace=record.trace,
            error=record.error,
            events=record.events,
            ownership=record.ownership,
            request=record.request,
            checkpoint=record.checkpoint,
        )
        with self._snapshot_run_lock(run_id):
            snapshot_path = self._snapshot_path(run_id)
            temp_path = snapshot_path.with_name(f"{snapshot_path.name}.{uuid4().hex}.tmp")
            temp_path.write_text(
                snapshot.model_dump_json(indent=2),
                encoding="utf-8",
            )
            temp_path.replace(snapshot_path)

    def _load_snapshots(self) -> None:
        if self.snapshot_dir is None:
            return
        with self._snapshot_dir_lock():
            for snapshot_path in sorted(self.snapshot_dir.glob("*.json")):
                snapshot = self._read_snapshot(snapshot_path)
                if snapshot is None:
                    continue
                self._runs[snapshot.run.run_id] = self._build_record(snapshot)

    def _snapshot_path(self, run_id: str) -> Path:
        if self.snapshot_dir is None:
            raise RuntimeError("snapshot_dir is not configured")
        return self.snapshot_dir / f"{run_id}.json"

    def _prune_expired_runs_locked(self) -> None:
        if self.retention_seconds is None:
            return
        now = utc_now()
        expired_run_ids = [
            run_id
            for run_id, record in self._runs.items()
            if self._is_expired_record(record, now=now)
        ]
        with self._snapshot_dir_lock():
            for run_id in expired_run_ids:
                self._runs.pop(run_id, None)
                self._cancel_local_execution_locked(run_id)
                self._local_execution_controls.pop(run_id, None)
                if self.snapshot_dir is not None:
                    with self._snapshot_run_lock(run_id):
                        self._snapshot_path(run_id).unlink(missing_ok=True)
                        self._snapshot_lock_path(run_id).unlink(missing_ok=True)

    def _is_expired_record(self, record: _RunRecord, *, now) -> bool:
        if record.run.state not in {RunState.COMPLETED, RunState.FAILED}:
            return False
        terminal_at = record.run.finished_at or record.run.updated_at
        return (now - terminal_at).total_seconds() > self.retention_seconds

    def _sync_record_from_snapshot_locked(self, run_id: str) -> None:
        if self.snapshot_dir is None:
            return
        snapshot_path = self._snapshot_path(run_id)
        if not snapshot_path.exists():
            return
        snapshot = self._read_snapshot(snapshot_path)
        if snapshot is None:
            return
        existing = self._runs.get(run_id)
        if existing is None or self._should_replace_record(existing, snapshot):
            self._runs[run_id] = self._build_record(snapshot)
        self._sync_local_execution_control_locked(run_id)

    def _should_replace_record(
        self,
        existing: _RunRecord,
        snapshot: ReviewRunSnapshot,
    ) -> bool:
        if snapshot.run.updated_at > existing.run.updated_at:
            return True
        if len(snapshot.events) > len(existing.events):
            return True
        if existing.report is None and snapshot.report is not None:
            return True
        if existing.trace is None and snapshot.trace is not None:
            return True
        if existing.error is None and snapshot.error is not None:
            return True
        if existing.request is None and snapshot.request is not None:
            return True
        if existing.checkpoint is None and snapshot.checkpoint is not None:
            return True
        if (
            existing.checkpoint is not None
            and snapshot.checkpoint is not None
            and len(snapshot.checkpoint.completed_workers) > len(existing.checkpoint.completed_workers)
        ):
            return True
        if existing.ownership is None and snapshot.ownership is not None:
            return True
        if (
            existing.ownership is not None
            and snapshot.ownership is not None
            and snapshot.ownership.ownership_epoch > existing.ownership.ownership_epoch
        ):
            return True
        if (
            existing.ownership is not None
            and snapshot.ownership is not None
            and snapshot.ownership.last_heartbeat_at > existing.ownership.last_heartbeat_at
        ):
            return True
        return False

    def _build_record(self, snapshot: ReviewRunSnapshot) -> _RunRecord:
        return _RunRecord(
            run=snapshot.run,
            report=snapshot.report,
            trace=snapshot.trace,
            error=snapshot.error,
            events=snapshot.events,
            ownership=snapshot.ownership,
            request=snapshot.request,
            checkpoint=snapshot.checkpoint,
        )

    def _read_snapshot(self, snapshot_path: Path) -> ReviewRunSnapshot | None:
        run_id = snapshot_path.stem
        with self._snapshot_run_lock(run_id):
            if not snapshot_path.exists():
                return None
            return ReviewRunSnapshot.model_validate_json(snapshot_path.read_text(encoding="utf-8"))

    @contextmanager
    def _snapshot_dir_lock(self) -> Iterator[None]:
        if self.snapshot_dir is None:
            yield
            return
        with self._file_lock(self.snapshot_dir / ".registry.lock"):
            yield

    @contextmanager
    def _snapshot_run_lock(self, run_id: str) -> Iterator[None]:
        if self.snapshot_dir is None:
            yield
            return
        with self._file_lock(self._snapshot_lock_path(run_id)):
            yield

    @contextmanager
    def _file_lock(self, lock_path: Path) -> Iterator[None]:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+", encoding="utf-8") as handle:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl is not None:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _snapshot_lock_path(self, run_id: str) -> Path:
        if self.snapshot_dir is None:
            raise RuntimeError("snapshot_dir is not configured")
        return self.snapshot_dir / f".{run_id}.lock"

    def _renew_run_lease_until_stopped(
        self,
        run_id: str,
        ownership_epoch: int,
        stop_event: Event,
    ) -> None:
        interval_seconds = max(self.lease_seconds / 3, 0.1)
        while not stop_event.wait(interval_seconds):
            self._heartbeat_run_lease(run_id, ownership_epoch=ownership_epoch)

    def _heartbeat_run_lease(self, run_id: str, *, ownership_epoch: int) -> None:
        with self._lock:
            self._sync_record_from_snapshot_locked(run_id)
            record = self._runs.get(run_id)
            if record is None:
                return
            if record.run.state in {RunState.COMPLETED, RunState.FAILED}:
                return
            if not self._execution_branch_can_write_locked(record, ownership_epoch):
                return
            record.ownership = self._active_ownership(ownership_epoch=ownership_epoch)
            self._persist_record_locked(run_id)

    def _build_cancel_check(
        self,
        run_id: str,
        *,
        ownership_epoch: int,
    ) -> Callable[[], bool]:
        def _handle() -> bool:
            with self._lock:
                control = self._local_execution_controls.get(run_id)
                if control is not None and (
                    control.cancel_event.is_set()
                    or control.ownership_epoch != ownership_epoch
                ):
                    return True
                self._sync_record_from_snapshot_locked(run_id)
                record = self._runs.get(run_id)
                if record is None:
                    return False
                return not self._execution_branch_can_write_locked(record, ownership_epoch)

        return _handle

    def _sync_local_execution_control_locked(self, run_id: str) -> None:
        control = self._local_execution_controls.get(run_id)
        record = self._runs.get(run_id)
        if control is None or record is None:
            return
        if record.run.state in {RunState.COMPLETED, RunState.FAILED}:
            ownership = record.ownership
            if (
                ownership is not None
                and ownership.owner_instance_id == self.instance_id
                and ownership.ownership_epoch == control.ownership_epoch
                and record.report is None
                and record.error is None
            ):
                return
            self._cancel_local_execution_locked(run_id)
            return
        ownership = record.ownership
        if ownership is None:
            return
        if (
            ownership.owner_instance_id == self.instance_id
            and ownership.ownership_epoch == control.ownership_epoch
        ):
            return
        self._cancel_local_execution_locked(run_id)

    def _cancel_local_execution_locked(self, run_id: str) -> None:
        control = self._local_execution_controls.get(run_id)
        if control is None:
            return
        control.cancel_event.set()
        control.lease_stop_event.set()

    def _resume_claimed_run(self, run_id: str, ownership_epoch: int) -> None:
        with self._lock:
            self._sync_record_from_snapshot_locked(run_id)
            record = self._runs.get(run_id)
            if record is None or not self._can_auto_resume_locked(record):
                return
            if not self._execution_branch_can_write_locked(record, ownership_epoch):
                return
            request = record.request
            checkpoint = record.checkpoint.model_copy(deep=True) if record.checkpoint is not None else None
            llm_config = request.llm.model_copy(deep=True) if request is not None and request.llm is not None else None
            file_path = Path(request.file_path)
            stage = request.stage
            discipline = request.discipline

        reviewer = self.reviewer_builder(
            llm_config,
            run_update_hook=self._build_run_update_hook(
                run_id,
                ownership_epoch=ownership_epoch,
            ),
            worker_checkpoint_hook=self._build_worker_checkpoint_hook(
                run_id,
                ownership_epoch=ownership_epoch,
            ),
            cancel_check=self._build_cancel_check(
                run_id,
                ownership_epoch=ownership_epoch,
            ),
        )
        with self._lock:
            control = self._local_execution_controls.setdefault(run_id, _LocalExecutionControl())
            control.cancel_event.clear()
            control.lease_stop_event.clear()
            control.ownership_epoch = ownership_epoch
            lease_stop_event = control.lease_stop_event
        lease_thread = Thread(
            target=self._renew_run_lease_until_stopped,
            args=(run_id, ownership_epoch, lease_stop_event),
            daemon=True,
        )
        lease_thread.start()
        try:
            report = reviewer.review_docx(
                file_path,
                stage=stage,
                discipline=discipline,
                checkpoint=checkpoint,
                run_id=run_id,
            )
            trace = self.trace_builder(reviewer)
            with self._lock:
                self._sync_record_from_snapshot_locked(run_id)
                record = self._runs.get(run_id)
                if record is None or not self._execution_branch_can_write_locked(record, ownership_epoch):
                    return
                if reviewer.last_review_run is not None:
                    record.run = reviewer.last_review_run.model_copy(deep=True)
                record.report = report.model_copy(deep=True)
                record.trace = trace.model_copy(deep=True)
                record.error = None
                record.ownership = self._released_ownership(
                    ownership_epoch=ownership_epoch,
                )
                self._append_event_locked(run_id, "resumed_completed", record.run)
                self._persist_record_locked(run_id)
        except ReviewRunCancelledError:
            return
        except Exception as error:  # pragma: no cover - integration behavior
            mapped_error = self.error_mapper(error)
            trace = self.trace_builder(reviewer)
            with self._lock:
                self._sync_record_from_snapshot_locked(run_id)
                record = self._runs.get(run_id)
                if record is None or not self._execution_branch_can_write_locked(record, ownership_epoch):
                    return
                if reviewer.last_review_run is not None:
                    record.run = reviewer.last_review_run.model_copy(deep=True)
                else:
                    record.run.state = RunState.FAILED
                record.trace = trace.model_copy(deep=True)
                record.error = mapped_error
                record.ownership = self._released_ownership(
                    ownership_epoch=ownership_epoch,
                )
                self._append_event_locked(run_id, "resumed_failed", record.run)
                self._persist_record_locked(run_id)
        finally:
            lease_stop_event.set()
            lease_thread.join(timeout=max(self.lease_seconds, 0.1))
            with self._lock:
                self._clear_local_execution_control_locked(run_id, ownership_epoch=ownership_epoch)

    def _active_ownership(
        self,
        timestamp=None,
        *,
        ownership_epoch: int,
    ) -> ReviewRunOwnershipSnapshot:
        now = timestamp or utc_now()
        return ReviewRunOwnershipSnapshot(
            owner_instance_id=self.instance_id,
            ownership_epoch=ownership_epoch,
            lease_expires_at=now + timedelta(seconds=self.lease_seconds),
            last_heartbeat_at=now,
        )

    def _released_ownership(
        self,
        timestamp=None,
        *,
        ownership_epoch: int,
    ) -> ReviewRunOwnershipSnapshot:
        now = timestamp or utc_now()
        return ReviewRunOwnershipSnapshot(
            owner_instance_id=self.instance_id,
            ownership_epoch=ownership_epoch,
            lease_expires_at=None,
            last_heartbeat_at=now,
        )

    def _materialize_public_ownership(
        self,
        ownership: ReviewRunOwnershipSnapshot | None,
        *,
        run_state: RunState,
    ) -> ReviewRunOwnership | None:
        if ownership is None:
            return None
        lease_active = (
            ownership.lease_expires_at is not None
            and ownership.lease_expires_at > utc_now()
        )
        stale_lease = ownership.lease_expires_at is not None and not lease_active
        owned_by_current_instance = ownership.owner_instance_id == self.instance_id
        return ReviewRunOwnership(
            owner_instance_id=ownership.owner_instance_id,
            lease_expires_at=ownership.lease_expires_at,
            last_heartbeat_at=ownership.last_heartbeat_at,
            lease_active=lease_active,
            stale_lease=stale_lease,
            claimable=(
                run_state not in {RunState.COMPLETED, RunState.FAILED}
                and stale_lease
                and not owned_by_current_instance
            ),
            owned_by_current_instance=owned_by_current_instance,
        )

    def _build_request_snapshot(
        self,
        *,
        file_path: Path,
        stage: PaperStage,
        discipline: Discipline,
        llm_config: ReviewLLMConfig | None,
    ) -> ReviewRunRequestSnapshot:
        sanitized_llm_config = self._sanitize_llm_config_for_resume(llm_config)
        auto_resume_supported = file_path.exists() and sanitized_llm_config is not None
        auto_resume_reason = None if auto_resume_supported else self._build_auto_resume_reason(
            file_path=file_path,
            llm_config=llm_config,
        )
        return ReviewRunRequestSnapshot(
            file_path=str(file_path),
            stage=stage,
            discipline=discipline,
            llm=sanitized_llm_config,
            auto_resume_supported=auto_resume_supported,
            auto_resume_reason=auto_resume_reason,
        )

    def _sanitize_llm_config_for_resume(
        self,
        llm_config: ReviewLLMConfig | None,
    ) -> ReviewLLMConfig | None:
        if llm_config is None:
            return ReviewLLMConfig()
        if llm_config.api_key:
            return None
        return llm_config.model_copy(deep=True)

    def _build_auto_resume_reason(
        self,
        *,
        file_path: Path,
        llm_config: ReviewLLMConfig | None,
    ) -> str:
        if not file_path.exists():
            return "source_path_missing"
        if llm_config is not None and llm_config.api_key:
            return "request_scoped_api_key_not_persisted"
        return "resume_context_unavailable"

    def _can_auto_resume_locked(self, record: _RunRecord) -> bool:
        request = record.request
        if request is None:
            return False
        if not request.auto_resume_supported:
            return False
        if not Path(request.file_path).exists():
            return False
        return True

    def _auto_resume_reason_locked(self, record: _RunRecord) -> str:
        request = record.request
        if request is None:
            return "resume_request_missing"
        if request.auto_resume_supported:
            return "resume_not_started"
        return request.auto_resume_reason or "resume_not_supported"

    def _current_instance_can_write_locked(self, record: _RunRecord) -> bool:
        ownership = record.ownership
        if ownership is None:
            return True
        if ownership.owner_instance_id == self.instance_id:
            return True
        return ownership.lease_expires_at is None or ownership.lease_expires_at <= utc_now()

    def _execution_branch_can_write_locked(
        self,
        record: _RunRecord,
        ownership_epoch: int,
    ) -> bool:
        ownership = record.ownership
        if ownership is None:
            return False
        return (
            ownership.owner_instance_id == self.instance_id
            and ownership.ownership_epoch == ownership_epoch
        )

    def _next_ownership_epoch(self, record: _RunRecord) -> int:
        if record.ownership is None:
            return 1
        return record.ownership.ownership_epoch + 1

    def _clear_local_execution_control_locked(self, run_id: str, *, ownership_epoch: int) -> None:
        control = self._local_execution_controls.get(run_id)
        if control is None:
            return
        if control.ownership_epoch != ownership_epoch:
            return
        self._local_execution_controls.pop(run_id, None)
