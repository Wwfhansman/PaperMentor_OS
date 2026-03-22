from papermentor_os.evals import build_expectation_from_case, load_benchmark_cases, render_benchmark_markdown
from papermentor_os.evals.models import BenchmarkSummary
from tests.fixtures.review_cases import WEAK_REVIEW_CASE


def test_build_expectation_from_case_includes_issue_titles() -> None:
    expectation = build_expectation_from_case(WEAK_REVIEW_CASE)

    assert expectation.case_id == WEAK_REVIEW_CASE.case_id
    assert "摘要没有明确点出研究问题" in expectation.expected_issue_titles


def test_load_benchmark_cases_filters_by_tag() -> None:
    cases = load_benchmark_cases(tag="evaluation_fixture")

    case_ids = {case.case_id for case in cases}
    assert "strong_review_case" in case_ids
    assert "weak_review_case" in case_ids
    assert "boundary_review_case" in case_ids


def test_render_benchmark_markdown_outputs_readable_summary() -> None:
    markdown = render_benchmark_markdown(
        BenchmarkSummary(
            total_cases=1,
            fully_passed_cases=1,
            high_severity_dimension_recall=1.0,
            priority_first_dimension_accuracy=1.0,
            debate_dimension_recall=1.0,
            issue_title_recall=1.0,
            issue_title_false_positive_rate=0.0,
            case_results=[],
        )
    )

    assert "# PaperMentor OS Benchmark" in markdown
    assert "High severity dimension recall: 1.00" in markdown
