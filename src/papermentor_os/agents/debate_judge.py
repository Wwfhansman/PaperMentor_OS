from __future__ import annotations

from papermentor_os.schemas.debate import DebateCase, DebateResolution
from papermentor_os.schemas.report import DimensionReport, ReviewFinding
from papermentor_os.schemas.types import Severity


class DebateJudgeAgent:
    agent_name = "DebateJudgeAgent"
    skill_version = "severity-resolution-rubric@0.1.0"

    def adjudicate(
        self,
        case: DebateCase,
        report: DimensionReport,
        *,
        skill_version: str | None = None,
    ) -> tuple[DimensionReport, DebateResolution]:
        effective_skill_version = skill_version or self.skill_version
        upheld_findings, dropped_findings = self._partition_findings(report.findings)

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

    def _partition_findings(
        self,
        findings: list[ReviewFinding],
    ) -> tuple[list[ReviewFinding], list[ReviewFinding]]:
        upheld: list[ReviewFinding] = []
        dropped: list[ReviewFinding] = []
        for finding in findings:
            if finding.severity == Severity.HIGH or finding.confidence >= 0.72:
                upheld.append(finding)
            else:
                dropped.append(finding)
        return upheld, dropped

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
