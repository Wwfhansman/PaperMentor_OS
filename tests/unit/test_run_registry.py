from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

from papermentor_os.api.run_registry import InMemoryReviewRunRegistry, ReviewRunClaimError
from papermentor_os.llm import ReviewLLMConfig
from papermentor_os.orchestrator.checkpoint import ReviewCheckpoint
from papermentor_os.orchestrator.run_state import ReviewRun, RunState, WorkerRun, utc_now
from papermentor_os.schemas.paper import PaperPackage
from papermentor_os.schemas.report import AdvisorView, DimensionReport, FinalReport, StudentGuidance
from papermentor_os.schemas.run import ReviewRunError
from papermentor_os.schemas.trace import OrchestrationTrace, ReviewTrace
from papermentor_os.schemas.types import Dimension, Discipline, PaperStage


class _FakeParser:
    def parse_file(
        self,
        file_path: str | Path,
        *,
        stage: PaperStage = PaperStage.DRAFT,
        discipline: Discipline = Discipline.COMPUTER_SCIENCE,
    ) -> PaperPackage:
        return PaperPackage(
            paper_id="paper-1",
            title="Registry fencing test",
            abstract="abstract",
            stage=stage,
            discipline=discipline,
            source_path=str(file_path),
        )


class _BlockingReviewer:
    def __init__(
        self,
        *,
        report_label: str,
        worker_id: str = "TopicScopeAgent",
        started_event: Event | None = None,
        finish_event: Event | None = None,
        run_update_hook=None,
        worker_checkpoint_hook=None,
        cancel_check=None,
    ) -> None:
        self.parser = _FakeParser()
        self.report_label = report_label
        self.worker_id = worker_id
        self.started_event = started_event
        self.finish_event = finish_event
        self.run_update_hook = run_update_hook
        self.worker_checkpoint_hook = worker_checkpoint_hook
        self.cancel_check = cancel_check
        self.last_review_run: ReviewRun | None = None
        self.trace = ReviewTrace()

    def worker_ids(self) -> list[str]:
        return [self.worker_id]

    def worker_dimensions(self) -> dict[str, Dimension]:
        return {self.worker_id: Dimension.TOPIC_SCOPE}

    def review_docx(
        self,
        file_path: str | Path,
        *,
        stage: PaperStage = PaperStage.DRAFT,
        discipline: Discipline = Discipline.COMPUTER_SCIENCE,
        checkpoint: ReviewCheckpoint | None = None,
        run_id: str | None = None,
    ) -> FinalReport:
        paper = self.parser.parse_file(file_path, stage=stage, discipline=discipline)
        return self.review_paper(paper, checkpoint=checkpoint, run_id=run_id)

    def review_paper(
        self,
        paper: PaperPackage,
        *,
        checkpoint: ReviewCheckpoint | None = None,
        run_id: str | None = None,
    ) -> FinalReport:
        started_at = utc_now()
        self.last_review_run = self._build_run(
            run_id=run_id or "missing-run-id",
            paper=paper,
            state=RunState.RUNNING,
            started_at=started_at,
            finished_at=None,
            resumed_from_checkpoint=checkpoint is not None,
            checkpoint_completed_worker_count=len(checkpoint.completed_workers) if checkpoint is not None else 0,
        )
        if self.run_update_hook is not None:
            self.run_update_hook(self.last_review_run)
        if self.started_event is not None:
            self.started_event.set()
        if self.finish_event is not None:
            assert self.finish_event.wait(timeout=3.0)

        report = _build_report(self.report_label)
        finished_at = utc_now()
        self.last_review_run = self._build_run(
            run_id=run_id or "missing-run-id",
            paper=paper,
            state=RunState.COMPLETED,
            started_at=started_at,
            finished_at=finished_at,
            resumed_from_checkpoint=checkpoint is not None,
            checkpoint_completed_worker_count=len(checkpoint.completed_workers) if checkpoint is not None else 0,
            report=report,
        )
        self.trace = ReviewTrace(
            orchestration=OrchestrationTrace(
                stage=paper.stage,
                discipline=paper.discipline,
                worker_sequence=[self.worker_id],
                resumed_from_checkpoint=checkpoint is not None,
                checkpoint_completed_worker_count=len(checkpoint.completed_workers) if checkpoint is not None else 0,
                resumed_worker_ids=checkpoint.worker_ids() if checkpoint is not None else [],
                skipped_worker_ids=checkpoint.worker_ids() if checkpoint is not None else [],
                resume_start_worker_id=None,
                total_findings=len(report.dimension_reports[0].findings),
                debate_candidate_dimensions=[],
                debated_dimensions=[],
                debate_judge_skill_version=None,
            )
        )
        return report

    def _build_run(
        self,
        *,
        run_id: str,
        paper: PaperPackage,
        state: RunState,
        started_at,
        finished_at,
        resumed_from_checkpoint: bool,
        checkpoint_completed_worker_count: int,
        report: FinalReport | None = None,
    ) -> ReviewRun:
        worker_run = WorkerRun(
            worker_id=self.worker_id,
            dimension=Dimension.TOPIC_SCOPE,
            state=state,
            score=report.dimension_reports[0].score if report is not None else None,
            finding_count=len(report.dimension_reports[0].findings) if report is not None else 0,
            summary=report.dimension_reports[0].summary if report is not None else None,
            started_at=started_at,
            finished_at=finished_at,
        )
        return ReviewRun(
            run_id=run_id,
            paper_id=paper.paper_id,
            stage=paper.stage,
            discipline=paper.discipline,
            state=state,
            worker_sequence=[self.worker_id],
            selected_worker_ids=[self.worker_id],
            worker_runs=[worker_run],
            resumed_from_checkpoint=resumed_from_checkpoint,
            checkpoint_completed_worker_count=checkpoint_completed_worker_count,
            completed_worker_count=1 if state == RunState.COMPLETED else 0,
            started_at=started_at,
            updated_at=finished_at or started_at,
            finished_at=finished_at,
        )


def _build_report(label: str) -> FinalReport:
    return FinalReport(
        overall_summary=f"{label} summary",
        dimension_reports=[
            DimensionReport(
                dimension=Dimension.TOPIC_SCOPE,
                score=7.5,
                summary=f"{label} dimension summary",
                findings=[],
                debate_used=False,
            )
        ],
        priority_actions=[],
        student_guidance=StudentGuidance(next_steps=[]),
        advisor_view=AdvisorView(quick_summary=f"{label} advisor view", watch_points=[]),
        safety_notice=f"{label} safety notice",
    )


def _build_registry(
    *,
    snapshot_dir: Path,
    instance_id: str,
    report_label: str,
    started_event: Event | None = None,
    finish_event: Event | None = None,
    reviewer_builder=None,
    trace_builder=None,
    server_resume_llm_config=None,
) -> InMemoryReviewRunRegistry:
    return InMemoryReviewRunRegistry(
        reviewer_builder=reviewer_builder
        or (lambda llm_config=None, **kwargs: _BlockingReviewer(
            report_label=report_label,
            started_event=started_event,
            finish_event=finish_event,
            **kwargs,
        )),
        trace_builder=trace_builder or (lambda reviewer: reviewer.trace),
        error_mapper=lambda error: ReviewRunError(code="unexpected_error", message=str(error)),
        snapshot_dir=snapshot_dir,
        instance_id=instance_id,
        lease_seconds=0.1,
        server_resume_llm_config=server_resume_llm_config,
    )


def _wait_for_terminal(
    registry: InMemoryReviewRunRegistry,
    run_id: str,
    *,
    timeout_seconds: float = 3.0,
):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        payload = registry.get_run(run_id)
        assert payload is not None
        if payload.run.state in {RunState.COMPLETED, RunState.FAILED}:
            return payload
        time.sleep(0.02)
    raise AssertionError(f"review run {run_id} did not complete within {timeout_seconds} seconds")


def test_old_baseline_execution_cannot_overwrite_new_owner_terminal_result(tmp_path: Path, monkeypatch) -> None:
    snapshot_dir = tmp_path / "run-snapshots"
    file_path = tmp_path / "paper.docx"
    file_path.write_bytes(b"docx")
    primary_started = Event()
    primary_finish = Event()

    def _no_lease_renewal(self, run_id, ownership_epoch, ownership_token, stop_event):
        stop_event.wait(timeout=1.0)

    monkeypatch.setattr(
        InMemoryReviewRunRegistry,
        "_renew_run_lease_until_stopped",
        _no_lease_renewal,
    )

    primary_registry = _build_registry(
        snapshot_dir=snapshot_dir,
        instance_id="primary-instance",
        report_label="primary",
        started_event=primary_started,
        finish_event=primary_finish,
    )
    secondary_registry = _build_registry(
        snapshot_dir=snapshot_dir,
        instance_id="secondary-instance",
        report_label="secondary",
    )

    try:
        accepted = primary_registry.submit_docx(
            file_path=file_path,
            stage=PaperStage.DRAFT,
            discipline=Discipline.COMPUTER_SCIENCE,
            llm_config=None,
        )
        assert primary_started.wait(timeout=1.0) is True
        time.sleep(0.14)

        claim_response = secondary_registry.claim_run(accepted.run_id)
        assert claim_response is not None
        assert claim_response.claimed is True
        assert claim_response.resume_started is True

        completed_payload = _wait_for_terminal(secondary_registry, accepted.run_id)
        assert completed_payload.report is not None
        assert completed_payload.report.overall_summary == "secondary summary"

        primary_finish.set()
        time.sleep(0.15)

        final_payload = secondary_registry.get_run(accepted.run_id)
        assert final_payload is not None
        assert final_payload.report is not None
        assert final_payload.report.overall_summary == "secondary summary"
        assert final_payload.trace is not None
        assert final_payload.trace.orchestration is not None
        assert final_payload.trace.orchestration.resumed_from_checkpoint is True
        events_payload = secondary_registry.get_events(accepted.run_id)
        assert events_payload is not None
        event_types = [event.event_type for event in events_payload.events]
        assert event_types.count("resumed_completed") == 1
        assert "completed" not in event_types
    finally:
        primary_finish.set()
        primary_registry.close()
        secondary_registry.close()


def test_old_resumed_execution_cannot_overwrite_newer_owner_terminal_result(tmp_path: Path, monkeypatch) -> None:
    snapshot_dir = tmp_path / "run-snapshots"
    file_path = tmp_path / "paper.docx"
    file_path.write_bytes(b"docx")
    primary_started = Event()
    primary_finish = Event()
    secondary_started = Event()
    secondary_finish = Event()

    def _no_lease_renewal(self, run_id, ownership_epoch, ownership_token, stop_event):
        stop_event.wait(timeout=1.0)

    monkeypatch.setattr(
        InMemoryReviewRunRegistry,
        "_renew_run_lease_until_stopped",
        _no_lease_renewal,
    )

    primary_registry = _build_registry(
        snapshot_dir=snapshot_dir,
        instance_id="primary-instance",
        report_label="primary",
        started_event=primary_started,
        finish_event=primary_finish,
    )
    secondary_registry = _build_registry(
        snapshot_dir=snapshot_dir,
        instance_id="secondary-instance",
        report_label="secondary",
        started_event=secondary_started,
        finish_event=secondary_finish,
    )
    tertiary_registry = _build_registry(
        snapshot_dir=snapshot_dir,
        instance_id="tertiary-instance",
        report_label="tertiary",
    )

    try:
        accepted = primary_registry.submit_docx(
            file_path=file_path,
            stage=PaperStage.DRAFT,
            discipline=Discipline.COMPUTER_SCIENCE,
            llm_config=None,
        )
        assert primary_started.wait(timeout=1.0) is True
        time.sleep(0.14)

        first_claim = secondary_registry.claim_run(accepted.run_id)
        assert first_claim is not None
        assert first_claim.claimed is True
        assert first_claim.resume_started is True
        assert secondary_started.wait(timeout=1.0) is True

        primary_finish.set()
        time.sleep(0.05)
        time.sleep(0.14)

        second_claim = tertiary_registry.claim_run(accepted.run_id)
        assert second_claim is not None
        assert second_claim.claimed is True
        assert second_claim.resume_started is True

        completed_payload = _wait_for_terminal(tertiary_registry, accepted.run_id)
        assert completed_payload.report is not None
        assert completed_payload.report.overall_summary == "tertiary summary"

        secondary_finish.set()
        time.sleep(0.15)

        final_payload = tertiary_registry.get_run(accepted.run_id)
        assert final_payload is not None
        assert final_payload.report is not None
        assert final_payload.report.overall_summary == "tertiary summary"
        assert final_payload.trace is not None
        assert final_payload.trace.orchestration is not None
        assert final_payload.trace.orchestration.resumed_from_checkpoint is True
        events_payload = tertiary_registry.get_events(accepted.run_id)
        assert events_payload is not None
        event_types = [event.event_type for event in events_payload.events]
        assert event_types.count("ownership_claimed") == 2
        assert event_types.count("resumed_completed") == 1
        assert "completed" not in event_types
    finally:
        primary_finish.set()
        secondary_finish.set()
        primary_registry.close()
        secondary_registry.close()
        tertiary_registry.close()


def test_concurrent_cross_instance_claim_allows_only_one_winner(
    tmp_path: Path,
    monkeypatch,
) -> None:
    snapshot_dir = tmp_path / "run-snapshots"
    file_path = tmp_path / "paper.docx"
    file_path.write_bytes(b"docx")
    primary_started = Event()
    primary_finish = Event()

    def _no_lease_renewal(self, run_id, ownership_epoch, ownership_token, stop_event):
        stop_event.wait(timeout=1.0)

    monkeypatch.setattr(
        InMemoryReviewRunRegistry,
        "_renew_run_lease_until_stopped",
        _no_lease_renewal,
    )

    primary_registry = _build_registry(
        snapshot_dir=snapshot_dir,
        instance_id="primary-instance",
        report_label="primary",
        started_event=primary_started,
        finish_event=primary_finish,
    )
    secondary_registry = _build_registry(
        snapshot_dir=snapshot_dir,
        instance_id="secondary-instance",
        report_label="secondary",
    )
    tertiary_registry = _build_registry(
        snapshot_dir=snapshot_dir,
        instance_id="tertiary-instance",
        report_label="tertiary",
    )

    try:
        accepted = primary_registry.submit_docx(
            file_path=file_path,
            stage=PaperStage.DRAFT,
            discipline=Discipline.COMPUTER_SCIENCE,
            llm_config=None,
        )
        assert primary_started.wait(timeout=1.0) is True
        time.sleep(0.14)

        def _claim(registry: InMemoryReviewRunRegistry) -> tuple[str, str]:
            try:
                response = registry.claim_run(accepted.run_id)
            except ReviewRunClaimError as error:
                return ("error", error.code)
            assert response is not None
            return ("claimed", str(response.claimed))

        with ThreadPoolExecutor(max_workers=2) as executor:
            secondary_future = executor.submit(_claim, secondary_registry)
            tertiary_future = executor.submit(_claim, tertiary_registry)
            results = [secondary_future.result(timeout=2.0), tertiary_future.result(timeout=2.0)]

        assert results.count(("claimed", "True")) == 1
        assert results.count(("error", "active_foreign_lease")) == 1

        winning_registry = secondary_registry if results[0] == ("claimed", "True") else tertiary_registry
        completed_payload = _wait_for_terminal(winning_registry, accepted.run_id)
        assert completed_payload.report is not None
        assert completed_payload.report.overall_summary in {"secondary summary", "tertiary summary"}
    finally:
        primary_finish.set()
        primary_registry.close()
        secondary_registry.close()
        tertiary_registry.close()


def test_claimed_resume_builder_failure_marks_run_failed_and_releases_ownership(
    tmp_path: Path,
    monkeypatch,
) -> None:
    snapshot_dir = tmp_path / "run-snapshots"
    file_path = tmp_path / "paper.docx"
    file_path.write_bytes(b"docx")
    primary_started = Event()
    primary_finish = Event()

    def _no_lease_renewal(self, run_id, ownership_epoch, ownership_token, stop_event):
        stop_event.wait(timeout=1.0)

    monkeypatch.setattr(
        InMemoryReviewRunRegistry,
        "_renew_run_lease_until_stopped",
        _no_lease_renewal,
    )

    primary_registry = _build_registry(
        snapshot_dir=snapshot_dir,
        instance_id="primary-instance",
        report_label="primary",
        started_event=primary_started,
        finish_event=primary_finish,
    )
    secondary_registry = _build_registry(
        snapshot_dir=snapshot_dir,
        instance_id="secondary-instance",
        report_label="secondary",
        reviewer_builder=lambda llm_config=None, **kwargs: (_ for _ in ()).throw(
            RuntimeError("resume builder failed")
        ),
    )

    try:
        accepted = primary_registry.submit_docx(
            file_path=file_path,
            stage=PaperStage.DRAFT,
            discipline=Discipline.COMPUTER_SCIENCE,
            llm_config=None,
        )
        assert primary_started.wait(timeout=1.0) is True
        time.sleep(0.14)

        claim_response = secondary_registry.claim_run(accepted.run_id)
        assert claim_response is not None
        assert claim_response.claimed is True
        assert claim_response.resume_started is True

        failed_payload = _wait_for_terminal(secondary_registry, accepted.run_id)
        assert failed_payload.run.state == RunState.FAILED
        assert failed_payload.error is not None
        assert failed_payload.error.code == "unexpected_error"
        assert failed_payload.error.message == "resume builder failed"
        assert failed_payload.ownership is not None
        assert failed_payload.ownership.owner_instance_id == "secondary-instance"
        assert failed_payload.ownership.lease_active is False
        assert failed_payload.trace is not None
        events_payload = secondary_registry.get_events(accepted.run_id)
        assert events_payload is not None
        event_types = [event.event_type for event in events_payload.events]
        assert "ownership_claimed" in event_types
        assert "resumed_failed" in event_types
    finally:
        primary_finish.set()
        primary_registry.close()
        secondary_registry.close()


def test_request_scoped_llm_can_auto_resume_with_server_resume_config(
    tmp_path: Path,
    monkeypatch,
) -> None:
    snapshot_dir = tmp_path / "run-snapshots"
    file_path = tmp_path / "paper.docx"
    file_path.write_bytes(b"docx")
    primary_started = Event()
    primary_finish = Event()
    server_resume_llm_config = ReviewLLMConfig(
        review_backend="model_with_fallback",
        base_url="https://server.example.com/v1",
        api_key="sk-server",
        model_name="server-model",
    )
    request_llm_config = ReviewLLMConfig(
        review_backend="model_with_fallback",
        base_url="https://request.example.com/v1",
        api_key="sk-request",
        model_name="request-model",
        temperature=0.2,
        max_tokens=900,
    )

    def _no_lease_renewal(self, run_id, ownership_epoch, ownership_token, stop_event):
        stop_event.wait(timeout=1.0)

    monkeypatch.setattr(
        InMemoryReviewRunRegistry,
        "_renew_run_lease_until_stopped",
        _no_lease_renewal,
    )

    primary_registry = _build_registry(
        snapshot_dir=snapshot_dir,
        instance_id="primary-instance",
        report_label="primary",
        started_event=primary_started,
        finish_event=primary_finish,
        server_resume_llm_config=server_resume_llm_config,
    )
    secondary_registry = _build_registry(
        snapshot_dir=snapshot_dir,
        instance_id="secondary-instance",
        report_label="secondary",
        server_resume_llm_config=server_resume_llm_config,
    )

    try:
        accepted = primary_registry.submit_docx(
            file_path=file_path,
            stage=PaperStage.DRAFT,
            discipline=Discipline.COMPUTER_SCIENCE,
            llm_config=request_llm_config,
        )
        assert primary_started.wait(timeout=1.0) is True
        time.sleep(0.14)

        claim_response = secondary_registry.claim_run(accepted.run_id)
        assert claim_response is not None
        assert claim_response.claimed is True
        assert claim_response.resume_started is True
        assert claim_response.resume_reason == "resumed_from_source_with_checkpoint"

        completed_payload = _wait_for_terminal(secondary_registry, accepted.run_id)
        assert completed_payload.run.state == RunState.COMPLETED
        assert completed_payload.report is not None
        assert completed_payload.report.overall_summary == "secondary summary"
        assert completed_payload.trace is not None
        assert completed_payload.trace.orchestration is not None
        assert completed_payload.trace.orchestration.resumed_from_checkpoint is True

        with secondary_registry._lock:
            request_snapshot = secondary_registry._runs[accepted.run_id].request
            assert request_snapshot is not None
            assert request_snapshot.resume_uses_server_llm_credentials is True
            assert request_snapshot.llm is not None
            assert request_snapshot.llm.api_key is None
            assert request_snapshot.llm.base_url == "https://request.example.com/v1"
            assert request_snapshot.llm.model_name == "request-model"
    finally:
        primary_finish.set()
        primary_registry.close()
        secondary_registry.close()


def test_trace_builder_failure_falls_back_to_empty_trace_without_failing_run(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "run-snapshots"
    file_path = tmp_path / "paper.docx"
    file_path.write_bytes(b"docx")

    registry = _build_registry(
        snapshot_dir=snapshot_dir,
        instance_id="primary-instance",
        report_label="primary",
        trace_builder=lambda reviewer: (_ for _ in ()).throw(RuntimeError("trace builder failed")),
    )

    try:
        accepted = registry.submit_docx(
            file_path=file_path,
            stage=PaperStage.DRAFT,
            discipline=Discipline.COMPUTER_SCIENCE,
            llm_config=None,
        )

        completed_payload = _wait_for_terminal(registry, accepted.run_id)
        assert completed_payload.run.state == RunState.COMPLETED
        assert completed_payload.report is not None
        assert completed_payload.error is None
        assert completed_payload.trace is not None
        assert completed_payload.trace.orchestration is None
        events_payload = registry.get_events(accepted.run_id)
        assert events_payload is not None
        assert any(event.event_type == "completed" for event in events_payload.events)
    finally:
        registry.close()
