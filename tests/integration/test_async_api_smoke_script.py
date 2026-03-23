import json
import importlib
import time

from papermentor_os.api.app import create_app
from papermentor_os.llm import ReviewBackend, ReviewLLMConfig
from scripts.run_async_api_smoke import main, run_async_api_smoke


def test_run_async_api_smoke_returns_completed_payload_for_real_app() -> None:
    payload = run_async_api_smoke()

    assert payload["case_id"] == "topic_precision_case"
    assert payload["review_backend"] == "rule_only"
    assert payload["final_state"] == "completed"
    assert payload["lease_active"] is False
    assert payload["worker_count"] == 5
    assert payload["completed_worker_count"] == 5
    assert payload["parsed_worker_count"] == 0
    assert payload["all_workers_parsed"] is False
    assert payload["finding_count"] >= 0
    assert payload["priority_action_count"] >= 0
    assert payload["resumed_from_checkpoint"] is False
    assert payload["checkpoint_completed_worker_count"] == 0
    assert payload["event_types"][0] == "created"
    assert "completed" in payload["event_types"]


def test_async_api_smoke_main_supports_rule_only_defaults(capsys, monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["run_async_api_smoke.py"])

    exit_code = main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["review_backend"] == "rule_only"
    assert payload["final_state"] == "completed"


def test_async_api_smoke_main_passes_llm_args(monkeypatch, capsys) -> None:
    captured_kwargs: dict[str, object] = {}

    def _fake_run_async_api_smoke(**kwargs):
        captured_kwargs.update(kwargs)
        return {
            "review_backend": ReviewBackend.MODEL_WITH_FALLBACK.value,
            "final_state": "completed",
            "all_workers_parsed": True,
        }

    monkeypatch.setattr("scripts.run_async_api_smoke.run_async_api_smoke", _fake_run_async_api_smoke)
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_async_api_smoke.py",
            "--review-backend",
            "model_with_fallback",
            "--base-url",
            "https://example.com/v1",
            "--api-key",
            "sk-test",
            "--model-name",
            "gpt-4.1-mini",
            "--poll-timeout-seconds",
            "12",
            "--poll-interval-seconds",
            "0.2",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    llm_config = captured_kwargs["llm_config"]
    assert exit_code == 0
    assert payload["review_backend"] == "model_with_fallback"
    assert llm_config.review_backend == ReviewBackend.MODEL_WITH_FALLBACK
    assert llm_config.base_url == "https://example.com/v1"
    assert llm_config.api_key == "sk-test"
    assert llm_config.model_name == "gpt-4.1-mini"
    assert captured_kwargs["poll_timeout_seconds"] == 12.0
    assert captured_kwargs["poll_interval_seconds"] == 0.2


def test_run_async_api_smoke_supports_stale_claim_path(monkeypatch) -> None:
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

    payload = run_async_api_smoke(
        claim_stale_run=True,
        lease_seconds=0.15,
        claim_poll_timeout_seconds=2.0,
        poll_timeout_seconds=4.0,
    )

    assert payload["final_state"] == "completed"
    assert payload["claim_stale_run"] is True
    assert payload["claim_result"] is not None
    assert payload["claim_result"]["claimed"] is True
    assert payload["claim_result"]["resume_started"] is True
    assert payload["claim_result"]["ownership"]["owner_instance_id"] == "async-api-smoke-secondary"
    assert payload["owned_by"] == "async-api-smoke-secondary"
    assert "ownership_claimed" in payload["event_types"]
    assert "resumed_completed" in payload["event_types"] or "resumed_failed" in payload["event_types"]


def test_run_async_api_smoke_claim_path_passes_server_llm_config(monkeypatch) -> None:
    chief_module = importlib.import_module("papermentor_os.orchestrator.chief_reviewer")
    app_module = importlib.import_module("papermentor_os.api.app")
    original_review_paper = chief_module.ChiefReviewer.review_paper
    original_build_chief_reviewer = app_module.build_chief_reviewer
    captured_server_llm_configs = []

    def _slow_review_paper(self, *args, **kwargs):
        time.sleep(0.35)
        return original_review_paper(self, *args, **kwargs)

    def _rule_only_builder(llm_config=None, **kwargs):
        return original_build_chief_reviewer(None, **kwargs)

    def _capturing_app_builder(**kwargs):
        captured_server_llm_configs.append(kwargs.get("server_llm_config"))
        return create_app(**kwargs)

    monkeypatch.setattr(chief_module.ChiefReviewer, "review_paper", _slow_review_paper)
    monkeypatch.setattr(app_module, "build_chief_reviewer", _rule_only_builder)

    payload = run_async_api_smoke(
        llm_config=ReviewLLMConfig(
            review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
            base_url="https://example.com/v1",
            api_key="sk-test",
            model_name="test-model",
        ),
        claim_stale_run=True,
        lease_seconds=0.15,
        claim_poll_timeout_seconds=2.0,
        poll_timeout_seconds=4.0,
        app_builder=_capturing_app_builder,
    )

    assert payload["final_state"] == "completed"
    assert payload["claim_result"] is not None
    assert payload["claim_result"]["resume_started"] is True
    assert len(captured_server_llm_configs) == 2
    assert all(config is not None for config in captured_server_llm_configs)
    assert all(config.api_key == "sk-test" for config in captured_server_llm_configs)
    assert all(config.model_name == "test-model" for config in captured_server_llm_configs)


def test_async_api_smoke_main_passes_claim_args(monkeypatch, capsys) -> None:
    captured_kwargs: dict[str, object] = {}

    def _fake_run_async_api_smoke(**kwargs):
        captured_kwargs.update(kwargs)
        return {
            "review_backend": ReviewBackend.RULE_ONLY.value,
            "final_state": "completed",
            "all_workers_parsed": False,
        }

    monkeypatch.setattr("scripts.run_async_api_smoke.run_async_api_smoke", _fake_run_async_api_smoke)
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_async_api_smoke.py",
            "--claim-stale-run",
            "--lease-seconds",
            "0.2",
            "--claim-poll-timeout-seconds",
            "5",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["final_state"] == "completed"
    assert captured_kwargs["claim_stale_run"] is True
    assert captured_kwargs["lease_seconds"] == 0.2
    assert captured_kwargs["claim_poll_timeout_seconds"] == 5.0


def test_async_api_smoke_main_prints_timeout_diagnostics(monkeypatch, capsys) -> None:
    from scripts.run_async_api_smoke import _AsyncApiSmokeTimeoutError

    monkeypatch.setattr(
        "scripts.run_async_api_smoke.run_async_api_smoke",
        lambda **kwargs: (_ for _ in ()).throw(
            _AsyncApiSmokeTimeoutError(
                message="async api smoke timed out after 12.0s.",
                diagnostics={
                    "run_id": "run-1",
                    "event_count": 7,
                    "last_event_type": "updated",
                },
            )
        ),
    )
    monkeypatch.setattr("sys.argv", ["run_async_api_smoke.py"])

    exit_code = main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 1
    assert payload["error"] == "async api smoke timed out after 12.0s."
    assert payload["diagnostics"]["run_id"] == "run-1"
    assert payload["diagnostics"]["event_count"] == 7
    assert payload["diagnostics"]["last_event_type"] == "updated"
