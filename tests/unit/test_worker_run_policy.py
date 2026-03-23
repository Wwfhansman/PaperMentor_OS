from __future__ import annotations

from dataclasses import dataclass
import pytest

from papermentor_os.agents.base import BaseReviewAgent
from papermentor_os.llm import ProviderConfig
from papermentor_os.orchestrator.chief_reviewer import ChiefReviewer, ReviewRunCancelledError
from papermentor_os.runtime import WorkerRunPolicy
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
        dimension_reports = ledger.get_dimension_reports()
        return FinalReport(
            overall_summary="stub",
            dimension_reports=dimension_reports,
            priority_actions=[],
            student_guidance=StudentGuidance(next_steps=[]),
            advisor_view=AdvisorView(quick_summary="stub", watch_points=[]),
            safety_notice="stub",
        )


@dataclass
class _FakeDisagreementDetector:
    def detect(self, reports: list[DimensionReport]) -> list[object]:
        return []


class _StubAgent(BaseReviewAgent):
    def __init__(
        self,
        *,
        agent_name: str,
        dimension: Dimension,
        metadata: WorkerExecutionMetadata,
        llm_config: ProviderConfig | None = None,
    ) -> None:
        self.agent_name = agent_name
        self.skill_version = f"{agent_name}@test"
        self._dimension = dimension
        self._metadata = metadata
        self.llm_config = llm_config
        self.observed_llm_config: ProviderConfig | None = None

    def review(self, paper: PaperPackage, skill_bundle: SkillBundle | None = None) -> DimensionReport:
        self.observed_llm_config = self.llm_config
        return DimensionReport(
            dimension=self._dimension,
            score=8.0,
            summary=f"{self.agent_name} summary",
            findings=[],
            debate_used=False,
        )

    def build_execution_metadata(self) -> WorkerExecutionMetadata:
        return self._metadata


def test_chief_reviewer_applies_worker_policy_overrides_and_cooldowns() -> None:
    base_config = ProviderConfig(
        provider_id="openai_compatible",
        base_url="https://example.com/v1",
        api_key="sk-test",
        model_name="gpt-test",
        prompt_char_budget=9000,
        timeout=20.0,
    )
    sleep_calls: list[float] = []
    reviewer = ChiefReviewer(
        topic_scope_agent=_StubAgent(
            agent_name="TopicScopeAgent",
            dimension=Dimension.TOPIC_SCOPE,
            llm_config=base_config,
            metadata=WorkerExecutionMetadata(
                review_backend="model_with_fallback",
                structured_output_status="parsed",
                fallback_used=False,
            ),
        ),
        logic_chain_agent=_StubAgent(
            agent_name="LogicChainAgent",
            dimension=Dimension.LOGIC_CHAIN,
            llm_config=base_config,
            metadata=WorkerExecutionMetadata(
                review_backend="model_with_fallback",
                structured_output_status="error:LLMProviderError",
                fallback_used=True,
            ),
        ),
        literature_support_agent=_StubAgent(
            agent_name="LiteratureSupportAgent",
            dimension=Dimension.LITERATURE_SUPPORT,
            llm_config=base_config,
            metadata=WorkerExecutionMetadata(),
        ),
        novelty_depth_agent=_StubAgent(
            agent_name="NoveltyDepthAgent",
            dimension=Dimension.NOVELTY_DEPTH,
            llm_config=base_config,
            metadata=WorkerExecutionMetadata(),
        ),
        writing_format_agent=_StubAgent(
            agent_name="WritingFormatAgent",
            dimension=Dimension.WRITING_FORMAT,
            llm_config=base_config,
            metadata=WorkerExecutionMetadata(),
        ),
        skill_loader=_FakeSkillLoader(),
        disagreement_detector=_FakeDisagreementDetector(),
        composer=_FakeComposer(),
        worker_run_policies={
            "TopicScopeAgent": WorkerRunPolicy(
                prompt_char_budget=3200,
                cooldown_after_success_ms=250,
            ),
            "LogicChainAgent": WorkerRunPolicy(
                timeout=45.0,
                cooldown_after_failure_ms=800,
            ),
        },
        sleep_fn=sleep_calls.append,
    )

    reviewer.review_paper(
        PaperPackage(
            paper_id="paper-1",
            title="Test Paper",
            abstract="Test abstract",
        )
    )

    assert reviewer.topic_scope_agent.observed_llm_config is not None
    assert reviewer.topic_scope_agent.observed_llm_config.prompt_char_budget == 3200
    assert reviewer.topic_scope_agent.llm_config == base_config

    assert reviewer.logic_chain_agent.observed_llm_config is not None
    assert reviewer.logic_chain_agent.observed_llm_config.timeout == 45.0
    assert reviewer.logic_chain_agent.llm_config == base_config

    assert sleep_calls == [0.25, 0.8]


def test_chief_reviewer_cooldown_stops_when_run_is_cancelled() -> None:
    cancelled = False
    sleep_calls: list[float] = []

    def _cancel_check() -> bool:
        return cancelled

    def _sleep_and_trigger_cancel(seconds: float) -> None:
        nonlocal cancelled
        sleep_calls.append(seconds)
        cancelled = True

    reviewer = ChiefReviewer(
        topic_scope_agent=_StubAgent(
            agent_name="TopicScopeAgent",
            dimension=Dimension.TOPIC_SCOPE,
            metadata=WorkerExecutionMetadata(
                review_backend="model_with_fallback",
                structured_output_status="parsed",
                fallback_used=False,
            ),
        ),
        logic_chain_agent=_StubAgent(
            agent_name="LogicChainAgent",
            dimension=Dimension.LOGIC_CHAIN,
            metadata=WorkerExecutionMetadata(),
        ),
        literature_support_agent=_StubAgent(
            agent_name="LiteratureSupportAgent",
            dimension=Dimension.LITERATURE_SUPPORT,
            metadata=WorkerExecutionMetadata(),
        ),
        novelty_depth_agent=_StubAgent(
            agent_name="NoveltyDepthAgent",
            dimension=Dimension.NOVELTY_DEPTH,
            metadata=WorkerExecutionMetadata(),
        ),
        writing_format_agent=_StubAgent(
            agent_name="WritingFormatAgent",
            dimension=Dimension.WRITING_FORMAT,
            metadata=WorkerExecutionMetadata(),
        ),
        skill_loader=_FakeSkillLoader(),
        disagreement_detector=_FakeDisagreementDetector(),
        composer=_FakeComposer(),
        worker_run_policies={
            "TopicScopeAgent": WorkerRunPolicy(cooldown_after_success_ms=250),
        },
        sleep_fn=_sleep_and_trigger_cancel,
        cancel_check=_cancel_check,
    )

    with pytest.raises(ReviewRunCancelledError):
        reviewer.run_review_until(
            PaperPackage(
                paper_id="paper-1",
                title="Test Paper",
                abstract="Test abstract",
            ),
            stop_after_worker_id="TopicScopeAgent",
        )

    assert sleep_calls == [0.05]
