from __future__ import annotations

from pathlib import Path

from papermentor_os.agents.literature_support import LiteratureSupportAgent
from papermentor_os.agents.logic_chain import LogicChainAgent
from papermentor_os.agents.novelty_depth import NoveltyDepthAgent
from papermentor_os.agents.topic_scope import TopicScopeAgent
from papermentor_os.agents.writing_format import WritingFormatAgent
from papermentor_os.ledger.evidence_ledger import EvidenceLedger
from papermentor_os.orchestrator.disagreement import DisagreementDetector
from papermentor_os.parsers.docx_parser import DocxPaperParser
from papermentor_os.reporting.composer import GuidanceComposer
from papermentor_os.schemas.debate import DebateCase
from papermentor_os.schemas.paper import PaperPackage
from papermentor_os.schemas.report import FinalReport
from papermentor_os.schemas.types import Discipline, PaperStage
from papermentor_os.skills.loader import SkillLoader


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
        self.skill_loader = skill_loader or SkillLoader(Path(__file__).resolve().parents[3] / "skills")
        self.disagreement_detector = disagreement_detector or DisagreementDetector()
        self.composer = composer or GuidanceComposer()
        self.last_debate_candidates: list[DebateCase] = []

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

        reports = (
            self.topic_scope_agent.review(
                paper,
                self.skill_loader.resolve_worker_skills(self.topic_scope_agent.agent_name, **skill_context),
            ),
            self.logic_chain_agent.review(
                paper,
                self.skill_loader.resolve_worker_skills(self.logic_chain_agent.agent_name, **skill_context),
            ),
            self.literature_support_agent.review(
                paper,
                self.skill_loader.resolve_worker_skills(self.literature_support_agent.agent_name, **skill_context),
            ),
            self.novelty_depth_agent.review(
                paper,
                self.skill_loader.resolve_worker_skills(self.novelty_depth_agent.agent_name, **skill_context),
            ),
            self.writing_format_agent.review(
                paper,
                self.skill_loader.resolve_worker_skills(self.writing_format_agent.agent_name, **skill_context),
            ),
        )

        for report in reports:
            ledger.record_dimension_report(report)

        self.last_debate_candidates = self.disagreement_detector.detect(list(reports))
        return self.composer.compose(paper, ledger)
