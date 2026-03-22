from scripts.run_benchmark import main, run_benchmark


def test_run_benchmark_returns_summary_for_evaluation_fixtures() -> None:
    payload = run_benchmark()

    assert payload["total_cases"] >= 11
    assert "issue_title_recall" in payload
    assert "issue_title_false_positive_rate" in payload
    assert "case_results" in payload
    case_ids = {item["case_id"] for item in payload["case_results"]}
    assert "contents_variation_case" in case_ids
    assert "cover_page_variation_case" in case_ids
    assert "literature_precision_case" in case_ids
    assert "logic_precision_case" in case_ids
    assert "novelty_precision_case" in case_ids
    assert "template_variation_case" in case_ids
    assert "writing_precision_case" in case_ids
    assert "strong_review_case" in case_ids
    assert "topic_precision_case" in case_ids
    assert "weak_review_case" in case_ids
    assert "boundary_review_case" in case_ids


def test_run_benchmark_supports_markdown_output(capsys, monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["run_benchmark.py", "--format", "markdown"])

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "# PaperMentor OS Benchmark" in captured.out


def test_run_benchmark_returns_failure_code_when_threshold_is_not_met(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["run_benchmark.py", "--min-issue-title-recall", "1.1"],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Invalid threshold value." in captured.out


def test_run_benchmark_returns_regression_exit_code_when_gate_fails(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.run_benchmark.run_benchmark",
        lambda tag="evaluation_fixture": {
            "total_cases": 1,
            "fully_passed_cases": 0,
            "high_severity_dimension_recall": 0.8,
            "priority_first_dimension_accuracy": 1.0,
            "debate_dimension_recall": 0.5,
            "issue_title_recall": 0.7,
            "issue_title_false_positive_rate": 0.2,
            "case_results": [],
        },
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_benchmark.py",
            "--max-issue-title-fpr",
            "0.1",
            "--min-issue-title-recall",
            "0.9",
            "--min-debate-recall",
            "0.8",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "failed_checks" in captured.out
