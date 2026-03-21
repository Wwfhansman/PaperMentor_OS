from __future__ import annotations

from papermentor_os.schemas.debate import DebateCase
from papermentor_os.schemas.report import DimensionReport
from papermentor_os.schemas.types import Dimension, Severity


SUBJECTIVE_DIMENSIONS = {
    Dimension.LOGIC_CHAIN,
    Dimension.NOVELTY_DEPTH,
}

LOW_CONFIDENCE_THRESHOLD = 0.76
BORDERLINE_SCORE_MAX = 7.0
BORDERLINE_SCORE_MIN = 4.5


class DisagreementDetector:
    """Detect debate candidates before the actual debate layer is implemented."""

    def detect(self, reports: list[DimensionReport]) -> list[DebateCase]:
        candidates: list[DebateCase] = []
        for report in reports:
            if report.dimension not in SUBJECTIVE_DIMENSIONS:
                continue

            relevant_findings = [
                finding
                for finding in report.findings
                if finding.severity in {Severity.HIGH, Severity.MEDIUM}
            ]
            if not relevant_findings:
                continue

            confidence_floor = min(finding.confidence for finding in relevant_findings)
            is_borderline = BORDERLINE_SCORE_MIN <= report.score <= BORDERLINE_SCORE_MAX
            is_low_confidence = confidence_floor <= LOW_CONFIDENCE_THRESHOLD
            if not (is_borderline or is_low_confidence):
                continue

            reason_parts: list[str] = []
            if is_borderline:
                reason_parts.append("score is in the borderline band")
            if is_low_confidence:
                reason_parts.append("finding confidence is low")
            trigger_reason = " and ".join(reason_parts)

            candidates.append(
                DebateCase(
                    dimension=report.dimension,
                    trigger_reason=trigger_reason,
                    score=report.score,
                    confidence_floor=confidence_floor,
                    candidate_issue_titles=[finding.issue_title for finding in relevant_findings],
                    recommended_action="queue this dimension for selective debate once multi-review support is added",
                )
            )

        return candidates

