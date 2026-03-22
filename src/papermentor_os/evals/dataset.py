from __future__ import annotations

from tests.fixtures.review_cases import ReviewCaseSpec, get_review_cases_by_tag

from papermentor_os.evals.models import BenchmarkExpectation


def build_expectation_from_case(case: ReviewCaseSpec) -> BenchmarkExpectation:
    return BenchmarkExpectation(
        case_id=case.case_id,
        expected_high_severity_dimensions=list(case.expected_high_severity_dimensions),
        expected_priority_first_dimension=case.expected_priority_first_dimension,
        expected_debate_dimensions=list(case.expected_debate_dimensions),
        expected_issue_titles=list(case.expected_issue_titles),
    )


def load_benchmark_cases(*, tag: str = "evaluation_fixture") -> tuple[ReviewCaseSpec, ...]:
    return get_review_cases_by_tag(tag)
