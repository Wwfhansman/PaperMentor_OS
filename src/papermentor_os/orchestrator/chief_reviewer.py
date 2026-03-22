from __future__ import annotations

from pathlib import Path

from papermentor_os.agents.base import BaseReviewAgent
from papermentor_os.agents.debate_judge import DebateJudgeAgent
from papermentor_os.agents.literature_support import LiteratureSupportAgent
from papermentor_os.agents.logic_chain import LogicChainAgent
from papermentor_os.agents.novelty_depth import NoveltyDepthAgent
from papermentor_os.agents.topic_scope import TopicScopeAgent
from papermentor_os.agents.writing_format import WritingFormatAgent
from papermentor_os.ledger.evidence_ledger import EvidenceLedger
from papermentor_os.orchestrator.disagreement import DisagreementDetector
from papermentor_os.parsers.docx_parser import DocxPaperParser
from papermentor_os.reporting.composer import GuidanceComposer
from papermentor_os.schemas.debate import DebateCase, DebateResolution
from papermentor_os.schemas.paper import PaperPackage
from papermentor_os.schemas.report import DimensionReport, FinalReport
from papermentor_os.schemas.trace import OrchestrationTrace, WorkerExecutionTrace, WorkerSkillTrace
from papermentor_os.schemas.types import Dimension, Discipline, PaperStage, Severity
from papermentor_os.skills.loader import SkillBundle, SkillLoader


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
        self.last_debate_candidates: list[DebateCase] = []
        self.last_debate_resolutions: list[DebateResolution] = []
        self.last_worker_skill_traces: list[WorkerSkillTrace] = []
        self.last_worker_execution_traces: list[WorkerExecutionTrace] = []
        self.last_orchestration_trace: OrchestrationTrace | None = None

    def review_docx(
        self,
        file_path: str | Path,
        *,
        stage: PaperStage = PaperStage.DRAFT,
        discipline: Discipline = Discipline.COMPUTER_SCIENCE,
    ) -> FinalReport:
        paper = self.parser.parse_file(file_path, stage=stage, discipline=discipline)
        return self.review_paper(paper)

    def review_paper(self, paper: PaperPackage) -> FinalReport:
        ledger = EvidenceLedger()
        skill_context = {
            "discipline": paper.discipline.value,
            "stage": paper.stage.value,
        }
        self.last_debate_candidates = []
        self.last_debate_resolutions = []
        self.last_worker_skill_traces = []
        self.last_worker_execution_traces = []
        self.last_orchestration_trace = None

        worker_agents = [
            self.topic_scope_agent,
            self.logic_chain_agent,
            self.literature_support_agent,
            self.novelty_depth_agent,
            self.writing_format_agent,
        ]
        reports: list[DimensionReport] = []
        for worker_agent in worker_agents:
            report = self._execute_worker_review(worker_agent, paper, skill_context=skill_context)
            reports.append(report)

        for report in reports:
            ledger.record_dimension_report(report)

        self.last_debate_candidates = self.disagreement_detector.detect(reports)
        self.last_debate_resolutions = self._run_selective_debate(ledger, reports)
        self.last_worker_execution_traces = self._build_worker_execution_traces(reports)
        self.last_orchestration_trace = OrchestrationTrace(
            stage=paper.stage,
            discipline=paper.discipline,
            worker_sequence=[agent.agent_name for agent in worker_agents],
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

    def _execute_worker_review(
        self,
        worker_agent: BaseReviewAgent,
        paper: PaperPackage,
        *,
        skill_context: dict[str, str],
    ) -> DimensionReport:
        skill_bundle = self.skill_loader.resolve_worker_skills(worker_agent.agent_name, **skill_context)
        self.last_worker_skill_traces.append(
            self._build_worker_skill_trace(worker_agent.agent_name, skill_bundle)
        )
        return worker_agent.review(paper, skill_bundle)

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
        reports: list[DimensionReport],
    ) -> list[WorkerExecutionTrace]:
        candidate_dimensions = {candidate.dimension for candidate in self.last_debate_candidates}
        return [
            WorkerExecutionTrace(
                worker_id=report.findings[0].source_agent if report.findings else self._worker_id_from_dimension(report.dimension),
                dimension=report.dimension,
                score=report.score,
                finding_count=len(report.findings),
                high_severity_count=sum(1 for finding in report.findings if finding.severity == Severity.HIGH),
                debate_candidate=report.dimension in candidate_dimensions,
                debate_used=report.debate_used,
                summary=report.summary,
            )
            for report in reports
        ]

    def _worker_id_from_dimension(self, dimension: Dimension) -> str:
        dimension_map = {
            Dimension.TOPIC_SCOPE: self.topic_scope_agent.agent_name,
            Dimension.LOGIC_CHAIN: self.logic_chain_agent.agent_name,
            Dimension.LITERATURE_SUPPORT: self.literature_support_agent.agent_name,
            Dimension.NOVELTY_DEPTH: self.novelty_depth_agent.agent_name,
            Dimension.WRITING_FORMAT: self.writing_format_agent.agent_name,
        }
        return dimension_map[dimension]

    def _run_selective_debate(
        self,
        ledger: EvidenceLedger,
        reports: list[DimensionReport],
    ) -> list[DebateResolution]:
        resolutions: list[DebateResolution] = []
        if not self.last_debate_candidates:
            return resolutions

        rubric_skill = self.skill_loader.load_skill("severity-resolution-rubric")
        candidate_map = {candidate.dimension: candidate for candidate in self.last_debate_candidates}
        updated_reports: list[DimensionReport] = []
        for report in reports:
            candidate = candidate_map.get(report.dimension)
            if candidate is None:
                updated_reports.append(report)
                continue

            updated_report, resolution = self.debate_judge_agent.adjudicate(
                candidate,
                report,
                skill_version=rubric_skill.metadata.versioned_id,
            )
            ledger.record_debate_result(resolution, updated_report)
            updated_reports.append(updated_report)
            resolutions.append(resolution)

        reports[:] = updated_reports
        return resolutions
