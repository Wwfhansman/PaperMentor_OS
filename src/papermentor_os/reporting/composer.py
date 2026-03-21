from __future__ import annotations

from papermentor_os.ledger.evidence_ledger import EvidenceLedger
from papermentor_os.schemas.paper import PaperPackage
from papermentor_os.schemas.report import (
    AdvisorView,
    FinalReport,
    PriorityAction,
    ReviewFinding,
    StudentGuidance,
)
from papermentor_os.schemas.types import Dimension, Severity


RESEARCH_DIMENSIONS = {
    Dimension.TOPIC_SCOPE,
    Dimension.LOGIC_CHAIN,
    Dimension.LITERATURE_SUPPORT,
    Dimension.NOVELTY_DEPTH,
}

WRITING_DIMENSIONS = {
    Dimension.WRITING_FORMAT,
}

SEVERITY_ORDER = {
    Severity.HIGH: 0,
    Severity.MEDIUM: 1,
    Severity.LOW: 2,
}

DIMENSION_ORDER = {
    Dimension.TOPIC_SCOPE: 0,
    Dimension.LOGIC_CHAIN: 1,
    Dimension.LITERATURE_SUPPORT: 2,
    Dimension.NOVELTY_DEPTH: 3,
    Dimension.WRITING_FORMAT: 4,
}


class GuidanceComposer:
    def compose(self, paper: PaperPackage, ledger: EvidenceLedger) -> FinalReport:
        dimension_reports = ledger.get_dimension_reports()
        all_findings = ledger.get_all_findings()
        priority_findings = self._build_priority_findings(all_findings, limit=3)

        if priority_findings:
            issue_titles = "；".join(finding.issue_title for finding in priority_findings)
            overall_summary = (
                f"《{paper.title}》已完成最小链路评审。当前最优先处理的问题集中在：{issue_titles}。"
            )
        else:
            overall_summary = f"《{paper.title}》已完成最小链路评审，当前未发现明显高优先级问题。"

        priority_actions = [
            PriorityAction(
                title=finding.issue_title,
                severity=finding.severity,
                dimension=finding.dimension,
                why_it_matters=finding.why_it_matters,
                next_action=finding.next_action,
                anchor_id=finding.evidence_anchor.anchor_id,
            )
            for finding in priority_findings
        ]

        student_guidance = StudentGuidance(
            next_steps=self._build_student_guidance(priority_findings)
        )

        high_risk_count = sum(1 for finding in all_findings if finding.severity == Severity.HIGH)
        research_issue_count = sum(1 for finding in all_findings if finding.dimension in RESEARCH_DIMENSIONS)
        writing_issue_count = sum(1 for finding in all_findings if finding.dimension in WRITING_DIMENSIONS)
        advisor_view = AdvisorView(
            quick_summary=(
                f"当前共识别 {len(all_findings)} 个问题，其中高严重度 {high_risk_count} 个；"
                f"研究内容类 {research_issue_count} 个，写作规范类 {writing_issue_count} 个。"
            ),
            watch_points=self._build_watch_points(priority_findings),
        )

        return FinalReport(
            overall_summary=overall_summary,
            dimension_reports=dimension_reports,
            priority_actions=priority_actions,
            student_guidance=student_guidance,
            advisor_view=advisor_view,
            safety_notice="本系统默认处于 review mode，输出诊断与修改建议，不直接代写正文。",
        )

    def _build_priority_findings(self, findings: list[ReviewFinding], limit: int) -> list[ReviewFinding]:
        deduplicated = self._deduplicate_findings(findings)
        ordered = sorted(
            deduplicated,
            key=lambda finding: (
                self._report_category_priority(finding.dimension),
                SEVERITY_ORDER[finding.severity],
                DIMENSION_ORDER[finding.dimension],
                -finding.confidence,
            ),
        )
        return ordered[:limit]

    def _deduplicate_findings(self, findings: list[ReviewFinding]) -> list[ReviewFinding]:
        deduplicated: list[ReviewFinding] = []
        seen_keys: set[tuple[Dimension, str, str]] = set()
        for finding in findings:
            key = (
                finding.dimension,
                finding.issue_title.strip(),
                finding.evidence_anchor.anchor_id,
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            deduplicated.append(finding)
        return deduplicated

    def _build_student_guidance(self, priority_findings: list[ReviewFinding]) -> list[str]:
        if not priority_findings:
            return ["继续完善摘要、章节和参考文献，让论文结构更完整。"]

        next_steps: list[str] = []
        seen_actions: set[str] = set()
        for finding in priority_findings:
            action = finding.next_action.strip()
            if action in seen_actions:
                continue
            seen_actions.add(action)
            next_steps.append(action)
        return next_steps

    def _build_watch_points(self, priority_findings: list[ReviewFinding]) -> list[str]:
        watch_points: list[str] = []
        for finding in priority_findings:
            category_label = "研究内容" if finding.dimension in RESEARCH_DIMENSIONS else "写作规范"
            watch_points.append(f"{category_label}：{finding.issue_title}（{finding.dimension.value}）")
        return watch_points

    def _report_category_priority(self, dimension: Dimension) -> int:
        if dimension in RESEARCH_DIMENSIONS:
            return 0
        return 1
