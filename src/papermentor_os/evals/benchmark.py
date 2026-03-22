from __future__ import annotations

from papermentor_os.evals.models import BenchmarkCaseResult, BenchmarkExpectation, BenchmarkSummary
from papermentor_os.schemas.debate import DebateCase
from papermentor_os.schemas.report import FinalReport
from papermentor_os.schemas.types import Dimension, Severity


class ReviewBenchmark:
    def evaluate_case(
        self,
        report: FinalReport,
        expectation: BenchmarkExpectation,
        *,
        debate_candidates: list[DebateCase] | None = None,
    ) -> BenchmarkCaseResult:
        actual_issue_titles = sorted(
            {
                finding.issue_title
                for dimension_report in report.dimension_reports
                for finding in dimension_report.findings
            }
        )
        actual_high_severity_dimensions = sorted(
            {
                finding.dimension
                for dimension_report in report.dimension_reports
                for finding in dimension_report.findings
                if finding.severity == Severity.HIGH
            },
            key=self._dimension_sort_key,
        )
        actual_debate_dimensions = sorted(
            {candidate.dimension for candidate in (debate_candidates or [])},
            key=self._dimension_sort_key,
        )
        actual_priority_first_dimension = (
            report.priority_actions[0].dimension if report.priority_actions else None
        )
        expected_issue_titles = sorted(set(expectation.expected_issue_titles))
        actual_issue_title_set = set(actual_issue_titles)
        expected_issue_title_set = set(expected_issue_titles)
        missing_issue_titles = sorted(expected_issue_title_set - actual_issue_title_set)
        unexpected_issue_titles = sorted(actual_issue_title_set - expected_issue_title_set)

        high_severity_recall = self._recall(
            expectation.expected_high_severity_dimensions,
            actual_high_severity_dimensions,
        )
        debate_recall = self._recall(
            expectation.expected_debate_dimensions,
            actual_debate_dimensions,
        )
        priority_match = None
        if expectation.expected_priority_first_dimension is not None:
            priority_match = actual_priority_first_dimension == expectation.expected_priority_first_dimension
        issue_title_recall = self._recall_strings(expected_issue_titles, actual_issue_titles)
        issue_title_false_positive_rate = self._false_positive_rate(
            expected_issue_titles,
            actual_issue_titles,
        )

        passed = (
            high_severity_recall == 1.0
            and debate_recall == 1.0
            and (priority_match is not False)
            and issue_title_recall == 1.0
            and issue_title_false_positive_rate == 0.0
        )

        return BenchmarkCaseResult(
            case_id=expectation.case_id,
            expected_high_severity_dimensions=expectation.expected_high_severity_dimensions,
            actual_high_severity_dimensions=actual_high_severity_dimensions,
            high_severity_dimension_recall=high_severity_recall,
            expected_priority_first_dimension=expectation.expected_priority_first_dimension,
            actual_priority_first_dimension=actual_priority_first_dimension,
            priority_first_dimension_match=priority_match,
            expected_debate_dimensions=expectation.expected_debate_dimensions,
            actual_debate_dimensions=actual_debate_dimensions,
            debate_dimension_recall=debate_recall,
            expected_issue_titles=expected_issue_titles,
            actual_issue_titles=actual_issue_titles,
            missing_issue_titles=missing_issue_titles,
            unexpected_issue_titles=unexpected_issue_titles,
            issue_title_recall=issue_title_recall,
            issue_title_false_positive_rate=issue_title_false_positive_rate,
            passed=passed,
        )

    def summarize(self, case_results: list[BenchmarkCaseResult]) -> BenchmarkSummary:
        total_cases = len(case_results)
        fully_passed_cases = sum(1 for result in case_results if result.passed)

        high_expected_total = sum(len(result.expected_high_severity_dimensions) for result in case_results)
        high_expected_hit = sum(
            len(set(result.expected_high_severity_dimensions) & set(result.actual_high_severity_dimensions))
            for result in case_results
        )
        debate_expected_total = sum(len(result.expected_debate_dimensions) for result in case_results)
        debate_expected_hit = sum(
            len(set(result.expected_debate_dimensions) & set(result.actual_debate_dimensions))
            for result in case_results
        )

        priority_expected_results = [
            result for result in case_results if result.expected_priority_first_dimension is not None
        ]
        priority_hit = sum(
            1 for result in priority_expected_results if result.priority_first_dimension_match
        )
        issue_expected_total = sum(len(result.expected_issue_titles) for result in case_results)
        issue_expected_hit = sum(
            len(set(result.expected_issue_titles) & set(result.actual_issue_titles))
            for result in case_results
        )
        issue_actual_total = sum(len(result.actual_issue_titles) for result in case_results)
        issue_unexpected_total = sum(len(result.unexpected_issue_titles) for result in case_results)

        return BenchmarkSummary(
            total_cases=total_cases,
            fully_passed_cases=fully_passed_cases,
            high_severity_dimension_recall=(
                high_expected_hit / high_expected_total if high_expected_total else 1.0
            ),
            priority_first_dimension_accuracy=(
                priority_hit / len(priority_expected_results) if priority_expected_results else 1.0
            ),
            debate_dimension_recall=(
                debate_expected_hit / debate_expected_total if debate_expected_total else 1.0
            ),
            issue_title_recall=(
                issue_expected_hit / issue_expected_total if issue_expected_total else 1.0
            ),
            issue_title_false_positive_rate=(
                issue_unexpected_total / issue_actual_total if issue_actual_total else 0.0
            ),
            case_results=case_results,
        )

    def _recall(
        self,
        expected_dimensions: list[Dimension],
        actual_dimensions: list[Dimension],
    ) -> float:
        if not expected_dimensions:
            return 1.0
        expected_set = set(expected_dimensions)
        actual_set = set(actual_dimensions)
        return len(expected_set & actual_set) / len(expected_set)

    def _dimension_sort_key(self, dimension: Dimension) -> str:
        return dimension.value

    def _recall_strings(
        self,
        expected_values: list[str],
        actual_values: list[str],
    ) -> float:
        if not expected_values:
            return 1.0
        expected_set = set(expected_values)
        actual_set = set(actual_values)
        return len(expected_set & actual_set) / len(expected_set)

    def _false_positive_rate(
        self,
        expected_values: list[str],
        actual_values: list[str],
    ) -> float:
        if not actual_values:
            return 0.0
        expected_set = set(expected_values)
        actual_set = set(actual_values)
        return len(actual_set - expected_set) / len(actual_set)
