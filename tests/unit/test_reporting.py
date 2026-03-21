from papermentor_os.ledger.evidence_ledger import EvidenceLedger
from papermentor_os.reporting.composer import GuidanceComposer
from papermentor_os.schemas.paper import PaperPackage
from papermentor_os.schemas.report import DimensionReport, EvidenceAnchor, ReviewFinding
from papermentor_os.schemas.types import Dimension, Discipline, PaperStage, Severity


def test_guidance_composer_prioritizes_research_findings_over_writing_findings() -> None:
    paper = PaperPackage(
        paper_id="demo",
        title="demo title",
        discipline=Discipline.COMPUTER_SCIENCE,
        stage=PaperStage.DRAFT,
    )
    ledger = EvidenceLedger()
    ledger.record_dimension_report(
        DimensionReport(
            dimension=Dimension.WRITING_FORMAT,
            score=4.0,
            summary="writing summary",
            findings=[
                ReviewFinding(
                    dimension=Dimension.WRITING_FORMAT,
                    issue_title="缺少参考文献列表",
                    severity=Severity.HIGH,
                    confidence=0.95,
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="references",
                        location_label="参考文献",
                        quote="未识别到参考文献条目。",
                    ),
                    diagnosis="diagnosis",
                    why_it_matters="why",
                    next_action="补参考文献",
                    source_agent="WritingFormatAgent",
                    source_skill_version="writing-format-rubric@0.1.0",
                )
            ],
            debate_used=False,
        )
    )
    ledger.record_dimension_report(
        DimensionReport(
            dimension=Dimension.TOPIC_SCOPE,
            score=5.0,
            summary="topic summary",
            findings=[
                ReviewFinding(
                    dimension=Dimension.TOPIC_SCOPE,
                    issue_title="摘要没有明确点出研究问题",
                    severity=Severity.MEDIUM,
                    confidence=0.7,
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="abstract",
                        location_label="摘要",
                        quote="本文设计了一个系统。",
                    ),
                    diagnosis="diagnosis",
                    why_it_matters="why",
                    next_action="明确研究问题",
                    source_agent="TopicScopeAgent",
                    source_skill_version="topic-clarity-rubric@0.1.0",
                )
            ],
            debate_used=False,
        )
    )

    report = GuidanceComposer().compose(paper, ledger)

    assert report.priority_actions[0].dimension == Dimension.TOPIC_SCOPE
    assert report.priority_actions[1].dimension == Dimension.WRITING_FORMAT
    assert report.advisor_view.watch_points[0].startswith("研究内容：")


def test_guidance_composer_deduplicates_priority_actions() -> None:
    paper = PaperPackage(
        paper_id="demo",
        title="demo title",
        discipline=Discipline.COMPUTER_SCIENCE,
        stage=PaperStage.DRAFT,
    )
    duplicate_finding = ReviewFinding(
        dimension=Dimension.LOGIC_CHAIN,
        issue_title="论证链缺少明确的验证环节",
        severity=Severity.HIGH,
        confidence=0.8,
        evidence_anchor=EvidenceAnchor(
            anchor_id="sec-001",
            location_label="章节结构",
            quote="未识别到实验章节。",
        ),
        diagnosis="diagnosis",
        why_it_matters="why",
        next_action="补实验章节",
        source_agent="LogicChainAgent",
        source_skill_version="logic-chain-rubric@0.1.0",
    )
    ledger = EvidenceLedger()
    ledger.record_dimension_report(
        DimensionReport(
            dimension=Dimension.LOGIC_CHAIN,
            score=4.0,
            summary="logic summary",
            findings=[duplicate_finding, duplicate_finding],
            debate_used=False,
        )
    )

    report = GuidanceComposer().compose(paper, ledger)

    assert len(report.priority_actions) == 1
    assert report.student_guidance.next_steps == ["补实验章节"]
