from papermentor_os.agents.debate_judge import DebateJudgeAgent
from papermentor_os.schemas.debate import DebateCase
from papermentor_os.schemas.report import DimensionReport, EvidenceAnchor, ReviewFinding
from papermentor_os.schemas.types import Dimension, Severity


def test_debate_judge_marks_report_as_debated_and_keeps_high_confidence_findings() -> None:
    report = DimensionReport(
        dimension=Dimension.LOGIC_CHAIN,
        score=6.0,
        summary="logic summary",
        findings=[
            ReviewFinding(
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
                next_action="action",
                source_agent="LogicChainAgent",
                source_skill_version="logic-chain-rubric@0.1.0",
            ),
            ReviewFinding(
                dimension=Dimension.LOGIC_CHAIN,
                issue_title="缺少显式结论章节，论证收束不足",
                severity=Severity.MEDIUM,
                confidence=0.6,
                evidence_anchor=EvidenceAnchor(
                    anchor_id="sec-002",
                    location_label="结尾部分",
                    quote="2 系统设计",
                ),
                diagnosis="diagnosis",
                why_it_matters="why",
                next_action="action",
                source_agent="LogicChainAgent",
                source_skill_version="logic-chain-rubric@0.1.0",
            ),
        ],
        debate_used=False,
    )
    case = DebateCase(
        dimension=Dimension.LOGIC_CHAIN,
        trigger_reason="score is in the borderline band",
        score=6.0,
        confidence_floor=0.6,
        candidate_issue_titles=[finding.issue_title for finding in report.findings],
        recommended_action="queue this dimension for selective debate once multi-review support is added",
    )

    updated_report, resolution = DebateJudgeAgent().adjudicate(case, report)

    assert updated_report.debate_used is True
    assert len(updated_report.findings) == 1
    assert resolution.upheld_issue_titles == ["论证链缺少明确的验证环节"]
    assert resolution.dropped_issue_titles == ["缺少显式结论章节，论证收束不足"]


def test_debate_judge_can_explain_why_low_confidence_finding_was_dropped() -> None:
    report = DimensionReport(
        dimension=Dimension.LOGIC_CHAIN,
        score=6.0,
        summary="logic summary",
        findings=[
            ReviewFinding(
                dimension=Dimension.LOGIC_CHAIN,
                issue_title="缺少显式结论章节，论证收束不足",
                severity=Severity.MEDIUM,
                confidence=0.6,
                evidence_anchor=EvidenceAnchor(
                    anchor_id="sec-002",
                    location_label="结尾部分",
                    quote="2 系统设计",
                ),
                diagnosis="diagnosis",
                why_it_matters="why",
                next_action="action",
                source_agent="LogicChainAgent",
                source_skill_version="logic-chain-rubric@0.1.0",
            ),
        ],
        debate_used=False,
    )
    case = DebateCase(
        dimension=Dimension.LOGIC_CHAIN,
        trigger_reason="score is in the borderline band",
        score=6.0,
        confidence_floor=0.6,
        candidate_issue_titles=[finding.issue_title for finding in report.findings],
        recommended_action="queue this dimension for selective debate once multi-review support is added",
    )

    snapshot = DebateJudgeAgent().inspect_case(case, report)

    assert snapshot.decision_policy_summary
    assert snapshot.dropped_issue_reasons == {
        "缺少显式结论章节，论证收束不足": "未保留：严重度不是 HIGH，且置信度 0.60 低于 0.72。"
    }
