from __future__ import annotations

from dataclasses import dataclass
from threading import Event, Lock, Thread

from papermentor_os.agents.base import BaseReviewAgent
from papermentor_os.orchestrator.chief_reviewer import ChiefReviewer
from papermentor_os.orchestrator.run_state import RunState
from papermentor_os.schemas.paper import PaperPackage
from papermentor_os.schemas.report import AdvisorView, DimensionReport, FinalReport, StudentGuidance
from papermentor_os.schemas.trace import WorkerExecutionMetadata
from papermentor_os.schemas.types import Dimension
from papermentor_os.skills.loader import SkillBundle


@dataclass
class _FakeSkillLoader:
    def resolve_worker_skills(self, worker_id: str, *, discipline: str, stage: str) -> SkillBundle:
        return SkillBundle(
            rubric_skills=[],
            policy_skills=[],
            output_schema_skills=[],
            domain_skills=[],
        )


@dataclass
class _FakeComposer:
    def compose(self, paper: PaperPackage, ledger: object) -> FinalReport:
        return FinalReport(
            overall_summary="stub",
            dimension_reports=ledger.get_dimension_reports(),
            priority_actions=[],
            student_guidance=StudentGuidance(next_steps=[]),
            advisor_view=AdvisorView(quick_summary="stub", watch_points=[]),
            safety_notice="stub",
        )


@dataclass
class _FakeDisagreementDetector:
    def detect(self, reports: list[DimensionReport]) -> list[object]:
        return []


class _CountingAgent(BaseReviewAgent):
    def __init__(self, *, agent_name: str, dimension: Dimension) -> None:
        self.agent_name = agent_name
        self.skill_version = f"{agent_name}@test"
        self.dimension = dimension
        self.review_calls = 0

    def review(self, paper: PaperPackage, skill_bundle: SkillBundle | None = None) -> DimensionReport:
        self.review_calls += 1
        return DimensionReport(
            dimension=self.dimension,
            score=8.0,
            summary=f"{self.agent_name} summary",
            findings=[],
            debate_used=False,
        )

    def build_execution_metadata(self) -> WorkerExecutionMetadata:
        return WorkerExecutionMetadata(review_backend="rule_only")


class _DelayedCountingAgent(_CountingAgent):
    def __init__(
        self,
        *,
        agent_name: str,
        dimension: Dimension,
        delay_started: Event | None = None,
        release_delay: Event | None = None,
        started_workers: list[str] | None = None,
        started_lock: Lock | None = None,
        required_started_workers: set[str] | None = None,
    ) -> None:
        super().__init__(agent_name=agent_name, dimension=dimension)
        self.delay_started = delay_started
        self.release_delay = release_delay
        self.started_workers = started_workers
        self.started_lock = started_lock
        self.required_started_workers = required_started_workers

    def review(self, paper: PaperPackage, skill_bundle: SkillBundle | None = None) -> DimensionReport:
        if self.started_workers is not None and self.started_lock is not None:
            with self.started_lock:
                self.started_workers.append(self.agent_name)
                if self.delay_started is not None and self.required_started_workers is not None:
                    if self.required_started_workers.issubset(set(self.started_workers)):
                        self.delay_started.set()
        if self.release_delay is not None:
            assert self.release_delay.wait(timeout=1.0)
        return super().review(paper, skill_bundle)


def _reviewer() -> ChiefReviewer:
    return ChiefReviewer(
        topic_scope_agent=_CountingAgent(
            agent_name="TopicScopeAgent",
            dimension=Dimension.TOPIC_SCOPE,
        ),
        logic_chain_agent=_CountingAgent(
            agent_name="LogicChainAgent",
            dimension=Dimension.LOGIC_CHAIN,
        ),
        literature_support_agent=_CountingAgent(
            agent_name="LiteratureSupportAgent",
            dimension=Dimension.LITERATURE_SUPPORT,
        ),
        novelty_depth_agent=_CountingAgent(
            agent_name="NoveltyDepthAgent",
            dimension=Dimension.NOVELTY_DEPTH,
        ),
        writing_format_agent=_CountingAgent(
            agent_name="WritingFormatAgent",
            dimension=Dimension.WRITING_FORMAT,
        ),
        skill_loader=_FakeSkillLoader(),
        disagreement_detector=_FakeDisagreementDetector(),
        composer=_FakeComposer(),
    )


def _paper() -> PaperPackage:
    return PaperPackage(
        paper_id="paper-1",
        title="Checkpoint Test Paper",
        abstract="Test abstract",
    )


def test_chief_reviewer_can_resume_from_checkpoint_without_rerunning_completed_workers() -> None:
    reviewer = _reviewer()
    paper = _paper()

    checkpoint = reviewer.run_review_until(
        paper,
        stop_after_worker_id="LogicChainAgent",
    )

    assert checkpoint.worker_ids() == ["TopicScopeAgent", "LogicChainAgent"]
    assert reviewer.topic_scope_agent.review_calls == 1
    assert reviewer.logic_chain_agent.review_calls == 1
    assert reviewer.literature_support_agent.review_calls == 0

    report = reviewer.review_paper(paper, checkpoint=checkpoint)

    assert reviewer.topic_scope_agent.review_calls == 1
    assert reviewer.logic_chain_agent.review_calls == 1
    assert reviewer.literature_support_agent.review_calls == 1
    assert reviewer.novelty_depth_agent.review_calls == 1
    assert reviewer.writing_format_agent.review_calls == 1
    assert len(report.dimension_reports) == 5
    assert [item.worker_id for item in checkpoint.completed_workers] == [
        "TopicScopeAgent",
        "LogicChainAgent",
    ]
    assert reviewer.last_orchestration_trace is not None
    assert reviewer.last_orchestration_trace.resumed_from_checkpoint is True
    assert reviewer.last_orchestration_trace.checkpoint_completed_worker_count == 2
    assert reviewer.last_orchestration_trace.resumed_worker_ids == [
        "TopicScopeAgent",
        "LogicChainAgent",
    ]
    assert reviewer.last_orchestration_trace.skipped_worker_ids == [
        "TopicScopeAgent",
        "LogicChainAgent",
    ]
    assert reviewer.last_orchestration_trace.resume_start_worker_id == "LiteratureSupportAgent"
    assert reviewer.last_review_run is not None
    assert reviewer.last_review_run.state == RunState.COMPLETED
    assert reviewer.last_review_run.resumed_from_checkpoint is True
    assert reviewer.last_review_run.checkpoint_completed_worker_count == 2
    assert reviewer.last_review_run.completed_worker_count == 5
    assert reviewer.last_review_run.failed_worker_count == 0
    assert reviewer.last_review_run.get_worker("TopicScopeAgent").from_checkpoint is True
    assert reviewer.last_review_run.get_worker("WritingFormatAgent").state == RunState.COMPLETED


def test_chief_reviewer_rejects_checkpoint_for_different_paper() -> None:
    reviewer = _reviewer()
    checkpoint = reviewer.run_review_until(
        _paper(),
        stop_after_worker_id="TopicScopeAgent",
    )
    mismatched_paper = PaperPackage(
        paper_id="paper-2",
        title="Other Paper",
        abstract="Other abstract",
    )

    try:
        reviewer.review_paper(mismatched_paper, checkpoint=checkpoint)
    except ValueError as error:
        assert "paper_id" in str(error)
    else:
        raise AssertionError("expected checkpoint validation error")


def test_chief_reviewer_runs_worker_batch_concurrently() -> None:
    started_workers: list[str] = []
    started_lock = Lock()
    both_started = Event()
    release_delay = Event()
    reviewer = ChiefReviewer(
        topic_scope_agent=_DelayedCountingAgent(
            agent_name="TopicScopeAgent",
            dimension=Dimension.TOPIC_SCOPE,
            delay_started=both_started,
            release_delay=release_delay,
            started_workers=started_workers,
            started_lock=started_lock,
            required_started_workers={"TopicScopeAgent", "LogicChainAgent"},
        ),
        logic_chain_agent=_DelayedCountingAgent(
            agent_name="LogicChainAgent",
            dimension=Dimension.LOGIC_CHAIN,
            delay_started=both_started,
            release_delay=release_delay,
            started_workers=started_workers,
            started_lock=started_lock,
            required_started_workers={"TopicScopeAgent", "LogicChainAgent"},
        ),
        literature_support_agent=_CountingAgent(
            agent_name="LiteratureSupportAgent",
            dimension=Dimension.LITERATURE_SUPPORT,
        ),
        novelty_depth_agent=_CountingAgent(
            agent_name="NoveltyDepthAgent",
            dimension=Dimension.NOVELTY_DEPTH,
        ),
        writing_format_agent=_CountingAgent(
            agent_name="WritingFormatAgent",
            dimension=Dimension.WRITING_FORMAT,
        ),
        skill_loader=_FakeSkillLoader(),
        disagreement_detector=_FakeDisagreementDetector(),
        composer=_FakeComposer(),
    )
    paper = _paper()
    errors: list[Exception] = []

    def _run_review() -> None:
        try:
            reviewer.review_paper(paper)
        except Exception as error:  # pragma: no cover - failure path asserted below
            errors.append(error)

    review_thread = Thread(target=_run_review)
    review_thread.start()

    assert both_started.wait(timeout=1.0) is True
    with started_lock:
        assert "TopicScopeAgent" in started_workers
        assert "LogicChainAgent" in started_workers
    release_delay.set()
    review_thread.join(timeout=1.0)

    assert review_thread.is_alive() is False
    assert not errors
    assert reviewer.last_worker_run_states["TopicScopeAgent"] == "completed"
    assert reviewer.last_worker_run_states["LogicChainAgent"] == "completed"
    assert reviewer.topic_scope_agent.review_calls == 1
    assert reviewer.logic_chain_agent.review_calls == 1
    assert reviewer.last_review_run is not None
    assert reviewer.last_review_run.state == RunState.COMPLETED
    assert reviewer.last_review_run.completed_worker_count == 5
    assert reviewer.last_review_run.get_worker("TopicScopeAgent").state == RunState.COMPLETED
    assert reviewer.last_review_run.get_worker("TopicScopeAgent").started_at is not None
    assert reviewer.last_review_run.get_worker("TopicScopeAgent").finished_at is not None


def test_checkpoint_and_skill_trace_order_stay_stable_under_concurrent_completion() -> None:
    release_delay = Event()
    release_delay.set()
    reviewer = ChiefReviewer(
        topic_scope_agent=_DelayedCountingAgent(
            agent_name="TopicScopeAgent",
            dimension=Dimension.TOPIC_SCOPE,
            release_delay=release_delay,
        ),
        logic_chain_agent=_DelayedCountingAgent(
            agent_name="LogicChainAgent",
            dimension=Dimension.LOGIC_CHAIN,
            release_delay=release_delay,
        ),
        literature_support_agent=_CountingAgent(
            agent_name="LiteratureSupportAgent",
            dimension=Dimension.LITERATURE_SUPPORT,
        ),
        novelty_depth_agent=_CountingAgent(
            agent_name="NoveltyDepthAgent",
            dimension=Dimension.NOVELTY_DEPTH,
        ),
        writing_format_agent=_CountingAgent(
            agent_name="WritingFormatAgent",
            dimension=Dimension.WRITING_FORMAT,
        ),
        skill_loader=_FakeSkillLoader(),
        disagreement_detector=_FakeDisagreementDetector(),
        composer=_FakeComposer(),
    )
    paper = _paper()

    checkpoint = reviewer.run_review_until(
        paper,
        stop_after_worker_id="LogicChainAgent",
    )

    assert checkpoint.worker_ids() == ["TopicScopeAgent", "LogicChainAgent"]
    assert reviewer.last_review_run is not None
    assert reviewer.last_review_run.state == RunState.COMPLETED
    assert reviewer.last_review_run.selected_worker_ids == ["TopicScopeAgent", "LogicChainAgent"]
    assert reviewer.last_review_run.completed_worker_count == 2
    assert reviewer.last_review_run.get_worker("WritingFormatAgent").state == RunState.PENDING

    report = reviewer.review_paper(paper, checkpoint=checkpoint)

    assert [item.dimension for item in report.dimension_reports] == [
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ]
    assert [trace.worker_id for trace in reviewer.last_worker_skill_traces] == [
        "TopicScopeAgent",
        "LogicChainAgent",
        "LiteratureSupportAgent",
        "NoveltyDepthAgent",
        "WritingFormatAgent",
    ]
    assert reviewer.last_review_run is not None
    assert reviewer.last_review_run.worker_sequence == [
        "TopicScopeAgent",
        "LogicChainAgent",
        "LiteratureSupportAgent",
        "NoveltyDepthAgent",
        "WritingFormatAgent",
    ]
