from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from threading import Lock
import time
from uuid import uuid4
from collections.abc import Callable, Mapping
from pathlib import Path

from papermentor_os.agents.base import BaseReviewAgent
from papermentor_os.agents.debate_judge import DebateJudgeAgent
from papermentor_os.agents.literature_support import LiteratureSupportAgent
from papermentor_os.agents.logic_chain import LogicChainAgent
from papermentor_os.agents.novelty_depth import NoveltyDepthAgent
from papermentor_os.agents.topic_scope import TopicScopeAgent
from papermentor_os.agents.writing_format import WritingFormatAgent
from papermentor_os.ledger.evidence_ledger import EvidenceLedger
from papermentor_os.orchestrator.checkpoint import ReviewCheckpoint, WorkerCheckpoint
from papermentor_os.orchestrator.disagreement import DisagreementDetector
from papermentor_os.orchestrator.run_state import ReviewRun, RunState, WorkerRun, utc_now
from papermentor_os.parsers.docx_parser import DocxPaperParser
from papermentor_os.reporting.composer import GuidanceComposer
from papermentor_os.schemas.debate import DebateCase, DebateResolution
from papermentor_os.schemas.paper import PaperPackage
from papermentor_os.schemas.report import DimensionReport, FinalReport
from papermentor_os.schemas.trace import (
    DebateResolutionTrace,
    OrchestrationTrace,
    WorkerExecutionMetadata,
    WorkerExecutionTrace,
    WorkerSkillTrace,
)
from papermentor_os.schemas.types import Dimension, Discipline, PaperStage, Severity
from papermentor_os.runtime import WorkerRunPolicy
from papermentor_os.skills.loader import SkillBundle, SkillLoader


@dataclass(slots=True)
class _WorkerReviewResult:
    worker_id: str
    report: DimensionReport
    execution_metadata: WorkerExecutionMetadata
    skill_trace: WorkerSkillTrace
    status: RunState
    from_checkpoint: bool = False


class ReviewRunCancelledError(RuntimeError):
    """Raised when a locally executing review run loses ownership and should stop."""


class ChiefReviewer:
    """Deterministic orchestrator for the current MVP review pipeline."""

    def __init__(
        self,
        parser: DocxPaperParser | None = None,
        literature_support_agent: LiteratureSupportAgent | None = None,
        logic_chain_agent: LogicChainAgent | None = None,
        novelty_depth_agent: NoveltyDepthAgent | None = None,
        topic_scope_agent: TopicScopeAgent | None = None,
        writing_format_agent: WritingFormatAgent | None = None,
        debate_judge_agent: DebateJudgeAgent | None = None,
        skill_loader: SkillLoader | None = None,
        disagreement_detector: DisagreementDetector | None = None,
        composer: GuidanceComposer | None = None,
        worker_run_policies: Mapping[str, WorkerRunPolicy] | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        run_update_hook: Callable[[ReviewRun], None] | None = None,
        worker_checkpoint_hook: Callable[[WorkerCheckpoint], None] | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> None:
        self.parser = parser or DocxPaperParser()
        self.literature_support_agent = literature_support_agent or LiteratureSupportAgent()
        self.logic_chain_agent = logic_chain_agent or LogicChainAgent()
        self.novelty_depth_agent = novelty_depth_agent or NoveltyDepthAgent()
        self.topic_scope_agent = topic_scope_agent or TopicScopeAgent()
        self.writing_format_agent = writing_format_agent or WritingFormatAgent()
        self.debate_judge_agent = debate_judge_agent or DebateJudgeAgent()
        self.skill_loader = skill_loader or SkillLoader(Path(__file__).resolve().parents[3] / "skills")
        self.disagreement_detector = disagreement_detector or DisagreementDetector()
        self.composer = composer or GuidanceComposer()
        self.worker_run_policies = dict(worker_run_policies or {})
        self.sleep_fn = sleep_fn or time.sleep
        self.last_debate_candidates: list[DebateCase] = []
        self.last_debate_resolutions: list[DebateResolution] = []
        self.last_debate_resolution_traces: list[DebateResolutionTrace] = []
        self.last_worker_skill_traces: list[WorkerSkillTrace] = []
        self.last_worker_execution_traces: list[WorkerExecutionTrace] = []
        self.last_orchestration_trace: OrchestrationTrace | None = None
        self.last_worker_run_states: dict[str, str] = {}
        self.last_review_run: ReviewRun | None = None
        self._worker_run_state_lock = Lock()
        self.run_update_hook = run_update_hook
        self.worker_checkpoint_hook = worker_checkpoint_hook
        self.cancel_check = cancel_check

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
        self._raise_if_cancelled()
        pipeline_state = self._run_worker_pipeline(paper, checkpoint=checkpoint, run_id=run_id)
        ledger = pipeline_state["ledger"]
        reports = pipeline_state["reports"]
        worker_agents = pipeline_state["worker_agents"]
        checkpoint_trace = pipeline_state["checkpoint_trace"]

        self._raise_if_cancelled()
        self.last_debate_candidates = self.disagreement_detector.detect(reports)
        self._raise_if_cancelled()
        self.last_debate_resolutions, self.last_debate_resolution_traces = self._run_selective_debate(
            ledger,
            reports,
        )
        self._raise_if_cancelled()
        self.last_worker_execution_traces = self._build_worker_execution_traces(ledger, reports)
        self.last_orchestration_trace = OrchestrationTrace(
            stage=paper.stage,
            discipline=paper.discipline,
            worker_sequence=[agent.agent_name for agent in worker_agents],
            resumed_from_checkpoint=checkpoint_trace["resumed_from_checkpoint"],
            checkpoint_completed_worker_count=checkpoint_trace["checkpoint_completed_worker_count"],
            resumed_worker_ids=checkpoint_trace["resumed_worker_ids"],
            skipped_worker_ids=checkpoint_trace["skipped_worker_ids"],
            resume_start_worker_id=checkpoint_trace["resume_start_worker_id"],
            total_findings=sum(len(report.findings) for report in reports),
            debate_candidate_dimensions=[candidate.dimension for candidate in self.last_debate_candidates],
            debated_dimensions=[resolution.dimension for resolution in self.last_debate_resolutions],
            debate_judge_skill_version=(
                self.last_debate_resolutions[0].source_skill_version
                if self.last_debate_resolutions
                else None
            ),
        )
        return self.composer.compose(paper, ledger)

    def run_review_until(
        self,
        paper: PaperPackage,
        *,
        stop_after_worker_id: str,
        checkpoint: ReviewCheckpoint | None = None,
        run_id: str | None = None,
    ) -> ReviewCheckpoint:
        pipeline_state = self._run_worker_pipeline(
            paper,
            checkpoint=checkpoint,
            stop_after_worker_id=stop_after_worker_id,
            run_id=run_id,
        )
        return pipeline_state["checkpoint"]

    def run_worker_smoke(
        self,
        file_path: str | Path,
        worker_id: str,
        *,
        stage: PaperStage = PaperStage.DRAFT,
        discipline: Discipline = Discipline.COMPUTER_SCIENCE,
    ) -> tuple[DimensionReport, WorkerExecutionTrace]:
        paper = self.parser.parse_file(file_path, stage=stage, discipline=discipline)
        worker_agent = self._worker_agent_by_id(worker_id)
        skill_context = {
            "discipline": paper.discipline.value,
            "stage": paper.stage.value,
        }
        self._reset_last_run_state()
        worker_result = self._review_worker(
            worker_agent,
            paper,
            skill_context=skill_context,
            manage_run_state=False,
            emit_checkpoint=False,
        )
        worker_trace = self._build_worker_execution_trace(
            worker_result.report,
            worker_result.execution_metadata,
        )
        self.last_worker_skill_traces = [worker_result.skill_trace]
        self.last_worker_execution_traces = [worker_trace]
        self.last_orchestration_trace = OrchestrationTrace(
            stage=paper.stage,
            discipline=paper.discipline,
            worker_sequence=[worker_agent.agent_name],
            resumed_from_checkpoint=False,
            checkpoint_completed_worker_count=0,
            resumed_worker_ids=[],
            skipped_worker_ids=[],
            resume_start_worker_id=None,
            total_findings=len(worker_result.report.findings),
            debate_candidate_dimensions=[],
            debated_dimensions=[],
            debate_judge_skill_version=None,
        )
        return worker_result.report, worker_trace

    def _run_worker_pipeline(
        self,
        paper: PaperPackage,
        *,
        checkpoint: ReviewCheckpoint | None = None,
        stop_after_worker_id: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, object]:
        self._reset_last_run_state()
        self._validate_checkpoint(paper, checkpoint)
        self._raise_if_cancelled()

        ledger = EvidenceLedger()
        skill_context = {
            "discipline": paper.discipline.value,
            "stage": paper.stage.value,
        }
        resumed_checkpoint = checkpoint.model_copy(deep=True) if checkpoint is not None else ReviewCheckpoint(
            paper_id=paper.paper_id,
            stage=paper.stage,
            discipline=paper.discipline,
        )
        resumed_worker_ids = checkpoint.worker_ids() if checkpoint is not None else []

        self.last_debate_candidates = []
        self.last_debate_resolutions = []
        self.last_debate_resolution_traces = []
        self.last_worker_skill_traces = []
        self.last_worker_execution_traces = []
        self.last_orchestration_trace = None

        worker_agents = self._worker_agents()
        selected_worker_agents = worker_agents[
            : self._resolve_stop_after_index(worker_agents, stop_after_worker_id) + 1
        ]
        self.last_review_run = self._build_review_run(
            paper,
            worker_agents,
            selected_worker_agents,
            resumed_worker_ids=resumed_worker_ids,
            stop_after_worker_id=stop_after_worker_id,
            run_id=run_id,
        )
        self._sync_worker_run_state_map()
        self._emit_review_run_update()

        try:
            worker_results: dict[str, _WorkerReviewResult] = {}
            pending_worker_agents: list[BaseReviewAgent] = []

            for worker_agent in selected_worker_agents:
                self._raise_if_cancelled()
                checkpoint_entry = resumed_checkpoint.get_worker(worker_agent.agent_name)
                if checkpoint_entry is not None:
                    worker_result = _WorkerReviewResult(
                        worker_id=worker_agent.agent_name,
                        report=checkpoint_entry.report,
                        execution_metadata=checkpoint_entry.execution_metadata,
                        skill_trace=checkpoint_entry.skill_trace,
                        status=self._status_from_execution_metadata(checkpoint_entry.execution_metadata),
                        from_checkpoint=True,
                    )
                    worker_results[worker_agent.agent_name] = worker_result
                    self._mark_worker_from_result(worker_result)
                    continue
                pending_worker_agents.append(worker_agent)

            worker_results.update(
                self._execute_workers_concurrently(
                    pending_worker_agents,
                    paper,
                    skill_context=skill_context,
                )
            )
            self._raise_if_cancelled()

            reports: list[DimensionReport] = []
            ordered_worker_results = [
                worker_results[worker_agent.agent_name]
                for worker_agent in selected_worker_agents
            ]
            self.last_worker_skill_traces = []
            for worker_result in ordered_worker_results:
                reports.append(worker_result.report)
                ledger.record_dimension_report(
                    worker_result.report,
                    execution_metadata=worker_result.execution_metadata,
                )
                self.last_worker_skill_traces.append(worker_result.skill_trace)
                if not worker_result.from_checkpoint:
                    resumed_checkpoint.completed_workers.append(
                        WorkerCheckpoint(
                            worker_id=worker_result.worker_id,
                            dimension=worker_result.report.dimension,
                            report=worker_result.report,
                            execution_metadata=worker_result.execution_metadata,
                            skill_trace=worker_result.skill_trace,
                        )
                    )
                    self._apply_worker_cooldown(
                        worker_result.worker_id,
                        worker_result.execution_metadata,
                    )

            self._set_review_run_state(RunState.COMPLETED)
            return {
                "ledger": ledger,
                "reports": reports,
                "worker_agents": worker_agents,
                "checkpoint": resumed_checkpoint,
                "checkpoint_trace": {
                    "resumed_from_checkpoint": bool(resumed_worker_ids),
                    "checkpoint_completed_worker_count": len(resumed_worker_ids),
                    "resumed_worker_ids": resumed_worker_ids,
                    "skipped_worker_ids": resumed_worker_ids,
                    "resume_start_worker_id": self._resolve_resume_start_worker_id(
                        worker_agents,
                        resumed_worker_ids,
                    ),
                },
            }
        except Exception:
            self._set_review_run_state(RunState.FAILED)
            raise

    def _reset_last_run_state(self) -> None:
        self.last_debate_candidates = []
        self.last_debate_resolutions = []
        self.last_debate_resolution_traces = []
        self.last_worker_skill_traces = []
        self.last_worker_execution_traces = []
        self.last_orchestration_trace = None
        self.last_worker_run_states = {}
        self.last_review_run = None

    def _validate_checkpoint(
        self,
        paper: PaperPackage,
        checkpoint: ReviewCheckpoint | None,
    ) -> None:
        if checkpoint is None:
            return
        if checkpoint.paper_id != paper.paper_id:
            raise ValueError("Review checkpoint paper_id does not match the input paper.")
        if checkpoint.stage != paper.stage:
            raise ValueError("Review checkpoint stage does not match the input paper.")
        if checkpoint.discipline != paper.discipline:
            raise ValueError("Review checkpoint discipline does not match the input paper.")

    def _resolve_resume_start_worker_id(
        self,
        worker_agents: list[BaseReviewAgent],
        resumed_worker_ids: list[str],
    ) -> str | None:
        if not resumed_worker_ids:
            return None
        resumed_worker_id_set = set(resumed_worker_ids)
        for worker_agent in worker_agents:
            if worker_agent.agent_name not in resumed_worker_id_set:
                return worker_agent.agent_name
        return None

    def _worker_agents(self) -> list[BaseReviewAgent]:
        return [
            self.topic_scope_agent,
            self.logic_chain_agent,
            self.literature_support_agent,
            self.novelty_depth_agent,
            self.writing_format_agent,
        ]

    def worker_ids(self) -> list[str]:
        return [worker_agent.agent_name for worker_agent in self._worker_agents()]

    def worker_dimensions(self) -> dict[str, Dimension]:
        return {
            worker_id: self._dimension_from_worker_id(worker_id)
            for worker_id in self.worker_ids()
        }

    def _worker_agent_by_id(self, worker_id: str) -> BaseReviewAgent:
        for worker_agent in self._worker_agents():
            if worker_agent.agent_name == worker_id:
                return worker_agent
        raise KeyError(worker_id)

    def _resolve_stop_after_index(
        self,
        worker_agents: list[BaseReviewAgent],
        stop_after_worker_id: str | None,
    ) -> int:
        if stop_after_worker_id is None:
            return len(worker_agents) - 1
        for index, worker_agent in enumerate(worker_agents):
            if worker_agent.agent_name == stop_after_worker_id:
                return index
        return len(worker_agents) - 1

    def _build_review_run(
        self,
        paper: PaperPackage,
        worker_agents: list[BaseReviewAgent],
        selected_worker_agents: list[BaseReviewAgent],
        *,
        resumed_worker_ids: list[str],
        stop_after_worker_id: str | None,
        run_id: str | None,
    ) -> ReviewRun:
        timestamp = utc_now()
        return ReviewRun(
            run_id=run_id or uuid4().hex,
            paper_id=paper.paper_id,
            stage=paper.stage,
            discipline=paper.discipline,
            state=RunState.RUNNING,
            worker_sequence=[worker_agent.agent_name for worker_agent in worker_agents],
            selected_worker_ids=[worker_agent.agent_name for worker_agent in selected_worker_agents],
            worker_runs=[
                WorkerRun(
                    worker_id=worker_agent.agent_name,
                    dimension=self._dimension_from_worker_id(worker_agent.agent_name),
                )
                for worker_agent in worker_agents
            ],
            resumed_from_checkpoint=bool(resumed_worker_ids),
            checkpoint_completed_worker_count=len(resumed_worker_ids),
            started_at=timestamp,
            updated_at=timestamp,
            stop_after_worker_id=stop_after_worker_id,
        )

    def _get_worker_run(self, worker_id: str) -> WorkerRun:
        if self.last_review_run is None:
            raise RuntimeError("review run has not been initialized")
        worker_run = self.last_review_run.get_worker(worker_id)
        if worker_run is None:
            raise KeyError(worker_id)
        return worker_run

    def _sync_worker_run_state_map(self) -> None:
        if self.last_review_run is None:
            self.last_worker_run_states = {}
            return
        self.last_worker_run_states = {
            worker_run.worker_id: worker_run.state.value
            for worker_run in self.last_review_run.worker_runs
        }

    def _touch_review_run(self, timestamp) -> None:
        if self.last_review_run is None:
            return
        self.last_review_run.refresh_counters(now=timestamp)
        self._sync_worker_run_state_map()
        self._emit_review_run_update()

    def _emit_review_run_update(self) -> None:
        if self.run_update_hook is None or self.last_review_run is None:
            return
        self.run_update_hook(self.last_review_run.model_copy(deep=True))

    def _set_review_run_state(self, state: RunState) -> None:
        with self._worker_run_state_lock:
            if self.last_review_run is None:
                return
            timestamp = utc_now()
            self.last_review_run.state = state
            if state in {RunState.COMPLETED, RunState.FAILED}:
                self.last_review_run.finished_at = timestamp
            self._touch_review_run(timestamp)

    def _mark_worker_running(self, worker_id: str) -> None:
        with self._worker_run_state_lock:
            worker_run = self._get_worker_run(worker_id)
            timestamp = utc_now()
            worker_run.state = RunState.RUNNING
            worker_run.started_at = worker_run.started_at or timestamp
            worker_run.finished_at = None
            worker_run.error_message = None
            self._touch_review_run(timestamp)

    def _mark_worker_from_result(self, worker_result: _WorkerReviewResult) -> None:
        with self._worker_run_state_lock:
            worker_run = self._get_worker_run(worker_result.worker_id)
            timestamp = utc_now()
            worker_run.state = worker_result.status
            worker_run.from_checkpoint = worker_result.from_checkpoint
            worker_run.score = worker_result.report.score
            worker_run.finding_count = len(worker_result.report.findings)
            worker_run.summary = worker_result.report.summary
            worker_run.review_backend = worker_result.execution_metadata.review_backend
            worker_run.structured_output_status = worker_result.execution_metadata.structured_output_status
            worker_run.fallback_used = worker_result.execution_metadata.fallback_used
            worker_run.llm_error_category = worker_result.execution_metadata.llm_error_category
            worker_run.error_message = None
            worker_run.started_at = worker_run.started_at or timestamp
            worker_run.finished_at = timestamp
            self._touch_review_run(timestamp)

    def _mark_worker_failed(self, worker_id: str, error: Exception) -> None:
        with self._worker_run_state_lock:
            worker_run = self._get_worker_run(worker_id)
            timestamp = utc_now()
            worker_run.state = RunState.FAILED
            worker_run.started_at = worker_run.started_at or timestamp
            worker_run.finished_at = timestamp
            worker_run.error_message = str(error)
            self._touch_review_run(timestamp)

    def _execute_workers_concurrently(
        self,
        worker_agents: list[BaseReviewAgent],
        paper: PaperPackage,
        *,
        skill_context: dict[str, str],
    ) -> dict[str, _WorkerReviewResult]:
        if not worker_agents:
            return {}

        worker_results: dict[str, _WorkerReviewResult] = {}
        first_error: Exception | None = None
        with ThreadPoolExecutor(max_workers=len(worker_agents)) as executor:
            self._raise_if_cancelled()
            future_map = {
                executor.submit(
                    self._execute_worker_review,
                    worker_agent,
                    paper,
                    skill_context=skill_context,
                ): worker_agent.agent_name
                for worker_agent in worker_agents
            }
            for future in as_completed(future_map):
                self._raise_if_cancelled()
                worker_id = future_map[future]
                try:
                    worker_results[worker_id] = future.result()
                except Exception as error:  # pragma: no cover - exercised through caller behavior
                    self._mark_worker_failed(worker_id, error)
                    if first_error is None:
                        first_error = error
        if first_error is not None:
            raise first_error
        return worker_results

    def _execute_worker_review(
        self,
        worker_agent: BaseReviewAgent,
        paper: PaperPackage,
        *,
        skill_context: dict[str, str],
    ) -> _WorkerReviewResult:
        return self._review_worker(
            worker_agent,
            paper,
            skill_context=skill_context,
            manage_run_state=True,
            emit_checkpoint=True,
        )

    def _review_worker(
        self,
        worker_agent: BaseReviewAgent,
        paper: PaperPackage,
        *,
        skill_context: dict[str, str],
        manage_run_state: bool,
        emit_checkpoint: bool,
    ) -> _WorkerReviewResult:
        self._raise_if_cancelled()
        if manage_run_state:
            self._mark_worker_running(worker_agent.agent_name)
        skill_bundle = self.skill_loader.resolve_worker_skills(worker_agent.agent_name, **skill_context)
        skill_trace = self._build_worker_skill_trace(worker_agent.agent_name, skill_bundle)
        original_llm_config = getattr(worker_agent, "llm_config", None)
        policy = self.worker_run_policies.get(worker_agent.agent_name)
        if policy is None:
            self._raise_if_cancelled()
            report = worker_agent.review(paper, skill_bundle)
            self._raise_if_cancelled()
        else:
            setattr(worker_agent, "llm_config", policy.apply_to_config(original_llm_config))
            try:
                self._raise_if_cancelled()
                report = worker_agent.review(paper, skill_bundle)
                self._raise_if_cancelled()
            finally:
                setattr(worker_agent, "llm_config", original_llm_config)
        execution_metadata = self._build_worker_execution_metadata(worker_agent)
        status = self._status_from_execution_metadata(execution_metadata)
        worker_result = _WorkerReviewResult(
            worker_id=worker_agent.agent_name,
            report=report,
            execution_metadata=execution_metadata,
            skill_trace=skill_trace,
            status=status,
        )
        if manage_run_state:
            self._mark_worker_from_result(worker_result)
        if emit_checkpoint:
            self._emit_worker_checkpoint(worker_result)
        return worker_result

    def _emit_worker_checkpoint(self, worker_result: _WorkerReviewResult) -> None:
        if self.worker_checkpoint_hook is None:
            return
        self.worker_checkpoint_hook(
            WorkerCheckpoint(
                worker_id=worker_result.worker_id,
                dimension=worker_result.report.dimension,
                report=worker_result.report,
                execution_metadata=worker_result.execution_metadata,
                skill_trace=worker_result.skill_trace,
            )
        )

    def _raise_if_cancelled(self) -> None:
        if self.cancel_check is None:
            return
        if self.cancel_check():
            raise ReviewRunCancelledError("review run cancelled after ownership was transferred")

    def _apply_worker_cooldown(
        self,
        worker_id: str,
        execution_metadata: WorkerExecutionMetadata,
    ) -> None:
        policy = self.worker_run_policies.get(worker_id)
        if policy is None:
            return

        cooldown_ms = (
            policy.cooldown_after_failure_ms
            if execution_metadata.fallback_used or execution_metadata.structured_output_status != "parsed"
            else policy.cooldown_after_success_ms
        )
        if cooldown_ms <= 0:
            return
        self._sleep_with_cancel(cooldown_ms / 1000)

    def _sleep_with_cancel(self, seconds: float) -> None:
        if seconds <= 0:
            return
        if self.cancel_check is None:
            self.sleep_fn(seconds)
            return

        remaining = seconds
        while remaining > 0:
            self._raise_if_cancelled()
            sleep_seconds = min(remaining, 0.05)
            self.sleep_fn(sleep_seconds)
            remaining -= sleep_seconds
        self._raise_if_cancelled()

    def _status_from_execution_metadata(self, execution_metadata: WorkerExecutionMetadata) -> RunState:
        if execution_metadata.fallback_used:
            return RunState.FALLBACK_COMPLETED
        return RunState.COMPLETED

    def _build_worker_skill_trace(
        self,
        worker_id: str,
        skill_bundle: SkillBundle,
    ) -> WorkerSkillTrace:
        return WorkerSkillTrace(
            worker_id=worker_id,
            rubric_skills=[skill.metadata.versioned_id for skill in skill_bundle.rubric_skills],
            policy_skills=[skill.metadata.versioned_id for skill in skill_bundle.policy_skills],
            output_schema_skills=[skill.metadata.versioned_id for skill in skill_bundle.output_schema_skills],
            domain_skills=[skill.metadata.versioned_id for skill in skill_bundle.domain_skills],
        )

    def _build_worker_execution_traces(
        self,
        ledger: EvidenceLedger,
        reports: list[DimensionReport],
    ) -> list[WorkerExecutionTrace]:
        candidate_dimensions = {candidate.dimension for candidate in self.last_debate_candidates}
        traces: list[WorkerExecutionTrace] = []
        for report in reports:
            metadata = ledger.get_execution_metadata(report.dimension) or WorkerExecutionMetadata()
            traces.append(
                self._build_worker_execution_trace(
                    report,
                    metadata,
                    debate_candidate=report.dimension in candidate_dimensions,
                )
            )
        return traces

    def _build_worker_execution_trace(
        self,
        report: DimensionReport,
        metadata: WorkerExecutionMetadata,
        *,
        debate_candidate: bool = False,
    ) -> WorkerExecutionTrace:
        return WorkerExecutionTrace(
            worker_id=report.findings[0].source_agent if report.findings else self._worker_id_from_dimension(report.dimension),
            dimension=report.dimension,
            score=report.score,
            finding_count=len(report.findings),
            high_severity_count=sum(1 for finding in report.findings if finding.severity == Severity.HIGH),
            debate_candidate=debate_candidate,
            debate_used=report.debate_used,
            summary=report.summary,
            review_backend=metadata.review_backend,
            llm_provider_id=metadata.llm_provider_id,
            llm_model_name=metadata.llm_model_name,
            llm_finish_reason=metadata.llm_finish_reason,
            llm_error_category=metadata.llm_error_category,
            structured_output_status=metadata.structured_output_status,
            fallback_used=metadata.fallback_used,
            llm_request_attempts=metadata.llm_request_attempts,
            llm_retry_count=metadata.llm_retry_count,
            llm_prompt_tokens=metadata.llm_prompt_tokens,
            llm_completion_tokens=metadata.llm_completion_tokens,
            llm_total_tokens=metadata.llm_total_tokens,
        )

    def _build_worker_execution_metadata(
        self,
        worker_agent: BaseReviewAgent,
    ) -> WorkerExecutionMetadata:
        return worker_agent.build_execution_metadata()

    def _worker_id_from_dimension(self, dimension: Dimension) -> str:
        dimension_map = {
            Dimension.TOPIC_SCOPE: self.topic_scope_agent.agent_name,
            Dimension.LOGIC_CHAIN: self.logic_chain_agent.agent_name,
            Dimension.LITERATURE_SUPPORT: self.literature_support_agent.agent_name,
            Dimension.NOVELTY_DEPTH: self.novelty_depth_agent.agent_name,
            Dimension.WRITING_FORMAT: self.writing_format_agent.agent_name,
        }
        return dimension_map[dimension]

    def _dimension_from_worker_id(self, worker_id: str) -> Dimension:
        worker_dimension_map = {
            self.topic_scope_agent.agent_name: Dimension.TOPIC_SCOPE,
            self.logic_chain_agent.agent_name: Dimension.LOGIC_CHAIN,
            self.literature_support_agent.agent_name: Dimension.LITERATURE_SUPPORT,
            self.novelty_depth_agent.agent_name: Dimension.NOVELTY_DEPTH,
            self.writing_format_agent.agent_name: Dimension.WRITING_FORMAT,
        }
        return worker_dimension_map[worker_id]

    def _run_selective_debate(
        self,
        ledger: EvidenceLedger,
        reports: list[DimensionReport],
    ) -> tuple[list[DebateResolution], list[DebateResolutionTrace]]:
        resolutions: list[DebateResolution] = []
        resolution_traces: list[DebateResolutionTrace] = []
        if not self.last_debate_candidates:
            return resolutions, resolution_traces

        rubric_skill = self.skill_loader.load_skill("severity-resolution-rubric")
        candidate_map = {candidate.dimension: candidate for candidate in self.last_debate_candidates}
        updated_reports: list[DimensionReport] = []
        for report in reports:
            candidate = candidate_map.get(report.dimension)
            if candidate is None:
                updated_reports.append(report)
                continue

            decision_snapshot = self.debate_judge_agent.inspect_case(candidate, report)
            updated_report, resolution = self.debate_judge_agent.adjudicate(
                candidate,
                report,
                skill_version=rubric_skill.metadata.versioned_id,
            )
            ledger.record_debate_result(resolution, updated_report)
            metadata = ledger.get_execution_metadata(report.dimension) or WorkerExecutionMetadata()
            resolution_traces.append(
                DebateResolutionTrace(
                    dimension=resolution.dimension,
                    trigger_reason=resolution.trigger_reason,
                    candidate_issue_titles=candidate.candidate_issue_titles,
                    recommended_action=candidate.recommended_action,
                    confidence_floor=candidate.confidence_floor,
                    pre_debate_score=candidate.score,
                    adjusted_score=resolution.adjusted_score,
                    score_delta=resolution.adjusted_score - candidate.score,
                    decision_policy_summary=decision_snapshot.decision_policy_summary,
                    upheld_finding_count=len(decision_snapshot.upheld_findings),
                    dropped_finding_count=len(decision_snapshot.dropped_findings),
                    resolution_summary=resolution.resolution_summary,
                    upheld_issue_titles=resolution.upheld_issue_titles,
                    dropped_issue_titles=resolution.dropped_issue_titles,
                    dropped_issue_reasons=decision_snapshot.dropped_issue_reasons,
                    source_agent=resolution.source_agent,
                    source_skill_version=resolution.source_skill_version,
                    worker_review_backend=metadata.review_backend,
                    worker_llm_provider_id=metadata.llm_provider_id,
                    worker_llm_model_name=metadata.llm_model_name,
                    worker_llm_finish_reason=metadata.llm_finish_reason,
                    worker_llm_error_category=metadata.llm_error_category,
                    worker_structured_output_status=metadata.structured_output_status,
                    worker_fallback_used=metadata.fallback_used,
                    worker_llm_request_attempts=metadata.llm_request_attempts,
                    worker_llm_retry_count=metadata.llm_retry_count,
                    worker_llm_prompt_tokens=metadata.llm_prompt_tokens,
                    worker_llm_completion_tokens=metadata.llm_completion_tokens,
                    worker_llm_total_tokens=metadata.llm_total_tokens,
                )
            )
            updated_reports.append(updated_report)
            resolutions.append(resolution)

        reports[:] = updated_reports
        return resolutions, resolution_traces
