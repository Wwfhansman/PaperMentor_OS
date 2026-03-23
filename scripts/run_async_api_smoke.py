from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for import_root in (PROJECT_ROOT, PROJECT_ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from papermentor_os.api.app import create_app
from papermentor_os.api.run_registry import InMemoryReviewRunRegistry
from papermentor_os.llm import LLMConfigurationError, ReviewBackend, ReviewLLMConfig
from tests.fixtures.review_cases import ReviewCaseSpec, TOPIC_PRECISION_CASE
from tests.fixtures.sample_docx import build_docx_from_case

SMOKE_CASES: dict[str, ReviewCaseSpec] = {
    TOPIC_PRECISION_CASE.case_id: TOPIC_PRECISION_CASE,
}


class _AsyncApiSmokeTimeoutError(RuntimeError):
    def __init__(self, *, message: str, diagnostics: dict[str, object]) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics


def run_async_api_smoke(
    *,
    case: ReviewCaseSpec = TOPIC_PRECISION_CASE,
    llm_config: ReviewLLMConfig | None = None,
    poll_timeout_seconds: float = 20.0,
    poll_interval_seconds: float = 0.05,
    claim_stale_run: bool = False,
    claim_poll_timeout_seconds: float = 10.0,
    lease_seconds: float = 30.0,
    primary_instance_id: str = "async-api-smoke-primary",
    secondary_instance_id: str = "async-api-smoke-secondary",
    app_builder: Callable[..., object] | None = None,
) -> dict[str, object]:
    build_app = app_builder or create_app
    started_at = time.perf_counter()

    with tempfile.TemporaryDirectory(prefix="papermentor-async-api-smoke-") as temp_dir:
        file_path = Path(temp_dir) / f"{case.case_id}.docx"
        build_docx_from_case(file_path, case)
        snapshot_dir = Path(temp_dir) / "run-snapshots"
        primary_app = build_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id=primary_instance_id,
            run_lease_seconds=lease_seconds,
            server_llm_config=llm_config if claim_stale_run and llm_config is not None else None,
        )
        if not claim_stale_run:
            with TestClient(primary_app) as client:
                accepted = _submit_async_review(
                    client,
                    file_path=file_path,
                    llm_config=llm_config,
                )
                completed = _poll_run_completion(
                    client,
                    accepted["run_id"],
                    timeout_seconds=poll_timeout_seconds,
                    poll_interval_seconds=poll_interval_seconds,
                )
                events = client.get(f"/review/runs/{accepted['run_id']}/events").json()["events"]
                claim_result = None
        else:
            with _lease_renewal_disabled_for_instance(primary_instance_id):
                with TestClient(primary_app) as primary_client:
                    accepted = _submit_async_review(
                        primary_client,
                        file_path=file_path,
                        llm_config=llm_config,
                    )
                    secondary_app = build_app(
                        run_snapshot_dir=snapshot_dir,
                        run_instance_id=secondary_instance_id,
                        run_lease_seconds=lease_seconds,
                        server_llm_config=llm_config if llm_config is not None else None,
                    )
                    with TestClient(secondary_app) as secondary_client:
                        _poll_run_claimable(
                            secondary_client,
                            accepted["run_id"],
                            timeout_seconds=claim_poll_timeout_seconds,
                            poll_interval_seconds=poll_interval_seconds,
                        )
                        claim_result = _claim_run(secondary_client, accepted["run_id"])
                        try:
                            completed = _poll_run_completion(
                                secondary_client,
                                accepted["run_id"],
                                timeout_seconds=poll_timeout_seconds,
                                poll_interval_seconds=poll_interval_seconds,
                            )
                        except _AsyncApiSmokeTimeoutError as error:
                            error.diagnostics["claim_result"] = claim_result
                            raise
                        events = secondary_client.get(f"/review/runs/{accepted['run_id']}/events").json()["events"]

    trace = completed.get("trace") or {}
    worker_runs = trace.get("worker_runs") or []
    orchestration = trace.get("orchestration") or {}
    fallback_worker_ids = [
        worker_run["worker_id"]
        for worker_run in worker_runs
        if worker_run.get("fallback_used")
    ]
    parsed_worker_count = sum(1 for worker_run in worker_runs if _worker_run_parsed(worker_run))

    return {
        "case_id": case.case_id,
        "review_backend": (
            llm_config.review_backend.value if llm_config is not None else ReviewBackend.RULE_ONLY.value
        ),
        "provider_id": llm_config.provider_id if llm_config is not None else None,
        "model_name": llm_config.model_name if llm_config is not None else None,
        "run_id": accepted["run_id"],
        "final_state": completed["run"]["state"],
        "owned_by": (completed.get("ownership") or {}).get("owner_instance_id"),
        "lease_active": (completed.get("ownership") or {}).get("lease_active"),
        "claim_stale_run": claim_stale_run,
        "claim_result": claim_result,
        "event_count": len(events),
        "event_types": [event["event_type"] for event in events],
        "worker_count": len(worker_runs),
        "completed_worker_count": completed["run"]["completed_worker_count"],
        "parsed_worker_count": parsed_worker_count,
        "all_workers_parsed": parsed_worker_count == len(worker_runs) if worker_runs else False,
        "fallback_worker_ids": fallback_worker_ids,
        "llm_request_attempts": sum(worker_run.get("llm_request_attempts", 0) for worker_run in worker_runs),
        "llm_retry_count": sum(worker_run.get("llm_retry_count", 0) for worker_run in worker_runs),
        "llm_total_tokens": sum((worker_run.get("llm_total_tokens") or 0) for worker_run in worker_runs),
        "finding_count": sum(
            len(dimension_report.get("findings", []))
            for dimension_report in (completed.get("report") or {}).get("dimension_reports", [])
        ),
        "priority_action_count": len((completed.get("report") or {}).get("priority_actions", [])),
        "resumed_from_checkpoint": orchestration.get("resumed_from_checkpoint", False),
        "checkpoint_completed_worker_count": orchestration.get("checkpoint_completed_worker_count", 0),
        "skipped_worker_count": len(orchestration.get("skipped_worker_ids", [])),
        "resume_start_worker_id": orchestration.get("resume_start_worker_id"),
        "error": completed.get("error"),
        "elapsed_seconds": time.perf_counter() - started_at,
    }


def _submit_async_review(
    client: TestClient,
    *,
    file_path: Path,
    llm_config: ReviewLLMConfig | None,
) -> dict[str, object]:
    payload = {"file_path": str(file_path)}
    if llm_config is not None:
        payload["llm"] = llm_config.model_dump(mode="json")
    response = client.post("/review/docx/async", json=payload)
    response.raise_for_status()
    return response.json()


def _poll_run_completion(
    client: TestClient,
    run_id: str,
    *,
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> dict[str, object]:
    deadline = time.time() + timeout_seconds
    last_payload: dict[str, object] | None = None
    while time.time() < deadline:
        response = client.get(f"/review/runs/{run_id}")
        response.raise_for_status()
        payload = response.json()
        last_payload = payload
        if payload["run"]["state"] in {"completed", "failed"}:
            return payload
        time.sleep(poll_interval_seconds)
    events_response = client.get(f"/review/runs/{run_id}/events")
    events_response.raise_for_status()
    events = events_response.json()["events"]
    diagnostics = {
        "run_id": run_id,
        "timeout_seconds": timeout_seconds,
        "last_run_payload": last_payload,
        "event_count": len(events),
        "last_event_type": events[-1]["event_type"] if events else None,
        "last_event_sequence_id": events[-1]["sequence_id"] if events else None,
    }
    raise _AsyncApiSmokeTimeoutError(
        message=f"async api smoke timed out after {timeout_seconds:.1f}s.",
        diagnostics=diagnostics,
    )


def _poll_run_claimable(
    client: TestClient,
    run_id: str,
    *,
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> dict[str, object]:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = client.get(f"/review/runs/{run_id}")
        response.raise_for_status()
        payload = response.json()
        ownership = payload.get("ownership") or {}
        if ownership.get("claimable"):
            return payload
        if payload["run"]["state"] in {"completed", "failed"}:
            raise RuntimeError("async api smoke expected a stale-claim window, but the run reached terminal state first.")
        time.sleep(poll_interval_seconds)
    raise RuntimeError(f"async api smoke did not become claimable within {timeout_seconds:.1f}s.")


def _claim_run(client: TestClient, run_id: str) -> dict[str, object]:
    response = client.post(f"/review/runs/{run_id}/claim")
    payload = response.json()
    if response.status_code != 200:
        raise RuntimeError(
            f"async api smoke claim failed with status {response.status_code}: {json.dumps(payload, ensure_ascii=False)}"
        )
    return payload


@contextmanager
def _lease_renewal_disabled_for_instance(instance_id: str):
    original = InMemoryReviewRunRegistry._renew_run_lease_until_stopped

    def _no_lease_renewal(self, run_id, ownership_epoch, ownership_token, stop_event):
        if self.instance_id != instance_id:
            return original(self, run_id, ownership_epoch, ownership_token, stop_event)
        stop_event.wait(timeout=1.0)

    InMemoryReviewRunRegistry._renew_run_lease_until_stopped = _no_lease_renewal
    try:
        yield
    finally:
        InMemoryReviewRunRegistry._renew_run_lease_until_stopped = original


def _worker_run_parsed(worker_run: dict[str, object]) -> bool:
    return (
        worker_run.get("review_backend") != ReviewBackend.RULE_ONLY.value
        and worker_run.get("structured_output_status") == "parsed"
        and not worker_run.get("fallback_used")
    )


def _resolve_llm_config_from_args(args: argparse.Namespace) -> ReviewLLMConfig | None:
    if (
        args.review_backend == ReviewBackend.RULE_ONLY.value
        and args.base_url is None
        and args.api_key is None
        and args.model_name is None
        and args.provider_id == "openai_compatible"
    ):
        return None

    review_backend = ReviewBackend(args.review_backend)
    if review_backend == ReviewBackend.RULE_ONLY:
        return ReviewLLMConfig(review_backend=review_backend)
    if not args.base_url:
        raise LLMConfigurationError("Async API smoke requires --base-url when llm review is enabled.")
    if not args.api_key:
        raise LLMConfigurationError("Async API smoke requires --api-key when llm review is enabled.")
    if not args.model_name:
        raise LLMConfigurationError("Async API smoke requires --model-name when llm review is enabled.")

    return ReviewLLMConfig(
        review_backend=review_backend,
        provider_id=args.provider_id,
        base_url=args.base_url,
        api_key=args.api_key,
        model_name=args.model_name,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
        max_retries=args.max_retries,
        prompt_char_budget=args.prompt_char_budget,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a local async API smoke against /review/docx/async and summarize the final run payload.",
    )
    parser.add_argument(
        "--case-id",
        default=TOPIC_PRECISION_CASE.case_id,
        choices=sorted(SMOKE_CASES.keys()),
        help="Built-in review case used for the smoke request.",
    )
    parser.add_argument(
        "--review-backend",
        choices=[
            ReviewBackend.RULE_ONLY.value,
            ReviewBackend.MODEL_ONLY.value,
            ReviewBackend.MODEL_WITH_FALLBACK.value,
        ],
        default=ReviewBackend.RULE_ONLY.value,
    )
    parser.add_argument("--provider-id", default="openai_compatible")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--prompt-char-budget", type=int, default=12000)
    parser.add_argument("--poll-timeout-seconds", type=float, default=20.0)
    parser.add_argument("--poll-interval-seconds", type=float, default=0.05)
    parser.add_argument("--claim-stale-run", action="store_true")
    parser.add_argument("--claim-poll-timeout-seconds", type=float, default=10.0)
    parser.add_argument("--lease-seconds", type=float, default=30.0)
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        llm_config = _resolve_llm_config_from_args(args)
        payload = run_async_api_smoke(
            case=SMOKE_CASES[args.case_id],
            llm_config=llm_config,
            poll_timeout_seconds=args.poll_timeout_seconds,
            poll_interval_seconds=args.poll_interval_seconds,
            claim_stale_run=args.claim_stale_run,
            claim_poll_timeout_seconds=args.claim_poll_timeout_seconds,
            lease_seconds=args.lease_seconds,
        )
    except _AsyncApiSmokeTimeoutError as error:
        print(
            json.dumps(
                {
                    "error": str(error),
                    "diagnostics": error.diagnostics,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    except Exception as error:
        print(str(error))
        return 1

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["final_state"] != "completed":
        return 2
    if payload["review_backend"] != ReviewBackend.RULE_ONLY.value and not payload["all_workers_parsed"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
