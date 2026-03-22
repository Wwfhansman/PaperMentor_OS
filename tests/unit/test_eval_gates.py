from papermentor_os.evals import BenchmarkSummary, BenchmarkThresholds, evaluate_benchmark_thresholds


def test_evaluate_benchmark_thresholds_passes_when_metrics_meet_thresholds() -> None:
    summary = BenchmarkSummary(
        total_cases=3,
        fully_passed_cases=3,
        high_severity_dimension_recall=1.0,
        priority_first_dimension_accuracy=1.0,
        debate_dimension_recall=1.0,
        issue_title_recall=1.0,
        issue_title_false_positive_rate=0.0,
        case_results=[],
    )
    thresholds = BenchmarkThresholds(
        min_high_severity_dimension_recall=0.9,
        min_issue_title_recall=0.9,
        max_issue_title_false_positive_rate=0.1,
    )

    result = evaluate_benchmark_thresholds(summary, thresholds)

    assert result.passed is True
    assert result.failed_checks == []


def test_evaluate_benchmark_thresholds_collects_all_failed_checks() -> None:
    summary = BenchmarkSummary(
        total_cases=3,
        fully_passed_cases=1,
        high_severity_dimension_recall=0.7,
        priority_first_dimension_accuracy=0.6,
        debate_dimension_recall=0.5,
        issue_title_recall=0.8,
        issue_title_false_positive_rate=0.3,
        case_results=[],
    )
    thresholds = BenchmarkThresholds(
        min_high_severity_dimension_recall=0.9,
        min_priority_first_dimension_accuracy=0.8,
        min_debate_dimension_recall=0.7,
        min_issue_title_recall=0.9,
        max_issue_title_false_positive_rate=0.1,
    )

    result = evaluate_benchmark_thresholds(summary, thresholds)

    assert result.passed is False
    assert len(result.failed_checks) == 5
