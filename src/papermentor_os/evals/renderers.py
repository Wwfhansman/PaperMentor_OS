from __future__ import annotations

from papermentor_os.evals.models import BenchmarkCaseResult, BenchmarkSummary


def render_benchmark_markdown(summary: BenchmarkSummary) -> str:
    lines = [
        "# PaperMentor OS Benchmark",
        "",
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
    for case_result in summary.case_results:
        lines.extend(_render_case_result(case_result))
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
    if case_result.missing_issue_titles:
        lines.append(f"- Missing issue titles: {', '.join(case_result.missing_issue_titles)}")
    if case_result.unexpected_issue_titles:
        lines.append(f"- Unexpected issue titles: {', '.join(case_result.unexpected_issue_titles)}")
    lines.append("")
    return lines
