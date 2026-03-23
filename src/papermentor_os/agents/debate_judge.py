from __future__ import annotations

from dataclasses import dataclass

from papermentor_os.schemas.debate import DebateCase, DebateResolution
from papermentor_os.schemas.report import DimensionReport, ReviewFinding
from papermentor_os.schemas.types import Severity


@dataclass(slots=True)
class DebateDecisionSnapshot:
    upheld_findings: list[ReviewFinding]
    dropped_findings: list[ReviewFinding]
    dropped_issue_reasons: dict[str, str]
    decision_policy_summary: str


class DebateJudgeAgent:
    agent_name = "DebateJudgeAgent"
    skill_version = "severity-resolution-rubric@0.1.0"
    confidence_uphold_threshold = 0.72

    def adjudicate(
        self,
        case: DebateCase,
        report: DimensionReport,
        *,
        skill_version: str | None = None,
    ) -> tuple[DimensionReport, DebateResolution]:
        effective_skill_version = skill_version or self.skill_version
        snapshot = self.inspect_case(case, report)
        upheld_findings = snapshot.upheld_findings
        dropped_findings = snapshot.dropped_findings

        adjusted_score = report.score
        if dropped_findings and not upheld_findings:
            adjusted_score = min(7.0, report.score + 0.5)
        elif upheld_findings and any(finding.severity == Severity.HIGH for finding in upheld_findings):
            adjusted_score = min(report.score, report.score)
        elif upheld_findings:
            adjusted_score = min(7.0, report.score + 0.2)

        resolution_summary = self._build_resolution_summary(case, upheld_findings, dropped_findings)
        updated_report = report.model_copy(
            update={
                "summary": f"{report.summary} 经 selective debate 复核：{resolution_summary}",
                "findings": upheld_findings or report.findings,
                "score": adjusted_score,
                "debate_used": True,
            }
        )
        resolution = DebateResolution(
            dimension=case.dimension,
            trigger_reason=case.trigger_reason,
            resolution_summary=resolution_summary,
            adjusted_score=adjusted_score,
            upheld_issue_titles=[finding.issue_title for finding in upheld_findings],
            dropped_issue_titles=[finding.issue_title for finding in dropped_findings],
            source_agent=self.agent_name,
            source_skill_version=effective_skill_version,
        )
        return updated_report, resolution

    def inspect_case(
        self,
        case: DebateCase,
        report: DimensionReport,
    ) -> DebateDecisionSnapshot:
        upheld, dropped, dropped_reasons = self._partition_findings(report.findings)
        policy_summary = (
            "保留高严重度问题，或保留置信度不低于 "
            f"{self.confidence_uphold_threshold:.2f} 的问题；其余问题在 debate 中降为待补证据项。"
        )
        return DebateDecisionSnapshot(
            upheld_findings=upheld,
            dropped_findings=dropped,
            dropped_issue_reasons=dropped_reasons,
            decision_policy_summary=policy_summary,
        )

    def _partition_findings(
        self,
        findings: list[ReviewFinding],
    ) -> tuple[list[ReviewFinding], list[ReviewFinding], dict[str, str]]:
        upheld: list[ReviewFinding] = []
        dropped: list[ReviewFinding] = []
        dropped_reasons: dict[str, str] = {}
        for finding in findings:
            if finding.severity == Severity.HIGH or finding.confidence >= self.confidence_uphold_threshold:
                upheld.append(finding)
            else:
                dropped.append(finding)
                dropped_reasons[finding.issue_title] = (
                    "未保留：严重度不是 HIGH，且置信度 "
                    f"{finding.confidence:.2f} 低于 {self.confidence_uphold_threshold:.2f}。"
                )
        return upheld, dropped, dropped_reasons

    def _build_resolution_summary(
        self,
        case: DebateCase,
        upheld_findings: list[ReviewFinding],
        dropped_findings: list[ReviewFinding],
    ) -> str:
        if upheld_findings and dropped_findings:
            return (
                f"保留 {len(upheld_findings)} 个主要问题，剔除 {len(dropped_findings)} 个低置信度问题；"
                f"触发原因是 {case.trigger_reason}。"
            )
        if upheld_findings:
            return f"保留现有主要问题判断；触发原因是 {case.trigger_reason}。"
        return f"未保留高置信度问题，建议后续补更多证据后再评审；触发原因是 {case.trigger_reason}。"
