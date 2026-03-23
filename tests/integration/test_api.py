import importlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
import time

from fastapi.testclient import TestClient

from papermentor_os.api.app import create_app
from papermentor_os.llm import LLMProviderError, ReviewBackend, ReviewLLMConfig
from papermentor_os.schemas.types import Dimension
from tests.fixtures.review_cases import (
    BOUNDARY_REVIEW_CASE,
    DEBATE_CANDIDATE_CASE,
    REVIEW_CASE_CATALOG,
    STRONG_REVIEW_CASE,
    WEAK_REVIEW_CASE,
    get_review_cases_by_tag,
)
from tests.fixtures.sample_docx import build_docx_from_case


def _poll_run_completion(client: TestClient, run_id: str, *, timeout_seconds: float = 4.0) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = client.get(f"/review/runs/{run_id}")
        assert response.status_code == 200
        payload = response.json()
        if payload["run"]["state"] in {"completed", "failed"}:
            return payload
        time.sleep(0.02)
    raise AssertionError(f"review run {run_id} did not finish within {timeout_seconds} seconds")


def test_debug_review_endpoint_returns_trace(tmp_path: Path) -> None:
    file_path = tmp_path / "debate_case.docx"
    build_docx_from_case(file_path, DEBATE_CANDIDATE_CASE)
    client = TestClient(create_app())

    response = client.post(
        "/review/docx/debug",
        json={"file_path": str(file_path)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "report" in payload
    assert "trace" in payload
    assert payload["trace"]["worker_skills"]
    assert payload["trace"]["worker_runs"]
    assert payload["trace"]["orchestration"]["worker_sequence"] == [
        "TopicScopeAgent",
        "LogicChainAgent",
        "LiteratureSupportAgent",
        "NoveltyDepthAgent",
        "WritingFormatAgent",
    ]
    assert payload["trace"]["debate_candidates"]
    assert payload["trace"]["debate_resolutions"]
    assert payload["trace"]["debate_resolution_traces"]
    assert payload["trace"]["worker_skills"][0]["rubric_skills"]
    assert payload["trace"]["worker_skills"][0]["policy_skills"]
    assert payload["trace"]["worker_runs"][0]["finding_count"] >= 0
    assert payload["trace"]["worker_runs"][0]["review_backend"] == "rule_only"
    assert payload["trace"]["worker_runs"][0]["structured_output_status"] == "not_requested"
    assert payload["trace"]["worker_runs"][0]["fallback_used"] is False
    assert payload["trace"]["worker_runs"][0]["llm_request_attempts"] == 0
    assert payload["trace"]["worker_runs"][0]["llm_retry_count"] == 0
    assert payload["trace"]["debate_resolution_traces"][0]["worker_review_backend"] == "rule_only"
    assert payload["trace"]["orchestration"]["resumed_from_checkpoint"] is False
    assert payload["trace"]["orchestration"]["checkpoint_completed_worker_count"] == 0
    assert payload["trace"]["orchestration"]["resumed_worker_ids"] == []
    assert payload["trace"]["orchestration"]["skipped_worker_ids"] == []
    assert payload["trace"]["orchestration"]["resume_start_worker_id"] is None
    assert payload["trace"]["debate_resolution_traces"][0]["confidence_floor"] >= 0.0
    assert payload["trace"]["debate_resolution_traces"][0]["pre_debate_score"] >= 0.0
    assert payload["trace"]["debate_resolution_traces"][0]["decision_policy_summary"]
    assert payload["trace"]["debate_resolution_traces"][0]["recommended_action"]
    dimensions = {item["dimension"] for item in payload["report"]["dimension_reports"]}
    assert Dimension.NOVELTY_DEPTH.value in dimensions


def test_pdf_review_endpoint_returns_pdf_file(tmp_path: Path) -> None:
    file_path = tmp_path / "strong_case.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    client = TestClient(create_app())

    response = client.post(
        "/review/docx/pdf",
        json={"file_path": str(file_path)},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "strong_case-review.pdf" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-1.4")


def test_pdf_review_endpoint_cleans_up_temporary_pdf(tmp_path: Path, monkeypatch) -> None:
    file_path = tmp_path / "strong_case.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    captured_pdf_path = tmp_path / "exported-review.pdf"
    app_module = importlib.import_module("papermentor_os.api.app")

    class _NamedTempHandle:
        def __init__(self, path: Path) -> None:
            self.name = str(path)

        def __enter__(self) -> "_NamedTempHandle":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    def _fake_named_temporary_file(*args, **kwargs) -> _NamedTempHandle:
        return _NamedTempHandle(captured_pdf_path)

    monkeypatch.setattr(app_module.tempfile, "NamedTemporaryFile", _fake_named_temporary_file)

    client = TestClient(create_app())
    response = client.post(
        "/review/docx/pdf",
        json={"file_path": str(file_path)},
    )

    assert response.status_code == 200
    assert not captured_pdf_path.exists()


def test_async_review_endpoint_returns_queryable_run_and_final_report(tmp_path: Path) -> None:
    file_path = tmp_path / "async-strong.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    client = TestClient(create_app(run_instance_id="primary-instance"))

    response = client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    )

    assert response.status_code == 202
    accepted = response.json()
    assert accepted["run"]["state"] == "pending"
    assert accepted["run"]["worker_sequence"] == [
        "TopicScopeAgent",
        "LogicChainAgent",
        "LiteratureSupportAgent",
        "NoveltyDepthAgent",
        "WritingFormatAgent",
    ]
    assert accepted["status_url"] == f"/review/runs/{accepted['run_id']}"
    assert accepted["events_url"] == f"/review/runs/{accepted['run_id']}/events"
    assert accepted["ownership"]["owner_instance_id"] == "primary-instance"
    assert accepted["ownership"]["lease_active"] is True
    assert accepted["ownership"]["owned_by_current_instance"] is True

    completed = _poll_run_completion(client, accepted["run_id"])
    assert completed["run"]["state"] == "completed"
    assert completed["report"] is not None
    assert completed["trace"] is not None
    assert completed["error"] is None
    assert completed["ownership"]["owner_instance_id"] == "primary-instance"
    assert completed["ownership"]["lease_active"] is False
    assert completed["ownership"]["owned_by_current_instance"] is True
    assert len(completed["report"]["dimension_reports"]) == 5
    assert completed["run"]["completed_worker_count"] == 5
    assert completed["run"]["failed_worker_count"] == 0


def test_async_review_run_events_endpoint_returns_event_log(tmp_path: Path) -> None:
    file_path = tmp_path / "async-boundary.docx"
    build_docx_from_case(file_path, BOUNDARY_REVIEW_CASE)
    client = TestClient(create_app())

    accepted = client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    ).json()
    _poll_run_completion(client, accepted["run_id"], timeout_seconds=8.0)

    response = client.get(f"/review/runs/{accepted['run_id']}/events")

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == accepted["run_id"]
    assert payload["events"]
    assert payload["events"][0]["event_type"] == "created"
    assert payload["events"][-1]["event_type"] == "completed"
    assert any(event["event_type"] == "updated" for event in payload["events"])

    last_sequence_id = payload["events"][-1]["sequence_id"]
    filtered_response = client.get(
        f"/review/runs/{accepted['run_id']}/events",
        params={"after_sequence_id": last_sequence_id - 1},
    )
    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()
    assert len(filtered_payload["events"]) == 1
    assert filtered_payload["events"][0]["sequence_id"] == last_sequence_id


def test_async_review_run_persists_across_app_recreation(tmp_path: Path) -> None:
    file_path = tmp_path / "async-persist.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    snapshot_dir = tmp_path / "run-snapshots"

    client = TestClient(create_app(run_snapshot_dir=snapshot_dir))
    accepted = client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    ).json()
    completed = _poll_run_completion(client, accepted["run_id"])

    recreated_client = TestClient(create_app(run_snapshot_dir=snapshot_dir))
    recreated_response = recreated_client.get(f"/review/runs/{accepted['run_id']}")

    assert recreated_response.status_code == 200
    recreated_payload = recreated_response.json()
    assert recreated_payload["run"]["state"] == "completed"
    assert recreated_payload["run"]["run_id"] == accepted["run_id"]
    assert recreated_payload["report"] == completed["report"]
    assert recreated_payload["trace"] == completed["trace"]
    assert (snapshot_dir / f"{accepted['run_id']}.json").exists()


def test_async_review_run_is_queryable_from_parallel_app_instance(tmp_path: Path) -> None:
    file_path = tmp_path / "async-cross-app.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    snapshot_dir = tmp_path / "run-snapshots"

    primary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="primary-instance",
        )
    )
    secondary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="secondary-instance",
        )
    )

    accepted = primary_client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    ).json()
    _poll_run_completion(primary_client, accepted["run_id"])

    mirrored_response = secondary_client.get(f"/review/runs/{accepted['run_id']}")
    assert mirrored_response.status_code == 200
    mirrored_payload = mirrored_response.json()
    assert mirrored_payload["run"]["run_id"] == accepted["run_id"]
    assert mirrored_payload["run"]["state"] == "completed"
    assert mirrored_payload["report"] is not None
    assert mirrored_payload["trace"] is not None
    assert mirrored_payload["ownership"]["owner_instance_id"] == "primary-instance"
    assert mirrored_payload["ownership"]["owned_by_current_instance"] is False
    assert mirrored_payload["ownership"]["lease_active"] is False

    mirrored_events_response = secondary_client.get(f"/review/runs/{accepted['run_id']}/events")
    assert mirrored_events_response.status_code == 200
    mirrored_events = mirrored_events_response.json()["events"]
    assert mirrored_events
    assert mirrored_events[-1]["event_type"] == "completed"


def test_async_review_run_claim_endpoint_rejects_active_foreign_lease(
    tmp_path: Path,
    monkeypatch,
) -> None:
    file_path = tmp_path / "async-claim-active.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    snapshot_dir = tmp_path / "run-snapshots"
    chief_module = importlib.import_module("papermentor_os.orchestrator.chief_reviewer")
    original_review_paper = chief_module.ChiefReviewer.review_paper

    def _slow_review_paper(self, *args, **kwargs):
        time.sleep(0.35)
        return original_review_paper(self, *args, **kwargs)

    monkeypatch.setattr(chief_module.ChiefReviewer, "review_paper", _slow_review_paper)

    primary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="primary-instance",
            run_lease_seconds=1.0,
        )
    )
    secondary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="secondary-instance",
            run_lease_seconds=1.0,
        )
    )

    accepted = primary_client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    ).json()
    time.sleep(0.1)

    mirrored_payload = secondary_client.get(f"/review/runs/{accepted['run_id']}").json()
    assert mirrored_payload["ownership"]["lease_active"] is True
    assert mirrored_payload["ownership"]["stale_lease"] is False
    assert mirrored_payload["ownership"]["claimable"] is False
    assert mirrored_payload["ownership"]["owned_by_current_instance"] is False

    response = secondary_client.post(f"/review/runs/{accepted['run_id']}/claim")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "active_foreign_lease"

    _poll_run_completion(primary_client, accepted["run_id"], timeout_seconds=3.0)


def test_async_review_run_claim_endpoint_claims_stale_foreign_lease(
    tmp_path: Path,
    monkeypatch,
) -> None:
    file_path = tmp_path / "async-claim-stale.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    snapshot_dir = tmp_path / "run-snapshots"
    chief_module = importlib.import_module("papermentor_os.orchestrator.chief_reviewer")
    registry_module = importlib.import_module("papermentor_os.api.run_registry")
    original_review_paper = chief_module.ChiefReviewer.review_paper

    def _slow_review_paper(self, *args, **kwargs):
        time.sleep(0.35)
        return original_review_paper(self, *args, **kwargs)

    def _no_lease_renewal(self, run_id, ownership_epoch, ownership_token, stop_event):
        stop_event.wait(timeout=1.0)

    monkeypatch.setattr(chief_module.ChiefReviewer, "review_paper", _slow_review_paper)
    monkeypatch.setattr(
        registry_module.InMemoryReviewRunRegistry,
        "_renew_run_lease_until_stopped",
        _no_lease_renewal,
    )

    primary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="primary-instance",
            run_lease_seconds=0.15,
        )
    )
    secondary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="secondary-instance",
            run_lease_seconds=0.3,
        )
    )

    accepted = primary_client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    ).json()
    time.sleep(0.22)

    stale_payload = secondary_client.get(f"/review/runs/{accepted['run_id']}").json()
    assert stale_payload["ownership"]["owner_instance_id"] == "primary-instance"
    assert stale_payload["ownership"]["lease_active"] is False
    assert stale_payload["ownership"]["stale_lease"] is True
    assert stale_payload["ownership"]["claimable"] is True
    assert stale_payload["ownership"]["owned_by_current_instance"] is False

    claim_response = secondary_client.post(f"/review/runs/{accepted['run_id']}/claim")
    assert claim_response.status_code == 200
    claim_payload = claim_response.json()
    assert claim_payload["claimed"] is True
    assert claim_payload["previous_owner_instance_id"] == "primary-instance"
    assert claim_payload["resume_started"] is True
    assert claim_payload["resume_reason"] == "resumed_from_source_with_checkpoint"
    assert claim_payload["ownership"]["owner_instance_id"] == "secondary-instance"
    assert claim_payload["ownership"]["lease_active"] is True
    assert claim_payload["ownership"]["owned_by_current_instance"] is True

    claimed_run_payload = _poll_run_completion(
        secondary_client,
        accepted["run_id"],
        timeout_seconds=3.0,
    )
    assert claimed_run_payload["ownership"]["owner_instance_id"] == "secondary-instance"
    assert claimed_run_payload["ownership"]["owned_by_current_instance"] is True
    assert claimed_run_payload["ownership"]["lease_active"] is False
    assert claimed_run_payload["report"] is not None

    claimed_events = secondary_client.get(f"/review/runs/{accepted['run_id']}/events").json()["events"]
    assert any(event["event_type"] == "ownership_claimed" for event in claimed_events)
    assert any(event["event_type"] == "resumed_completed" for event in claimed_events)


def test_async_review_run_claim_cancels_previous_owner_locally(
    tmp_path: Path,
    monkeypatch,
) -> None:
    file_path = tmp_path / "async-claim-cancel-old-owner.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    snapshot_dir = tmp_path / "run-snapshots"
    chief_module = importlib.import_module("papermentor_os.orchestrator.chief_reviewer")
    registry_module = importlib.import_module("papermentor_os.api.run_registry")
    original_execute_worker_review = chief_module.ChiefReviewer._execute_worker_review
    previous_owner_cancelled = Event()

    def _cooperative_slow_execute_worker_review(self, worker_agent, paper, *, skill_context):
        deadline = time.time() + 0.6
        while time.time() < deadline:
            try:
                self._raise_if_cancelled()
            except chief_module.ReviewRunCancelledError:
                previous_owner_cancelled.set()
                raise
            time.sleep(0.02)
        return original_execute_worker_review(self, worker_agent, paper, skill_context=skill_context)

    def _observe_claim_then_stop(self, run_id, ownership_epoch, ownership_token, stop_event):
        if stop_event.wait(timeout=0.35):
            return
        self._heartbeat_run_lease(
            run_id,
            ownership_epoch=ownership_epoch,
            ownership_token=ownership_token,
        )
        stop_event.wait(timeout=1.0)

    monkeypatch.setattr(
        chief_module.ChiefReviewer,
        "_execute_worker_review",
        _cooperative_slow_execute_worker_review,
    )
    monkeypatch.setattr(
        registry_module.InMemoryReviewRunRegistry,
        "_renew_run_lease_until_stopped",
        _observe_claim_then_stop,
    )

    primary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="primary-instance",
            run_lease_seconds=0.15,
        )
    )
    secondary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="secondary-instance",
            run_lease_seconds=0.3,
        )
    )

    accepted = primary_client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    ).json()
    time.sleep(0.22)

    claim_response = secondary_client.post(f"/review/runs/{accepted['run_id']}/claim")
    assert claim_response.status_code == 200
    assert claim_response.json()["resume_started"] is True
    assert previous_owner_cancelled.wait(timeout=1.0) is True

    completed = _poll_run_completion(secondary_client, accepted["run_id"], timeout_seconds=4.0)
    assert completed["run"]["state"] == "completed"
    assert completed["ownership"]["owner_instance_id"] == "secondary-instance"


def test_async_review_run_claim_endpoint_rejects_terminal_run(tmp_path: Path) -> None:
    file_path = tmp_path / "async-claim-terminal.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    client = TestClient(create_app(run_instance_id="primary-instance"))

    accepted = client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    ).json()
    _poll_run_completion(client, accepted["run_id"], timeout_seconds=8.0)

    response = client.post(f"/review/runs/{accepted['run_id']}/claim")
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "terminal_run"


def test_async_review_run_claim_endpoint_can_skip_auto_resume_for_request_scoped_key(
    tmp_path: Path,
    monkeypatch,
) -> None:
    for env_name in (
        "PAPERMENTOR_OS_SERVER_LLM_PROVIDER_ID",
        "PAPERMENTOR_OS_SERVER_LLM_BASE_URL",
        "PAPERMENTOR_OS_SERVER_LLM_API_KEY",
        "PAPERMENTOR_OS_SERVER_LLM_MODEL_NAME",
        "PAPERMENTOR_OS_SERVER_LLM_REVIEW_BACKEND",
    ):
        monkeypatch.delenv(env_name, raising=False)

    file_path = tmp_path / "async-claim-no-auto-resume.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    snapshot_dir = tmp_path / "run-snapshots"
    chief_module = importlib.import_module("papermentor_os.orchestrator.chief_reviewer")
    registry_module = importlib.import_module("papermentor_os.api.run_registry")
    original_review_paper = chief_module.ChiefReviewer.review_paper

    def _slow_review_paper(self, *args, **kwargs):
        time.sleep(0.35)
        return original_review_paper(self, *args, **kwargs)

    def _no_lease_renewal(self, run_id, ownership_epoch, ownership_token, stop_event):
        stop_event.wait(timeout=1.0)

    monkeypatch.setattr(chief_module.ChiefReviewer, "review_paper", _slow_review_paper)
    monkeypatch.setattr(
        registry_module.InMemoryReviewRunRegistry,
        "_renew_run_lease_until_stopped",
        _no_lease_renewal,
    )

    primary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="primary-instance",
            run_lease_seconds=0.15,
        )
    )
    secondary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="secondary-instance",
            run_lease_seconds=0.3,
        )
    )

    accepted = primary_client.post(
        "/review/docx/async",
        json={
            "file_path": str(file_path),
            "llm": ReviewLLMConfig(
                review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
                base_url="https://example.com/v1",
                api_key="sk-test",
                model_name="test-model",
            ).model_dump(mode="json"),
        },
    ).json()
    time.sleep(0.22)

    claim_response = secondary_client.post(f"/review/runs/{accepted['run_id']}/claim")
    assert claim_response.status_code == 200
    claim_payload = claim_response.json()
    assert claim_payload["claimed"] is True
    assert claim_payload["resume_started"] is False
    assert claim_payload["resume_reason"] == "request_scoped_api_key_not_persisted"


def test_async_review_run_claim_endpoint_can_auto_resume_request_scoped_key_with_server_llm_config(
    tmp_path: Path,
    monkeypatch,
) -> None:
    file_path = tmp_path / "async-claim-server-resume.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    snapshot_dir = tmp_path / "run-snapshots"
    chief_module = importlib.import_module("papermentor_os.orchestrator.chief_reviewer")
    registry_module = importlib.import_module("papermentor_os.api.run_registry")
    app_module = importlib.import_module("papermentor_os.api.app")
    original_review_paper = chief_module.ChiefReviewer.review_paper
    original_build_chief_reviewer = app_module.build_chief_reviewer

    def _slow_review_paper(self, *args, **kwargs):
        time.sleep(0.35)
        return original_review_paper(self, *args, **kwargs)

    def _no_lease_renewal(self, run_id, ownership_epoch, ownership_token, stop_event):
        stop_event.wait(timeout=1.0)

    def _rule_only_builder(llm_config=None, **kwargs):
        return original_build_chief_reviewer(
            ReviewLLMConfig(review_backend=ReviewBackend.RULE_ONLY),
            **kwargs,
        )

    monkeypatch.setattr(chief_module.ChiefReviewer, "review_paper", _slow_review_paper)
    monkeypatch.setattr(
        registry_module.InMemoryReviewRunRegistry,
        "_renew_run_lease_until_stopped",
        _no_lease_renewal,
    )
    monkeypatch.setattr(app_module, "build_chief_reviewer", _rule_only_builder)

    server_llm_config = ReviewLLMConfig(
        review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
        base_url="https://server.example.com/v1",
        api_key="sk-server",
        model_name="server-model",
    )

    primary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="primary-instance",
            run_lease_seconds=0.15,
            server_llm_config=server_llm_config,
        )
    )
    secondary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="secondary-instance",
            run_lease_seconds=0.3,
            server_llm_config=server_llm_config,
        )
    )

    accepted = primary_client.post(
        "/review/docx/async",
        json={
            "file_path": str(file_path),
            "llm": ReviewLLMConfig(
                review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
                base_url="https://request.example.com/v1",
                api_key="sk-request",
                model_name="request-model",
            ).model_dump(mode="json"),
        },
    ).json()
    time.sleep(0.22)

    claim_response = secondary_client.post(f"/review/runs/{accepted['run_id']}/claim")
    assert claim_response.status_code == 200
    claim_payload = claim_response.json()
    assert claim_payload["claimed"] is True
    assert claim_payload["resume_started"] is True
    assert claim_payload["resume_reason"] == "resumed_from_source_with_checkpoint"
    assert claim_payload["ownership"]["owner_instance_id"] == "secondary-instance"

    completed = _poll_run_completion(secondary_client, accepted["run_id"], timeout_seconds=4.0)
    assert completed["run"]["state"] == "completed"
    assert completed["ownership"]["owner_instance_id"] == "secondary-instance"
    assert completed["ownership"]["lease_active"] is False

    events = secondary_client.get(f"/review/runs/{accepted['run_id']}/events").json()["events"]
    assert any(event["event_type"] == "ownership_claimed" for event in events)
    assert any(event["event_type"] == "resumed_completed" for event in events)


def test_async_review_run_claim_endpoint_allows_only_one_concurrent_winner(
    tmp_path: Path,
    monkeypatch,
) -> None:
    file_path = tmp_path / "async-claim-concurrent.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    snapshot_dir = tmp_path / "run-snapshots"
    chief_module = importlib.import_module("papermentor_os.orchestrator.chief_reviewer")
    registry_module = importlib.import_module("papermentor_os.api.run_registry")
    original_review_paper = chief_module.ChiefReviewer.review_paper

    def _slow_review_paper(self, *args, **kwargs):
        time.sleep(0.35)
        return original_review_paper(self, *args, **kwargs)

    def _no_lease_renewal(self, run_id, ownership_epoch, ownership_token, stop_event):
        stop_event.wait(timeout=1.0)

    monkeypatch.setattr(chief_module.ChiefReviewer, "review_paper", _slow_review_paper)
    monkeypatch.setattr(
        registry_module.InMemoryReviewRunRegistry,
        "_renew_run_lease_until_stopped",
        _no_lease_renewal,
    )

    primary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="primary-instance",
            run_lease_seconds=0.15,
        )
    )
    secondary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="secondary-instance",
            run_lease_seconds=0.3,
        )
    )
    tertiary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="tertiary-instance",
            run_lease_seconds=0.3,
        )
    )

    accepted = primary_client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    ).json()
    time.sleep(0.22)

    def _claim(client: TestClient):
        return client.post(f"/review/runs/{accepted['run_id']}/claim")

    with ThreadPoolExecutor(max_workers=2) as executor:
        secondary_future = executor.submit(_claim, secondary_client)
        tertiary_future = executor.submit(_claim, tertiary_client)
        responses = [secondary_future.result(timeout=2.0), tertiary_future.result(timeout=2.0)]

    status_codes = sorted(response.status_code for response in responses)
    assert status_codes == [200, 409]

    winning_response = next(response for response in responses if response.status_code == 200)
    winning_payload = winning_response.json()
    assert winning_payload["claimed"] is True
    assert winning_payload["resume_started"] is True
    assert winning_payload["ownership"]["owner_instance_id"] in {"secondary-instance", "tertiary-instance"}

    losing_response = next(response for response in responses if response.status_code == 409)
    assert losing_response.json()["detail"]["code"] == "active_foreign_lease"

    winning_client = (
        secondary_client
        if winning_payload["ownership"]["owner_instance_id"] == "secondary-instance"
        else tertiary_client
    )
    completed = _poll_run_completion(winning_client, accepted["run_id"], timeout_seconds=4.0)
    assert completed["run"]["state"] == "completed"


def test_async_review_run_claim_auto_resume_builder_failure_marks_run_failed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    file_path = tmp_path / "async-claim-builder-failure.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    snapshot_dir = tmp_path / "run-snapshots"
    chief_module = importlib.import_module("papermentor_os.orchestrator.chief_reviewer")
    registry_module = importlib.import_module("papermentor_os.api.run_registry")
    app_module = importlib.import_module("papermentor_os.api.app")
    original_review_paper = chief_module.ChiefReviewer.review_paper

    def _slow_review_paper(self, *args, **kwargs):
        time.sleep(0.35)
        return original_review_paper(self, *args, **kwargs)

    def _no_lease_renewal(self, run_id, ownership_epoch, ownership_token, stop_event):
        stop_event.wait(timeout=1.0)

    monkeypatch.setattr(chief_module.ChiefReviewer, "review_paper", _slow_review_paper)
    monkeypatch.setattr(
        registry_module.InMemoryReviewRunRegistry,
        "_renew_run_lease_until_stopped",
        _no_lease_renewal,
    )

    primary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="primary-instance",
            run_lease_seconds=0.15,
        )
    )

    accepted = primary_client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    ).json()
    time.sleep(0.22)

    monkeypatch.setattr(
        app_module,
        "build_chief_reviewer",
        lambda llm_config=None, **kwargs: (_ for _ in ()).throw(RuntimeError("resume builder failed")),
    )

    secondary_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_instance_id="secondary-instance",
            run_lease_seconds=0.3,
        )
    )

    claim_response = secondary_client.post(f"/review/runs/{accepted['run_id']}/claim")
    assert claim_response.status_code == 200
    claim_payload = claim_response.json()
    assert claim_payload["claimed"] is True
    assert claim_payload["resume_started"] is True

    failed = _poll_run_completion(secondary_client, accepted["run_id"], timeout_seconds=4.0)
    assert failed["run"]["state"] == "failed"
    assert failed["ownership"]["owner_instance_id"] == "secondary-instance"
    assert failed["ownership"]["lease_active"] is False
    assert failed["error"] == {
        "code": "internal_server_error",
        "message": "review run failed unexpectedly.",
        "retryable": False,
    }

    events = secondary_client.get(f"/review/runs/{accepted['run_id']}/events").json()["events"]
    assert any(event["event_type"] == "ownership_claimed" for event in events)
    assert any(event["event_type"] == "resumed_failed" for event in events)


def test_async_review_run_ttl_prunes_completed_snapshot(tmp_path: Path) -> None:
    file_path = tmp_path / "async-expire.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    snapshot_dir = tmp_path / "run-snapshots"

    client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_retention_seconds=0.05,
        )
    )
    accepted = client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    ).json()
    _poll_run_completion(client, accepted["run_id"])

    snapshot_path = snapshot_dir / f"{accepted['run_id']}.json"
    assert snapshot_path.exists()

    time.sleep(0.08)

    expired_response = client.get(f"/review/runs/{accepted['run_id']}")
    assert expired_response.status_code == 404
    assert not snapshot_path.exists()

    recreated_client = TestClient(
        create_app(
            run_snapshot_dir=snapshot_dir,
            run_retention_seconds=0.05,
        )
    )
    recreated_response = recreated_client.get(f"/review/runs/{accepted['run_id']}")
    assert recreated_response.status_code == 404


def test_async_review_run_sse_endpoint_streams_events(tmp_path: Path) -> None:
    file_path = tmp_path / "async-sse.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    client = TestClient(create_app())

    accepted = client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    ).json()
    _poll_run_completion(client, accepted["run_id"])

    with client.stream("GET", f"/review/runs/{accepted['run_id']}/events/stream") as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "id: 1" in body
    assert "retry: 200" in body
    assert "event: review_run_event" in body
    assert '"event_type":"created"' in body
    assert '"event_type":"completed"' in body
    assert "event: review_run_completed" in body
    assert '"final_state":"completed"' in body


def test_async_review_run_sse_endpoint_supports_last_event_id_resume(tmp_path: Path) -> None:
    file_path = tmp_path / "async-sse-resume.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    client = TestClient(create_app())

    accepted = client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    ).json()
    _poll_run_completion(client, accepted["run_id"])
    events_payload = client.get(f"/review/runs/{accepted['run_id']}/events").json()
    first_sequence_id = events_payload["events"][0]["sequence_id"]

    with client.stream(
        "GET",
        f"/review/runs/{accepted['run_id']}/events/stream",
        headers={"Last-Event-ID": str(first_sequence_id)},
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert '"event_type":"created"' not in body
    assert '"event_type":"updated"' in body
    assert '"event_type":"completed"' in body
    assert "event: review_run_completed" in body


def test_async_review_run_sse_endpoint_emits_heartbeat_for_running_run(
    tmp_path: Path,
    monkeypatch,
) -> None:
    file_path = tmp_path / "async-sse-heartbeat.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    registry_module = importlib.import_module("papermentor_os.api.run_registry")
    original_execute_run = registry_module.InMemoryReviewRunRegistry._execute_run

    def _slow_execute_run(self, run_id, ownership_epoch, ownership_token, reviewer, paper):
        time.sleep(0.25)
        return original_execute_run(self, run_id, ownership_epoch, ownership_token, reviewer, paper)

    monkeypatch.setattr(
        registry_module.InMemoryReviewRunRegistry,
        "_execute_run",
        _slow_execute_run,
    )

    client = TestClient(create_app())
    accepted = client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    ).json()

    with client.stream(
        "GET",
        f"/review/runs/{accepted['run_id']}/events/stream",
        params={"heartbeat_interval_ms": 100, "poll_interval_ms": 20},
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-cache, no-transform"
    assert response.headers["connection"] == "keep-alive"
    assert response.headers["x-papermentor-sse-heartbeat-ms"] == "100"
    assert "event: heartbeat" in body
    assert '"run_state":"pending"' in body or '"run_state":"running"' in body
    assert "event: review_run_completed" in body


def test_async_review_run_lease_renews_while_running(tmp_path: Path, monkeypatch) -> None:
    file_path = tmp_path / "async-lease-renewal.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    chief_module = importlib.import_module("papermentor_os.orchestrator.chief_reviewer")
    original_review_paper = chief_module.ChiefReviewer.review_paper

    def _slow_review_paper(self, *args, **kwargs):
        time.sleep(0.35)
        return original_review_paper(self, *args, **kwargs)

    monkeypatch.setattr(chief_module.ChiefReviewer, "review_paper", _slow_review_paper)

    client = TestClient(
        create_app(
            run_instance_id="lease-owner",
            run_lease_seconds=0.3,
        )
    )
    accepted = client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    ).json()
    initial_heartbeat = accepted["ownership"]["last_heartbeat_at"]

    time.sleep(0.18)

    running_payload = client.get(f"/review/runs/{accepted['run_id']}").json()
    assert running_payload["ownership"]["owner_instance_id"] == "lease-owner"
    assert running_payload["ownership"]["lease_active"] is True
    assert running_payload["ownership"]["owned_by_current_instance"] is True
    assert running_payload["ownership"]["last_heartbeat_at"] > initial_heartbeat

    completed_payload = _poll_run_completion(client, accepted["run_id"], timeout_seconds=3.0)
    assert completed_payload["ownership"]["lease_active"] is False


def test_async_review_run_sse_endpoint_rejects_invalid_last_event_id(tmp_path: Path) -> None:
    file_path = tmp_path / "async-sse-invalid-header.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    client = TestClient(create_app())

    accepted = client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    ).json()
    _poll_run_completion(client, accepted["run_id"])

    response = client.get(
        f"/review/runs/{accepted['run_id']}/events/stream",
        headers={"Last-Event-ID": "invalid"},
    )

    assert response.status_code == 400


def test_async_review_run_sse_endpoint_rejects_invalid_heartbeat_interval(tmp_path: Path) -> None:
    file_path = tmp_path / "async-sse-invalid-heartbeat.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    client = TestClient(create_app())

    accepted = client.post(
        "/review/docx/async",
        json={"file_path": str(file_path)},
    ).json()
    _poll_run_completion(client, accepted["run_id"])

    response = client.get(
        f"/review/runs/{accepted['run_id']}/events/stream",
        params={"heartbeat_interval_ms": 50},
    )

    assert response.status_code == 400


def test_async_review_run_endpoint_returns_404_for_unknown_run() -> None:
    client = TestClient(create_app())

    response = client.get("/review/runs/missing-run")

    assert response.status_code == 404


def test_async_review_run_sse_endpoint_returns_404_for_unknown_run() -> None:
    client = TestClient(create_app())

    response = client.get("/review/runs/missing-run/events/stream")

    assert response.status_code == 404


def test_review_case_catalog_contains_baseline_and_debate_cases() -> None:
    case_ids = {case.case_id for case in REVIEW_CASE_CATALOG}
    tags = {tag for case in REVIEW_CASE_CATALOG for tag in case.tags}

    assert "minimal_review_case" in case_ids
    assert STRONG_REVIEW_CASE.case_id in case_ids
    assert WEAK_REVIEW_CASE.case_id in case_ids
    assert BOUNDARY_REVIEW_CASE.case_id in case_ids
    assert "baseline" in tags
    assert "strong_sample" in tags
    assert "boundary_sample" in tags
    assert "debate_candidate" in tags


def test_get_review_cases_by_tag_returns_expected_fixture_groups() -> None:
    strong_cases = get_review_cases_by_tag("strong_sample")
    weak_cases = get_review_cases_by_tag("weak_sample")

    assert STRONG_REVIEW_CASE in strong_cases
    assert WEAK_REVIEW_CASE in weak_cases
    assert BOUNDARY_REVIEW_CASE in weak_cases


def test_review_endpoint_accepts_request_scoped_llm_config_with_fallback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    file_path = tmp_path / "strong_case.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    reviewer_factory_module = importlib.import_module("papermentor_os.reviewer_factory")

    def _fake_generate_structured(self, messages, schema, config):
        raise LLMProviderError("provider unavailable in test")

    monkeypatch.setattr(
        reviewer_factory_module.OpenAICompatibleProvider,
        "generate_structured",
        _fake_generate_structured,
    )

    client = TestClient(create_app())
    response = client.post(
        "/review/docx",
        json={
            "file_path": str(file_path),
            "llm": {
                "review_backend": "model_with_fallback",
                "provider_id": "openai_compatible",
                "base_url": "https://example.com/v1",
                "api_key": "sk-test",
                "model_name": "gpt-4.1-mini",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["dimension_reports"]) == 5


def test_review_endpoint_rejects_invalid_request_scoped_llm_provider(tmp_path: Path) -> None:
    file_path = tmp_path / "strong_case.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    client = TestClient(create_app())

    response = client.post(
        "/review/docx",
        json={
            "file_path": str(file_path),
            "llm": {
                "review_backend": "model_with_fallback",
                "provider_id": "custom_provider",
                "base_url": "https://example.com/v1",
                "model_name": "gpt-4.1-mini",
            },
        },
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "llm_configuration_error"
    assert "openai_compatible" in detail["message"]


def test_review_endpoint_rejects_private_llm_base_url_by_default(tmp_path: Path) -> None:
    file_path = tmp_path / "strong_case.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    client = TestClient(create_app())

    response = client.post(
        "/review/docx",
        json={
            "file_path": str(file_path),
            "llm": {
                "review_backend": "model_with_fallback",
                "provider_id": "openai_compatible",
                "base_url": "http://127.0.0.1:4000/v1",
                "model_name": "gpt-4.1-mini",
            },
        },
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "llm_configuration_error"
    assert "private network" in detail["message"]


def test_review_endpoint_allows_private_llm_base_url_when_env_enabled(
    tmp_path: Path,
    monkeypatch,
) -> None:
    file_path = tmp_path / "strong_case.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    reviewer_factory_module = importlib.import_module("papermentor_os.reviewer_factory")

    def _fake_generate_structured(self, messages, schema, config):
        raise LLMProviderError("provider unavailable in test")

    monkeypatch.setenv("PAPERMENTOR_OS_ALLOW_PRIVATE_LLM_BASE_URLS", "1")
    monkeypatch.setattr(
        reviewer_factory_module.OpenAICompatibleProvider,
        "generate_structured",
        _fake_generate_structured,
    )

    client = TestClient(create_app())
    response = client.post(
        "/review/docx",
        json={
            "file_path": str(file_path),
            "llm": {
                "review_backend": "model_with_fallback",
                "provider_id": "openai_compatible",
                "base_url": "http://127.0.0.1:4000/v1",
                "api_key": "sk-test",
                "model_name": "gpt-4.1-mini",
            },
        },
    )

    assert response.status_code == 200
    assert len(response.json()["dimension_reports"]) == 5


def test_review_endpoint_surfaces_sanitized_llm_provider_errors_in_model_only_mode(
    tmp_path: Path,
    monkeypatch,
) -> None:
    file_path = tmp_path / "strong_case.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    reviewer_factory_module = importlib.import_module("papermentor_os.reviewer_factory")

    def _fake_generate_structured(self, messages, schema, config):
        raise LLMProviderError("provider failed with secret sk-live-should-not-leak")

    monkeypatch.setattr(
        reviewer_factory_module.OpenAICompatibleProvider,
        "generate_structured",
        _fake_generate_structured,
    )

    client = TestClient(create_app())
    response = client.post(
        "/review/docx",
        json={
            "file_path": str(file_path),
            "llm": {
                "review_backend": "model_only",
                "provider_id": "openai_compatible",
                "base_url": "https://example.com/v1",
                "api_key": "sk-live-should-not-leak",
                "model_name": "gpt-4.1-mini",
            },
        },
    )

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["code"] == "llm_provider_error"
    assert detail["retryable"] is True
    assert "provider request failed" in detail["message"].lower()
    assert "sk-live-should-not-leak" not in response.text


def test_debug_review_endpoint_surfaces_llm_fallback_metadata(
    tmp_path: Path,
    monkeypatch,
) -> None:
    file_path = tmp_path / "strong_case.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    reviewer_factory_module = importlib.import_module("papermentor_os.reviewer_factory")

    def _fake_generate_structured(self, messages, schema, config):
        raise LLMProviderError("provider unavailable in test")

    monkeypatch.setattr(
        reviewer_factory_module.OpenAICompatibleProvider,
        "generate_structured",
        _fake_generate_structured,
    )

    client = TestClient(create_app())
    response = client.post(
        "/review/docx/debug",
        json={
            "file_path": str(file_path),
            "llm": {
                "review_backend": "model_with_fallback",
                "provider_id": "openai_compatible",
                "base_url": "https://example.com/v1",
                "api_key": "sk-test",
                "model_name": "gpt-4.1-mini",
            },
        },
    )

    assert response.status_code == 200
    worker_runs = response.json()["trace"]["worker_runs"]
    assert worker_runs
    assert all(item["review_backend"] == "model_with_fallback" for item in worker_runs)
    assert all(item["fallback_used"] is True for item in worker_runs)
    assert all(item["llm_provider_id"] == "openai_compatible" for item in worker_runs)
    assert all(item["llm_model_name"] == "gpt-4.1-mini" for item in worker_runs)
    assert all(item["structured_output_status"] == "error:LLMProviderError" for item in worker_runs)
    assert all(item["llm_error_category"] == "provider_runtime" for item in worker_runs)
    assert all(item["llm_request_attempts"] == 1 for item in worker_runs)
    assert all(item["llm_retry_count"] == 0 for item in worker_runs)
