from __future__ import annotations

from papermentor_os.evals.models import BenchmarkCaseResult, BenchmarkComparison, BenchmarkSummary


def render_benchmark_markdown(summary: BenchmarkSummary) -> str:
    lines = [
        "# PaperMentor OS Benchmark",
        "",
        f"- Variant: `{summary.variant_id}`",
        f"- Review backend: `{summary.review_backend.value}`",
    ]
    if summary.expectation_override_case_count > 0:
        lines.append(f"- Expectation override cases: {summary.expectation_override_case_count}")
    if summary.llm_provider_id:
        lines.append(f"- LLM provider: `{summary.llm_provider_id}`")
    if summary.llm_model_name:
        lines.append(f"- LLM model: `{summary.llm_model_name}`")
    lines.extend(
        [
            f"- Elapsed seconds: {summary.elapsed_seconds:.2f}",
            f"- Average case duration ms: {summary.average_case_duration_ms:.2f}",
        ]
    )
    if summary.llm_request_attempts > 0:
        lines.extend(
            [
                f"- LLM request attempts: {summary.llm_request_attempts}",
                f"- LLM retry count: {summary.llm_retry_count}",
                f"- LLM fallback count: {summary.llm_fallback_count}",
                f"- LLM error count: {summary.llm_error_count}",
            ]
        )
        if summary.llm_error_categories:
            category_summary = ", ".join(
                f"{category}={count}" for category, count in sorted(summary.llm_error_categories.items())
            )
            lines.append(f"- LLM error categories: {category_summary}")
    if summary.llm_usage_observation_count > 0:
        lines.extend(
            [
                f"- LLM usage observations: {summary.llm_usage_observation_count}",
                f"- LLM prompt tokens: {summary.llm_prompt_tokens}",
                f"- LLM completion tokens: {summary.llm_completion_tokens}",
                f"- LLM total tokens: {summary.llm_total_tokens}",
            ]
        )
        if summary.llm_total_cost_estimate_usd is not None:
            lines.extend(
                [
                    f"- LLM input cost estimate usd: {summary.llm_input_cost_estimate_usd:.6f}",
                    f"- LLM output cost estimate usd: {summary.llm_output_cost_estimate_usd:.6f}",
                    f"- LLM total cost estimate usd: {summary.llm_total_cost_estimate_usd:.6f}",
                ]
            )
    if summary.resumed_case_count > 0:
        lines.extend(
            [
                f"- Resumed cases: {summary.resumed_case_count}",
                f"- Checkpoint completed workers: {summary.checkpoint_completed_worker_count}",
                f"- Skipped workers via resume: {summary.skipped_worker_count}",
            ]
        )
    lines.extend(
        [
        f"- Total cases: {summary.total_cases}",
        f"- Fully passed cases: {summary.fully_passed_cases}",
        f"- High severity dimension recall: {summary.high_severity_dimension_recall:.2f}",
        f"- Priority first dimension accuracy: {summary.priority_first_dimension_accuracy:.2f}",
        f"- Debate dimension recall: {summary.debate_dimension_recall:.2f}",
        f"- Issue title recall: {summary.issue_title_recall:.2f}",
        f"- Issue title false positive rate: {summary.issue_title_false_positive_rate:.2f}",
        "",
        "## Case Results",
        "",
        ]
    )
    for case_result in summary.case_results:
        lines.extend(_render_case_result(case_result))
    return "\n".join(lines)


def render_benchmark_comparison_markdown(comparison: BenchmarkComparison) -> str:
    lines = [
        "# PaperMentor OS Benchmark Comparison",
        "",
    ]
    if comparison.gate_variant_id:
        lines.append(f"- Gate variant: `{comparison.gate_variant_id}`")
        lines.append("")

    for index, summary in enumerate(comparison.variant_summaries):
        if index > 0:
            lines.append("---")
            lines.append("")
        lines.extend(render_benchmark_markdown(summary).splitlines())
    return "\n".join(lines)


def _render_case_result(case_result: BenchmarkCaseResult) -> list[str]:
    status = "PASS" if case_result.passed else "FAIL"
    lines = [
        f"### {case_result.case_id} [{status}]",
        "",
        f"- High severity recall: {case_result.high_severity_dimension_recall:.2f}",
        f"- Debate recall: {case_result.debate_dimension_recall:.2f}",
        f"- Issue title recall: {case_result.issue_title_recall:.2f}",
        f"- Issue title false positive rate: {case_result.issue_title_false_positive_rate:.2f}",
    ]
    if case_result.expected_priority_first_dimension is not None:
        lines.append(
            f"- Priority first dimension: expected `{case_result.expected_priority_first_dimension.value}`, actual `{case_result.actual_priority_first_dimension.value if case_result.actual_priority_first_dimension else 'none'}`"
        )
    if case_result.llm_request_attempts > 0:
        lines.append(f"- LLM request attempts: {case_result.llm_request_attempts}")
        lines.append(f"- LLM retry count: {case_result.llm_retry_count}")
        lines.append(f"- LLM fallback count: {case_result.llm_fallback_count}")
        lines.append(f"- LLM error count: {case_result.llm_error_count}")
        if case_result.llm_error_categories:
            category_summary = ", ".join(
                f"{category}={count}" for category, count in sorted(case_result.llm_error_categories.items())
            )
            lines.append(f"- LLM error categories: {category_summary}")
    if case_result.llm_usage_observation_count > 0:
        lines.append(f"- LLM total tokens: {case_result.llm_total_tokens}")
    if case_result.resumed_from_checkpoint:
        lines.append("- Resumed from checkpoint: true")
        lines.append(
            f"- Checkpoint completed workers: {case_result.checkpoint_completed_worker_count}"
        )
        lines.append(f"- Skipped workers via resume: {case_result.skipped_worker_count}")
    if case_result.missing_issue_titles:
        lines.append(f"- Missing issue titles: {', '.join(case_result.missing_issue_titles)}")
    if case_result.unexpected_issue_titles:
        lines.append(f"- Unexpected issue titles: {', '.join(case_result.unexpected_issue_titles)}")
    lines.append("")
    return lines
