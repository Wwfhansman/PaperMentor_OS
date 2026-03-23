from __future__ import annotations

from papermentor_os.evals.models import (
    BenchmarkCaseResult,
    BenchmarkExpectation,
    BenchmarkPricingConfig,
    BenchmarkSummary,
)
from papermentor_os.schemas.debate import DebateCase
from papermentor_os.schemas.report import FinalReport
from papermentor_os.schemas.trace import OrchestrationTrace, WorkerExecutionTrace
from papermentor_os.schemas.types import Dimension, Severity


class ReviewBenchmark:
    def evaluate_case(
        self,
        report: FinalReport,
        expectation: BenchmarkExpectation,
        *,
        debate_candidates: list[DebateCase] | None = None,
        worker_execution_traces: list[WorkerExecutionTrace] | None = None,
        orchestration_trace: OrchestrationTrace | None = None,
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

        llm_request_attempts = sum(
            trace.llm_request_attempts for trace in (worker_execution_traces or [])
        )
        llm_retry_count = sum(trace.llm_retry_count for trace in (worker_execution_traces or []))
        llm_fallback_count = sum(
            1 for trace in (worker_execution_traces or []) if trace.fallback_used
        )
        llm_error_count = sum(
            1
            for trace in (worker_execution_traces or [])
            if trace.review_backend != "rule_only" and trace.structured_output_status != "parsed"
        )
        llm_error_categories = self._count_error_categories(worker_execution_traces or [])
        llm_usage_observation_count = sum(
            1 for trace in (worker_execution_traces or []) if trace.llm_total_tokens is not None
        )
        llm_prompt_tokens = sum((trace.llm_prompt_tokens or 0) for trace in (worker_execution_traces or []))
        llm_completion_tokens = sum(
            (trace.llm_completion_tokens or 0) for trace in (worker_execution_traces or [])
        )
        llm_total_tokens = sum((trace.llm_total_tokens or 0) for trace in (worker_execution_traces or []))

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
            llm_request_attempts=llm_request_attempts,
            llm_retry_count=llm_retry_count,
            llm_fallback_count=llm_fallback_count,
            llm_error_count=llm_error_count,
            llm_error_categories=llm_error_categories,
            llm_usage_observation_count=llm_usage_observation_count,
            llm_prompt_tokens=llm_prompt_tokens,
            llm_completion_tokens=llm_completion_tokens,
            llm_total_tokens=llm_total_tokens,
            resumed_from_checkpoint=(
                orchestration_trace.resumed_from_checkpoint if orchestration_trace is not None else False
            ),
            checkpoint_completed_worker_count=(
                orchestration_trace.checkpoint_completed_worker_count if orchestration_trace is not None else 0
            ),
            skipped_worker_count=(
                len(orchestration_trace.skipped_worker_ids) if orchestration_trace is not None else 0
            ),
            passed=passed,
        )

    def summarize(self, case_results: list[BenchmarkCaseResult]) -> BenchmarkSummary:
        return self.summarize_variant(case_results)

    def summarize_variant(
        self,
        case_results: list[BenchmarkCaseResult],
        *,
        variant_id: str = "rule",
        review_backend: str | None = None,
        expectation_override_case_count: int = 0,
        llm_provider_id: str | None = None,
        llm_model_name: str | None = None,
        elapsed_seconds: float = 0.0,
        average_case_duration_ms: float = 0.0,
        pricing_config: BenchmarkPricingConfig | None = None,
    ) -> BenchmarkSummary:
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
        llm_request_attempts = sum(result.llm_request_attempts for result in case_results)
        llm_retry_count = sum(result.llm_retry_count for result in case_results)
        llm_fallback_count = sum(result.llm_fallback_count for result in case_results)
        llm_error_count = sum(result.llm_error_count for result in case_results)
        llm_error_categories = self._merge_error_category_counts(case_results)
        llm_usage_observation_count = sum(result.llm_usage_observation_count for result in case_results)
        llm_prompt_tokens = sum(result.llm_prompt_tokens for result in case_results)
        llm_completion_tokens = sum(result.llm_completion_tokens for result in case_results)
        llm_total_tokens = sum(result.llm_total_tokens for result in case_results)
        resumed_case_count = sum(1 for result in case_results if result.resumed_from_checkpoint)
        checkpoint_completed_worker_count = sum(
            result.checkpoint_completed_worker_count for result in case_results
        )
        skipped_worker_count = sum(result.skipped_worker_count for result in case_results)
        llm_input_cost_estimate_usd = None
        llm_output_cost_estimate_usd = None
        llm_total_cost_estimate_usd = None
        if pricing_config is not None:
            llm_input_cost_estimate_usd = (
                llm_prompt_tokens / 1000.0
            ) * pricing_config.input_price_per_1k_tokens_usd
            llm_output_cost_estimate_usd = (
                llm_completion_tokens / 1000.0
            ) * pricing_config.output_price_per_1k_tokens_usd
            llm_total_cost_estimate_usd = (
                llm_input_cost_estimate_usd + llm_output_cost_estimate_usd
            )

        return BenchmarkSummary(
            variant_id=variant_id,
            review_backend=review_backend or "rule_only",
            expectation_override_case_count=expectation_override_case_count,
            llm_provider_id=llm_provider_id,
            llm_model_name=llm_model_name,
            elapsed_seconds=elapsed_seconds,
            average_case_duration_ms=average_case_duration_ms,
            llm_request_attempts=llm_request_attempts,
            llm_retry_count=llm_retry_count,
            llm_fallback_count=llm_fallback_count,
            llm_error_count=llm_error_count,
            llm_error_categories=llm_error_categories,
            llm_usage_observation_count=llm_usage_observation_count,
            llm_prompt_tokens=llm_prompt_tokens,
            llm_completion_tokens=llm_completion_tokens,
            llm_total_tokens=llm_total_tokens,
            resumed_case_count=resumed_case_count,
            checkpoint_completed_worker_count=checkpoint_completed_worker_count,
            skipped_worker_count=skipped_worker_count,
            llm_input_cost_estimate_usd=llm_input_cost_estimate_usd,
            llm_output_cost_estimate_usd=llm_output_cost_estimate_usd,
            llm_total_cost_estimate_usd=llm_total_cost_estimate_usd,
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

    def _count_error_categories(
        self,
        worker_execution_traces: list[WorkerExecutionTrace],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for trace in worker_execution_traces:
            if not trace.llm_error_category:
                continue
            counts[trace.llm_error_category] = counts.get(trace.llm_error_category, 0) + 1
        return counts

    def _merge_error_category_counts(
        self,
        case_results: list[BenchmarkCaseResult],
    ) -> dict[str, int]:
        merged: dict[str, int] = {}
        for result in case_results:
            for category, count in result.llm_error_categories.items():
                merged[category] = merged.get(category, 0) + count
        return merged
