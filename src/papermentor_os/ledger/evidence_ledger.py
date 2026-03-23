from __future__ import annotations

from papermentor_os.schemas.debate import DebateResolution
from papermentor_os.schemas.report import DimensionReport, ReviewFinding
from papermentor_os.schemas.trace import WorkerExecutionMetadata
from papermentor_os.schemas.types import Dimension, Severity


SEVERITY_ORDER = {
    Severity.HIGH: 0,
    Severity.MEDIUM: 1,
    Severity.LOW: 2,
}

DIMENSION_PRIORITY = {
    Dimension.TOPIC_SCOPE: 0,
    Dimension.LOGIC_CHAIN: 1,
    Dimension.LITERATURE_SUPPORT: 2,
    Dimension.NOVELTY_DEPTH: 3,
    Dimension.WRITING_FORMAT: 4,
}


class EvidenceLedger:
    def __init__(self) -> None:
        self._dimension_reports: dict[Dimension, DimensionReport] = {}
        self._debate_results: dict[Dimension, DebateResolution] = {}
        self._execution_metadata: dict[Dimension, WorkerExecutionMetadata] = {}

    def record_dimension_report(
        self,
        report: DimensionReport,
        execution_metadata: WorkerExecutionMetadata | None = None,
    ) -> None:
        self._dimension_reports[report.dimension] = report
        if execution_metadata is not None:
            self._execution_metadata[report.dimension] = execution_metadata

    def record_debate_result(
        self,
        resolution: DebateResolution,
        updated_report: DimensionReport,
    ) -> None:
        self._debate_results[resolution.dimension] = resolution
        self._dimension_reports[resolution.dimension] = updated_report

    def get_dimension_reports(self) -> list[DimensionReport]:
        return [
            self._dimension_reports[dimension]
            for dimension in sorted(
                self._dimension_reports,
                key=lambda dimension: DIMENSION_PRIORITY[dimension],
            )
        ]

    def get_all_findings(self) -> list[ReviewFinding]:
        findings: list[ReviewFinding] = []
        for report in self.get_dimension_reports():
            findings.extend(report.findings)
        return findings

    def get_debate_results(self) -> list[DebateResolution]:
        return [
            self._debate_results[dimension]
            for dimension in sorted(
                self._debate_results,
                key=lambda dimension: DIMENSION_PRIORITY[dimension],
            )
        ]

    def get_execution_metadata(self, dimension: Dimension) -> WorkerExecutionMetadata | None:
        return self._execution_metadata.get(dimension)

    def get_findings_by_priority(self, limit: int | None = None) -> list[ReviewFinding]:
        findings = sorted(
            self.get_all_findings(),
            key=lambda finding: (
                SEVERITY_ORDER[finding.severity],
                DIMENSION_PRIORITY[finding.dimension],
                -finding.confidence,
            ),
        )
        if limit is None:
            return findings
        return findings[:limit]
