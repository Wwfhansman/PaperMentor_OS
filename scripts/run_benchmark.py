from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for import_root in (PROJECT_ROOT, PROJECT_ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from papermentor_os.evals import (
    ReviewBenchmark,
    BenchmarkSummary,
    BenchmarkThresholds,
    build_expectation_from_case,
    evaluate_benchmark_thresholds,
    load_benchmark_cases,
    render_benchmark_markdown,
)
from papermentor_os.orchestrator.chief_reviewer import ChiefReviewer
from tests.fixtures.sample_docx import build_docx_from_case


def run_benchmark(*, tag: str = "evaluation_fixture") -> dict[str, object]:
    reviewer = ChiefReviewer()
    benchmark = ReviewBenchmark()
    evaluation_cases = load_benchmark_cases(tag=tag)
    case_results = []

    with tempfile.TemporaryDirectory(prefix="papermentor-benchmark-") as temp_dir:
        temp_root = Path(temp_dir)
        for case in evaluation_cases:
            file_path = temp_root / f"{case.case_id}.docx"
            build_docx_from_case(file_path, case)
            report = reviewer.review_docx(file_path)
            case_results.append(
                benchmark.evaluate_case(
                    report,
                    build_expectation_from_case(case),
                    debate_candidates=reviewer.last_debate_candidates,
                )
            )

    summary = benchmark.summarize(case_results)
    return summary.model_dump(mode="json")


def _update_thresholds(
    thresholds: BenchmarkThresholds,
    *,
    field_name: str,
    raw_value: str,
) -> BenchmarkThresholds:
    current_payload = thresholds.model_dump(mode="python")
    current_payload[field_name] = float(raw_value)
    return BenchmarkThresholds.model_validate(current_payload)


def main() -> int:
    output_format = "json"
    tag = "evaluation_fixture"
    thresholds = BenchmarkThresholds()
    args = sys.argv[1:]
    index = 0
    try:
        while index < len(args):
            arg = args[index]
            if arg == "--format" and index + 1 < len(args):
                output_format = args[index + 1]
                index += 2
                continue
            if arg == "--tag" and index + 1 < len(args):
                tag = args[index + 1]
                index += 2
                continue
            if arg == "--min-high-severity-recall" and index + 1 < len(args):
                thresholds = _update_thresholds(
                    thresholds,
                    field_name="min_high_severity_dimension_recall",
                    raw_value=args[index + 1],
                )
                index += 2
                continue
            if arg == "--min-priority-accuracy" and index + 1 < len(args):
                thresholds = _update_thresholds(
                    thresholds,
                    field_name="min_priority_first_dimension_accuracy",
                    raw_value=args[index + 1],
                )
                index += 2
                continue
            if arg == "--min-debate-recall" and index + 1 < len(args):
                thresholds = _update_thresholds(
                    thresholds,
                    field_name="min_debate_dimension_recall",
                    raw_value=args[index + 1],
                )
                index += 2
                continue
            if arg == "--min-issue-title-recall" and index + 1 < len(args):
                thresholds = _update_thresholds(
                    thresholds,
                    field_name="min_issue_title_recall",
                    raw_value=args[index + 1],
                )
                index += 2
                continue
            if arg == "--max-issue-title-fpr" and index + 1 < len(args):
                thresholds = _update_thresholds(
                    thresholds,
                    field_name="max_issue_title_false_positive_rate",
                    raw_value=args[index + 1],
                )
                index += 2
                continue
            print(
                "Usage: python scripts/run_benchmark.py "
                "[--format json|markdown] [--tag evaluation_fixture] "
                "[--min-high-severity-recall 0.0-1.0] "
                "[--min-priority-accuracy 0.0-1.0] "
                "[--min-debate-recall 0.0-1.0] "
                "[--min-issue-title-recall 0.0-1.0] "
                "[--max-issue-title-fpr 0.0-1.0]"
            )
            return 1
    except (ValueError, ValidationError):
        print("Invalid threshold value. All thresholds must be numbers in the range 0.0 to 1.0.")
        return 1

    payload = run_benchmark(tag=tag)
    summary = BenchmarkSummary.model_validate(payload)
    gate_result = evaluate_benchmark_thresholds(summary, thresholds)

    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if gate_result.failed_checks:
            print(json.dumps({"failed_checks": gate_result.failed_checks}, ensure_ascii=False, indent=2))
        return 0 if gate_result.passed else 2
    if output_format == "markdown":
        print(render_benchmark_markdown(summary))
        if gate_result.failed_checks:
            print("")
            print("## Threshold Failures")
            print("")
            for failed_check in gate_result.failed_checks:
                print(f"- {failed_check}")
        return 0 if gate_result.passed else 2

    print("Unsupported format. Use json or markdown.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
