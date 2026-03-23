from __future__ import annotations

from tests.fixtures.review_cases import (
    BenchmarkExpectationOverride,
    ReviewCaseSpec,
    get_review_cases_by_tag,
)

from papermentor_os.evals.models import BenchmarkExpectation


def build_expectation_from_case(
    case: ReviewCaseSpec,
    *,
    variant_id: str = "rule",
) -> BenchmarkExpectation:
    override = _resolve_expectation_override(case, variant_id)
    return BenchmarkExpectation(
        case_id=case.case_id,
        expected_high_severity_dimensions=list(
            override.expected_high_severity_dimensions
            if override is not None and override.expected_high_severity_dimensions is not None
            else case.expected_high_severity_dimensions
        ),
        expected_priority_first_dimension=(
            override.expected_priority_first_dimension
            if override is not None and override.expected_priority_first_dimension is not None
            else case.expected_priority_first_dimension
        ),
        expected_debate_dimensions=list(
            override.expected_debate_dimensions
            if override is not None and override.expected_debate_dimensions is not None
            else case.expected_debate_dimensions
        ),
        expected_issue_titles=list(
            override.expected_issue_titles
            if override is not None and override.expected_issue_titles is not None
            else case.expected_issue_titles
        ),
    )


def load_benchmark_cases(*, tag: str = "evaluation_fixture") -> tuple[ReviewCaseSpec, ...]:
    return get_review_cases_by_tag(tag)


def case_has_expectation_override(
    case: ReviewCaseSpec,
    *,
    variant_id: str,
) -> bool:
    return _resolve_expectation_override(case, variant_id) is not None


def _resolve_expectation_override(
    case: ReviewCaseSpec,
    variant_id: str,
) -> BenchmarkExpectationOverride | None:
    for override in case.benchmark_expectation_overrides:
        if override.variant_id == variant_id:
            return override
    return None
