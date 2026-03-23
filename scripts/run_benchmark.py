from __future__ import annotations

import json
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for import_root in (PROJECT_ROOT, PROJECT_ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from papermentor_os.evals import (
    BenchmarkComparison,
    BenchmarkPricingConfig,
    ReviewBenchmark,
    BenchmarkSummary,
    BenchmarkThresholds,
    build_expectation_from_case,
    case_has_expectation_override,
    evaluate_benchmark_thresholds,
    load_benchmark_cases,
    render_benchmark_comparison_markdown,
    render_benchmark_markdown,
)
from papermentor_os.llm import LLMConfigurationError, ReviewBackend, ReviewLLMConfig
from papermentor_os.reviewer_factory import build_chief_reviewer
from tests.fixtures.sample_docx import build_docx_from_case
from tests.fixtures.review_cases import ReviewCaseSpec


def run_benchmark(
    *,
    tag: str = "evaluation_fixture",
    variants: list[str] | None = None,
    llm_config: ReviewLLMConfig | None = None,
    pricing_config: BenchmarkPricingConfig | None = None,
    resume_after_worker_id: str | None = None,
    reviewer_builder: Callable[[ReviewLLMConfig | None], ChiefReviewer] | None = None,
    case_loader: Callable[[str], tuple[ReviewCaseSpec, ...]] | None = None,
) -> dict[str, object]:
    benchmark = ReviewBenchmark()
    load_cases = case_loader or load_benchmark_cases
    build_reviewer = reviewer_builder or build_chief_reviewer
    evaluation_cases = load_cases(tag=tag)
    selected_variants = variants or ["rule"]
    variant_summaries: list[BenchmarkSummary] = []

    with tempfile.TemporaryDirectory(prefix="papermentor-benchmark-") as temp_dir:
        temp_root = Path(temp_dir)
        for variant_id in selected_variants:
            reviewer = build_reviewer(_resolve_variant_llm_config(variant_id, llm_config))
            case_results = []
            started_at = time.perf_counter()
            for case in evaluation_cases:
                file_path = temp_root / f"{variant_id}-{case.case_id}.docx"
                build_docx_from_case(file_path, case)
                case_started_at = time.perf_counter()
                report = _review_case(
                    reviewer,
                    file_path=file_path,
                    resume_after_worker_id=resume_after_worker_id,
                )
                case_results.append(
                    benchmark.evaluate_case(
                        report,
                        build_expectation_from_case(case, variant_id=variant_id),
                        debate_candidates=reviewer.last_debate_candidates,
                        worker_execution_traces=reviewer.last_worker_execution_traces,
                        orchestration_trace=reviewer.last_orchestration_trace,
                    )
                )
                _ = time.perf_counter() - case_started_at
            elapsed_seconds = time.perf_counter() - started_at
            average_case_duration_ms = (
                (elapsed_seconds / len(evaluation_cases)) * 1000.0 if evaluation_cases else 0.0
            )
            expectation_override_case_count = sum(
                1
                for case in evaluation_cases
                if case_has_expectation_override(case, variant_id=variant_id)
            )
            resolved_llm = _resolve_variant_llm_config(variant_id, llm_config)
            variant_summaries.append(
                benchmark.summarize_variant(
                    case_results,
                    variant_id=variant_id,
                    review_backend=(
                        resolved_llm.review_backend.value if resolved_llm is not None else ReviewBackend.RULE_ONLY.value
                    ),
                    expectation_override_case_count=expectation_override_case_count,
                    llm_provider_id=resolved_llm.provider_id if resolved_llm is not None else None,
                    llm_model_name=resolved_llm.model_name if resolved_llm is not None else None,
                    elapsed_seconds=elapsed_seconds,
                    average_case_duration_ms=average_case_duration_ms,
                    pricing_config=pricing_config,
                )
            )

    if len(variant_summaries) == 1:
        return variant_summaries[0].model_dump(mode="json")
    return BenchmarkComparison(
        variant_summaries=variant_summaries,
        gate_variant_id=variant_summaries[0].variant_id if variant_summaries else None,
    ).model_dump(mode="json")


def _resolve_variant_llm_config(
    variant_id: str,
    llm_config: ReviewLLMConfig | None,
) -> ReviewLLMConfig | None:
    if variant_id == "rule":
        return None
    if variant_id not in {ReviewBackend.MODEL_ONLY.value, ReviewBackend.MODEL_WITH_FALLBACK.value}:
        raise ValueError(
            "Unsupported benchmark variant. Use `rule`, `model_only`, or `model_with_fallback`."
        )
    if llm_config is None:
        raise ValueError("LLM benchmark variants require llm configuration.")
    return llm_config.model_copy(update={"review_backend": ReviewBackend(variant_id)})


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
    variants: list[str] = []
    llm_config: ReviewLLMConfig | None = None
    pricing_config: BenchmarkPricingConfig | None = None
    resume_after_worker_id: str | None = None
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
            if arg == "--variant" and index + 1 < len(args):
                variants.append(args[index + 1])
                index += 2
                continue
            if arg == "--llm-provider-id" and index + 1 < len(args):
                llm_config = _update_llm_config(llm_config, field_name="provider_id", raw_value=args[index + 1])
                index += 2
                continue
            if arg == "--llm-base-url" and index + 1 < len(args):
                llm_config = _update_llm_config(llm_config, field_name="base_url", raw_value=args[index + 1])
                index += 2
                continue
            if arg == "--llm-api-key" and index + 1 < len(args):
                llm_config = _update_llm_config(llm_config, field_name="api_key", raw_value=args[index + 1])
                index += 2
                continue
            if arg == "--llm-model-name" and index + 1 < len(args):
                llm_config = _update_llm_config(llm_config, field_name="model_name", raw_value=args[index + 1])
                index += 2
                continue
            if arg == "--llm-temperature" and index + 1 < len(args):
                llm_config = _update_llm_config(llm_config, field_name="temperature", raw_value=float(args[index + 1]))
                index += 2
                continue
            if arg == "--llm-max-tokens" and index + 1 < len(args):
                llm_config = _update_llm_config(llm_config, field_name="max_tokens", raw_value=int(args[index + 1]))
                index += 2
                continue
            if arg == "--llm-timeout" and index + 1 < len(args):
                llm_config = _update_llm_config(llm_config, field_name="timeout", raw_value=float(args[index + 1]))
                index += 2
                continue
            if arg == "--llm-max-retries" and index + 1 < len(args):
                llm_config = _update_llm_config(llm_config, field_name="max_retries", raw_value=int(args[index + 1]))
                index += 2
                continue
            if arg == "--llm-prompt-char-budget" and index + 1 < len(args):
                llm_config = _update_llm_config(
                    llm_config,
                    field_name="prompt_char_budget",
                    raw_value=int(args[index + 1]),
                )
                index += 2
                continue
            if arg == "--resume-after-worker-id" and index + 1 < len(args):
                resume_after_worker_id = args[index + 1]
                index += 2
                continue
            if arg == "--llm-input-price-per-1k-tokens" and index + 1 < len(args):
                pricing_config = _update_pricing_config(
                    pricing_config,
                    field_name="input_price_per_1k_tokens_usd",
                    raw_value=float(args[index + 1]),
                )
                index += 2
                continue
            if arg == "--llm-output-price-per-1k-tokens" and index + 1 < len(args):
                pricing_config = _update_pricing_config(
                    pricing_config,
                    field_name="output_price_per_1k_tokens_usd",
                    raw_value=float(args[index + 1]),
                )
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
                "[--variant rule|model_only|model_with_fallback] "
                "[--llm-provider-id openai_compatible] "
                "[--llm-base-url URL] "
                "[--llm-api-key KEY] "
                "[--llm-model-name NAME] "
                "[--resume-after-worker-id WORKER_ID] "
                "[--llm-input-price-per-1k-tokens USD] "
                "[--llm-output-price-per-1k-tokens USD] "
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

    run_kwargs: dict[str, object] = {"tag": tag}
    if variants:
        run_kwargs["variants"] = variants
    if llm_config is not None:
        run_kwargs["llm_config"] = llm_config
    if pricing_config is not None:
        if pricing_config.input_price_per_1k_tokens_usd < 0 or pricing_config.output_price_per_1k_tokens_usd < 0:
            print("LLM pricing values must be greater than or equal to zero.")
            return 1
        run_kwargs["pricing_config"] = pricing_config
    if resume_after_worker_id is not None:
        run_kwargs["resume_after_worker_id"] = resume_after_worker_id

    try:
        payload = run_benchmark(**run_kwargs)
    except (ValueError, LLMConfigurationError) as error:
        print(str(error))
        return 1

    if "variant_summaries" in payload:
        comparison = BenchmarkComparison.model_validate(payload)
        if not comparison.variant_summaries:
            print("Benchmark comparison did not contain any variant summaries.")
            return 1
        gate_summary = comparison.variant_summaries[0]
        gate_result = evaluate_benchmark_thresholds(gate_summary, thresholds)
    else:
        summary = BenchmarkSummary.model_validate(payload)
        gate_result = evaluate_benchmark_thresholds(summary, thresholds)

    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if gate_result.failed_checks:
            print(json.dumps({"failed_checks": gate_result.failed_checks}, ensure_ascii=False, indent=2))
        return 0 if gate_result.passed else 2
    if output_format == "markdown":
        if "variant_summaries" in payload:
            print(render_benchmark_comparison_markdown(BenchmarkComparison.model_validate(payload)))
        else:
            print(render_benchmark_markdown(BenchmarkSummary.model_validate(payload)))
        if gate_result.failed_checks:
            print("")
            print("## Threshold Failures")
            print("")
            for failed_check in gate_result.failed_checks:
                print(f"- {failed_check}")
        return 0 if gate_result.passed else 2

    print("Unsupported format. Use json or markdown.")
    return 1


def _update_llm_config(
    current: ReviewLLMConfig | None,
    *,
    field_name: str,
    raw_value: object,
) -> ReviewLLMConfig:
    payload = current.model_dump(mode="python") if current is not None else ReviewLLMConfig().model_dump(mode="python")
    payload[field_name] = raw_value
    return ReviewLLMConfig.model_validate(payload)


def _update_pricing_config(
    current: BenchmarkPricingConfig | None,
    *,
    field_name: str,
    raw_value: float,
) -> BenchmarkPricingConfig:
    payload = (
        current.model_dump(mode="python")
        if current is not None
        else {
            "input_price_per_1k_tokens_usd": 0.0,
            "output_price_per_1k_tokens_usd": 0.0,
        }
    )
    payload[field_name] = raw_value
    return BenchmarkPricingConfig.model_validate(payload)


def _review_case(
    reviewer: ChiefReviewer,
    *,
    file_path: Path,
    resume_after_worker_id: str | None,
):
    if resume_after_worker_id is None:
        return reviewer.review_docx(file_path)
    paper = reviewer.parser.parse_file(file_path)
    checkpoint = reviewer.run_review_until(
        paper,
        stop_after_worker_id=resume_after_worker_id,
    )
    return reviewer.review_paper(paper, checkpoint=checkpoint)


if __name__ == "__main__":
    raise SystemExit(main())
