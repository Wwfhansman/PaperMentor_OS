from __future__ import annotations

from papermentor_os.evals.models import BenchmarkGateResult, BenchmarkSummary, BenchmarkThresholds


def evaluate_benchmark_thresholds(
    summary: BenchmarkSummary,
    thresholds: BenchmarkThresholds,
) -> BenchmarkGateResult:
    failed_checks: list[str] = []

    if (
        thresholds.min_high_severity_dimension_recall is not None
        and summary.high_severity_dimension_recall < thresholds.min_high_severity_dimension_recall
    ):
        failed_checks.append(
            "high_severity_dimension_recall "
            f"{summary.high_severity_dimension_recall:.2f} < {thresholds.min_high_severity_dimension_recall:.2f}"
        )

    if (
        thresholds.min_priority_first_dimension_accuracy is not None
        and summary.priority_first_dimension_accuracy < thresholds.min_priority_first_dimension_accuracy
    ):
        failed_checks.append(
            "priority_first_dimension_accuracy "
            f"{summary.priority_first_dimension_accuracy:.2f} < {thresholds.min_priority_first_dimension_accuracy:.2f}"
        )

    if (
        thresholds.min_debate_dimension_recall is not None
        and summary.debate_dimension_recall < thresholds.min_debate_dimension_recall
    ):
        failed_checks.append(
            "debate_dimension_recall "
            f"{summary.debate_dimension_recall:.2f} < {thresholds.min_debate_dimension_recall:.2f}"
        )

    if (
        thresholds.min_issue_title_recall is not None
        and summary.issue_title_recall < thresholds.min_issue_title_recall
    ):
        failed_checks.append(
            "issue_title_recall "
            f"{summary.issue_title_recall:.2f} < {thresholds.min_issue_title_recall:.2f}"
        )

    if (
        thresholds.max_issue_title_false_positive_rate is not None
        and summary.issue_title_false_positive_rate > thresholds.max_issue_title_false_positive_rate
    ):
        failed_checks.append(
            "issue_title_false_positive_rate "
            f"{summary.issue_title_false_positive_rate:.2f} > {thresholds.max_issue_title_false_positive_rate:.2f}"
        )

    return BenchmarkGateResult(
        passed=not failed_checks,
        failed_checks=failed_checks,
    )
