from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import tempfile
import time
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for import_root in (PROJECT_ROOT, PROJECT_ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from papermentor_os.llm import LLMConfigurationError, ReviewBackend, ReviewLLMConfig
from papermentor_os.reviewer_factory import build_chief_reviewer
from papermentor_os.schemas.trace import WorkerExecutionTrace
from tests.fixtures.review_cases import ReviewCaseSpec, TOPIC_PRECISION_CASE
from tests.fixtures.sample_docx import build_docx_from_case

ENV_PREFIX = "PAPERMENTOR_OS_SMOKE_"
SMOKE_CASES: dict[str, ReviewCaseSpec] = {
    TOPIC_PRECISION_CASE.case_id: TOPIC_PRECISION_CASE,
}
SUPPORTED_WORKER_IDS = (
    "TopicScopeAgent",
    "LogicChainAgent",
    "LiteratureSupportAgent",
    "NoveltyDepthAgent",
    "WritingFormatAgent",
)


class _SmokePhaseTimeoutError(RuntimeError):
    pass


def run_live_llm_smoke(
    *,
    llm_config: ReviewLLMConfig,
    case: ReviewCaseSpec = TOPIC_PRECISION_CASE,
    worker_id: str | None = None,
    resume_after_worker_id: str | None = None,
    phase_timeout_seconds: float | None = None,
    reviewer_builder: Callable[[ReviewLLMConfig | None], object] | None = None,
) -> dict[str, object]:
    if worker_id is not None and resume_after_worker_id is not None:
        raise LLMConfigurationError("Smoke run does not support combining --worker-id with --resume-after-worker-id.")

    build_reviewer = reviewer_builder or build_chief_reviewer
    reviewer = build_reviewer(llm_config)
    started_at = time.perf_counter()

    with tempfile.TemporaryDirectory(prefix="papermentor-live-smoke-") as temp_dir:
        file_path = Path(temp_dir) / f"{case.case_id}.docx"
        build_docx_from_case(file_path, case)
        with _phase_timeout(phase_timeout_seconds):
            if worker_id is None:
                report = _run_full_review_smoke(
                    reviewer,
                    file_path=file_path,
                    resume_after_worker_id=resume_after_worker_id,
                )
                worker_runs = list(getattr(reviewer, "last_worker_execution_traces", []))
            else:
                report, worker_runs = _run_single_worker_smoke(reviewer, file_path, worker_id)
        orchestration_trace = getattr(reviewer, "last_orchestration_trace", None)

    all_workers_parsed = all(_worker_run_parsed(worker_run) for worker_run in worker_runs)
    fallback_worker_ids = [
        worker_run.worker_id for worker_run in worker_runs if worker_run.fallback_used
    ]
    failed_workers = [
        {
            "worker_id": worker_run.worker_id,
            "dimension": worker_run.dimension.value,
            "structured_output_status": worker_run.structured_output_status,
            "fallback_used": worker_run.fallback_used,
            "llm_error_category": worker_run.llm_error_category,
        }
        for worker_run in worker_runs
        if not _worker_run_parsed(worker_run)
    ]

    return {
        "case_id": case.case_id,
        "review_backend": llm_config.review_backend.value,
        "provider_id": llm_config.provider_id,
        "model_name": llm_config.model_name,
        "selected_worker_id": worker_id,
        "resume_after_worker_id": resume_after_worker_id,
        "resumed_from_checkpoint": (
            getattr(orchestration_trace, "resumed_from_checkpoint", False) if orchestration_trace is not None else False
        ),
        "checkpoint_completed_worker_count": (
            getattr(orchestration_trace, "checkpoint_completed_worker_count", 0)
            if orchestration_trace is not None
            else 0
        ),
        "skipped_worker_count": (
            len(getattr(orchestration_trace, "skipped_worker_ids", []))
            if orchestration_trace is not None
            else 0
        ),
        "resume_start_worker_id": (
            getattr(orchestration_trace, "resume_start_worker_id", None)
            if orchestration_trace is not None
            else None
        ),
        "all_workers_parsed": all_workers_parsed,
        "worker_count": len(worker_runs),
        "parsed_worker_count": sum(1 for worker_run in worker_runs if _worker_run_parsed(worker_run)),
        "failed_workers": failed_workers,
        "fallback_worker_ids": fallback_worker_ids,
        "llm_request_attempts": sum(worker_run.llm_request_attempts for worker_run in worker_runs),
        "llm_retry_count": sum(worker_run.llm_retry_count for worker_run in worker_runs),
        "llm_total_tokens": sum((worker_run.llm_total_tokens or 0) for worker_run in worker_runs),
        "finding_count": sum(len(dimension_report.findings) for dimension_report in report.dimension_reports),
        "priority_action_count": len(report.priority_actions),
        "elapsed_seconds": time.perf_counter() - started_at,
    }


def run_live_llm_smoke_comparison(
    *,
    llm_config: ReviewLLMConfig,
    case: ReviewCaseSpec = TOPIC_PRECISION_CASE,
    compare_resume_after_worker_id: str,
    phase_timeout_seconds: float | None = None,
    reviewer_builder: Callable[[ReviewLLMConfig | None], object] | None = None,
) -> dict[str, object]:
    if reviewer_builder is None:
        baseline_payload = _run_smoke_phase(
            llm_config=llm_config,
            case=case,
            phase_timeout_seconds=phase_timeout_seconds,
        )
        resumed_payload = _run_smoke_phase(
            llm_config=llm_config,
            case=case,
            resume_after_worker_id=compare_resume_after_worker_id,
            phase_timeout_seconds=phase_timeout_seconds,
        )
    else:
        baseline_payload = _run_smoke_phase(
            llm_config=llm_config,
            case=case,
            phase_timeout_seconds=phase_timeout_seconds,
            reviewer_builder=reviewer_builder,
        )
        resumed_payload = _run_smoke_phase(
            llm_config=llm_config,
            case=case,
            resume_after_worker_id=compare_resume_after_worker_id,
            phase_timeout_seconds=phase_timeout_seconds,
            reviewer_builder=reviewer_builder,
        )

    return {
        "case_id": case.case_id,
        "review_backend": llm_config.review_backend.value,
        "provider_id": llm_config.provider_id,
        "model_name": llm_config.model_name,
        "compare_resume_after_worker_id": compare_resume_after_worker_id,
        "phase_timeout_seconds": phase_timeout_seconds,
        "baseline": baseline_payload,
        "resume": resumed_payload,
        "parsed_worker_count_delta": _metric_delta(
            baseline_payload,
            resumed_payload,
            key="parsed_worker_count",
        ),
        "fallback_worker_count_delta": _fallback_worker_count_delta(
            baseline_payload,
            resumed_payload,
        ),
    }


def _run_smoke_phase(
    *,
    llm_config: ReviewLLMConfig,
    case: ReviewCaseSpec,
    worker_id: str | None = None,
    resume_after_worker_id: str | None = None,
    phase_timeout_seconds: float | None = None,
    reviewer_builder: Callable[[ReviewLLMConfig | None], object] | None = None,
) -> dict[str, object]:
    try:
        return run_live_llm_smoke(
            llm_config=llm_config,
            case=case,
            worker_id=worker_id,
            resume_after_worker_id=resume_after_worker_id,
            phase_timeout_seconds=phase_timeout_seconds,
            reviewer_builder=reviewer_builder,
        )
    except Exception as error:
        return {
            "case_id": case.case_id,
            "review_backend": llm_config.review_backend.value,
            "provider_id": llm_config.provider_id,
            "model_name": llm_config.model_name,
            "selected_worker_id": worker_id,
            "resume_after_worker_id": resume_after_worker_id,
            "resumed_from_checkpoint": False,
            "checkpoint_completed_worker_count": 0,
            "skipped_worker_count": 0,
            "resume_start_worker_id": None,
            "all_workers_parsed": False,
            "worker_count": 0,
            "parsed_worker_count": 0,
            "failed_workers": [],
            "fallback_worker_ids": [],
            "llm_request_attempts": 0,
            "llm_retry_count": 0,
            "llm_total_tokens": 0,
            "finding_count": 0,
            "priority_action_count": 0,
            "elapsed_seconds": 0.0,
            "phase_error": str(error),
            "phase_timed_out": isinstance(error, _SmokePhaseTimeoutError),
        }


def _metric_delta(
    baseline_payload: dict[str, object],
    resumed_payload: dict[str, object],
    *,
    key: str,
) -> int:
    return int(resumed_payload.get(key, 0)) - int(baseline_payload.get(key, 0))


def _fallback_worker_count_delta(
    baseline_payload: dict[str, object],
    resumed_payload: dict[str, object],
) -> int:
    return len(resumed_payload.get("fallback_worker_ids", [])) - len(
        baseline_payload.get("fallback_worker_ids", [])
    )


@contextmanager
def _phase_timeout(timeout_seconds: float | None):
    if timeout_seconds is None:
        yield
        return
    if timeout_seconds <= 0:
        raise LLMConfigurationError("Smoke phase timeout must be greater than zero.")
    previous_handler = signal.getsignal(signal.SIGALRM)

    def _handle_timeout(signum, frame):  # pragma: no cover - signal callback
        raise _SmokePhaseTimeoutError(f"Smoke phase timed out after {timeout_seconds:.1f}s.")

    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.setitimer(signal.ITIMER_REAL, timeout_seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def _run_full_review_smoke(
    reviewer: object,
    *,
    file_path: Path,
    resume_after_worker_id: str | None,
):
    if resume_after_worker_id is None:
        return reviewer.review_docx(file_path)
    parser = getattr(reviewer, "parser", None)
    if parser is None or not hasattr(parser, "parse_file"):
        raise LLMConfigurationError("Resume smoke requires reviewer.parser.parse_file().")
    if not hasattr(reviewer, "run_review_until") or not hasattr(reviewer, "review_paper"):
        raise LLMConfigurationError("Resume smoke requires reviewer.run_review_until() and reviewer.review_paper().")
    paper = parser.parse_file(file_path)
    checkpoint = reviewer.run_review_until(
        paper,
        stop_after_worker_id=resume_after_worker_id,
    )
    return reviewer.review_paper(paper, checkpoint=checkpoint)


def _run_single_worker_smoke(
    reviewer: object,
    file_path: Path,
    worker_id: str,
) -> tuple[object, list[WorkerExecutionTrace]]:
    if hasattr(reviewer, "run_worker_smoke"):
        smoke_result = reviewer.run_worker_smoke(file_path, worker_id)
        if not isinstance(smoke_result, tuple) or len(smoke_result) != 2:
            raise LLMConfigurationError("reviewer.run_worker_smoke() must return a two-item tuple.")
        first_item, second_item = smoke_result
        if hasattr(first_item, "dimension_reports"):
            return first_item, list(second_item)
        worker_trace = second_item[0] if isinstance(second_item, list) else second_item
        return (
            SimpleNamespace(
                dimension_reports=[first_item],
                priority_actions=[],
            ),
            [worker_trace],
        )

    raise LLMConfigurationError(
        "Single-worker smoke requires reviewer.run_worker_smoke().",
    )


def _worker_run_parsed(worker_run: WorkerExecutionTrace) -> bool:
    return (
        worker_run.review_backend != ReviewBackend.RULE_ONLY.value
        and worker_run.structured_output_status == "parsed"
        and not worker_run.fallback_used
    )


def _resolve_llm_config_from_args(args: argparse.Namespace) -> ReviewLLMConfig:
    base_url = args.base_url or os.getenv(f"{ENV_PREFIX}BASE_URL")
    api_key = args.api_key or os.getenv(f"{ENV_PREFIX}API_KEY")
    model_name = args.model_name or os.getenv(f"{ENV_PREFIX}MODEL_NAME")
    provider_id = args.provider_id or os.getenv(f"{ENV_PREFIX}PROVIDER_ID", "openai_compatible")
    raw_backend = args.review_backend or os.getenv(
        f"{ENV_PREFIX}REVIEW_BACKEND",
        ReviewBackend.MODEL_ONLY.value,
    )

    if not base_url:
        raise LLMConfigurationError("Smoke run requires base_url via --base-url or env.")
    if not model_name:
        raise LLMConfigurationError("Smoke run requires model_name via --model-name or env.")
    if not api_key:
        raise LLMConfigurationError("Smoke run requires api_key via --api-key or env.")

    return ReviewLLMConfig(
        review_backend=ReviewBackend(raw_backend),
        provider_id=provider_id,
        base_url=base_url,
        api_key=api_key,
        model_name=model_name,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
        max_retries=args.max_retries,
        prompt_char_budget=args.prompt_char_budget,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run an opt-in live smoke check against an OpenAI-compatible LLM provider.",
    )
    parser.add_argument(
        "--case-id",
        default=TOPIC_PRECISION_CASE.case_id,
        choices=sorted(SMOKE_CASES.keys()),
        help="Built-in review case used for the smoke request.",
    )
    parser.add_argument(
        "--review-backend",
        choices=[ReviewBackend.MODEL_ONLY.value, ReviewBackend.MODEL_WITH_FALLBACK.value],
        default=None,
        help="Smoke backend mode. Defaults to model_only.",
    )
    parser.add_argument("--provider-id", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--prompt-char-budget", type=int, default=12000)
    parser.add_argument(
        "--phase-timeout-seconds",
        type=float,
        default=None,
        help="Hard timeout for a single smoke phase or compare branch. Useful for online provider stability checks.",
    )
    parser.add_argument(
        "--worker-id",
        choices=SUPPORTED_WORKER_IDS,
        default=None,
        help="Optionally run smoke against a single worker instead of the full five-worker chain.",
    )
    parser.add_argument(
        "--resume-after-worker-id",
        choices=SUPPORTED_WORKER_IDS,
        default=None,
        help="Optionally run a two-phase smoke: stop after a worker, then resume the full chain from checkpoint.",
    )
    parser.add_argument(
        "--compare-resume-after-worker-id",
        choices=SUPPORTED_WORKER_IDS,
        default=None,
        help="Run both the direct full-chain smoke and the checkpoint-resume path, then print a comparison payload.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        llm_config = _resolve_llm_config_from_args(args)
        if args.compare_resume_after_worker_id is not None:
            if args.worker_id is not None or args.resume_after_worker_id is not None:
                raise LLMConfigurationError(
                    "Smoke run does not support combining --compare-resume-after-worker-id with --worker-id or --resume-after-worker-id."
                )
            payload = run_live_llm_smoke_comparison(
                llm_config=llm_config,
                case=SMOKE_CASES[args.case_id],
                compare_resume_after_worker_id=args.compare_resume_after_worker_id,
                phase_timeout_seconds=args.phase_timeout_seconds,
            )
        else:
            payload = run_live_llm_smoke(
                llm_config=llm_config,
                case=SMOKE_CASES[args.case_id],
                worker_id=args.worker_id,
                resume_after_worker_id=args.resume_after_worker_id,
                phase_timeout_seconds=args.phase_timeout_seconds,
            )
    except (LLMConfigurationError, ValueError) as error:
        print(str(error))
        return 1
    except Exception as error:  # pragma: no cover - defensive smoke wrapper
        print(
            json.dumps(
                {
                    "review_backend": args.review_backend or ReviewBackend.MODEL_ONLY.value,
                    "error": str(error),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if "resume" in payload:
        return 0 if payload["resume"].get("all_workers_parsed") else 2
    return 0 if payload["all_workers_parsed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
