from pathlib import Path
from types import SimpleNamespace

import pytest

from papermentor_os.llm import LLMConfigurationError, ReviewBackend, ReviewLLMConfig
from papermentor_os.reviewer_factory import build_chief_reviewer
from papermentor_os.schemas.report import DimensionReport
from papermentor_os.schemas.trace import WorkerExecutionTrace
from papermentor_os.schemas.types import Dimension
from scripts.run_live_llm_smoke import main, run_live_llm_smoke, run_live_llm_smoke_comparison


class _StubReviewer:
    def __init__(self, worker_runs: list[WorkerExecutionTrace]) -> None:
        self.last_worker_execution_traces = worker_runs
        self.last_orchestration_trace = None

    def review_docx(self, file_path: Path) -> SimpleNamespace:
        assert file_path.exists()
        return SimpleNamespace(
            dimension_reports=[
                SimpleNamespace(findings=[object(), object()]),
                SimpleNamespace(findings=[]),
            ],
            priority_actions=[object()],
        )

    def worker_ids(self) -> list[str]:
        return [worker_run.worker_id for worker_run in self.last_worker_execution_traces]

    def run_worker_smoke(self, file_path: Path, worker_id: str) -> tuple[DimensionReport, WorkerExecutionTrace]:
        assert file_path.exists()
        selected_runs = [item for item in self.last_worker_execution_traces if item.worker_id == worker_id]
        assert len(selected_runs) == 1
        return (
            DimensionReport(
                dimension=selected_runs[0].dimension,
                score=8.1,
                summary=f"{worker_id} smoke summary",
                findings=[],
                debate_used=False,
            ),
            selected_runs[0],
        )


class _StubResumeReviewer(_StubReviewer):
    def __init__(self, worker_runs: list[WorkerExecutionTrace]) -> None:
        super().__init__(worker_runs)
        self.parser = SimpleNamespace(parse_file=lambda file_path: SimpleNamespace(file_path=file_path))

    def worker_ids(self) -> list[str]:
        return [
            "TopicScopeAgent",
            "LogicChainAgent",
            "LiteratureSupportAgent",
            "NoveltyDepthAgent",
            "WritingFormatAgent",
        ]

    def run_review_until(self, paper: SimpleNamespace, *, stop_after_worker_id: str) -> SimpleNamespace:
        assert paper.file_path.exists()
        return SimpleNamespace(stop_after_worker_id=stop_after_worker_id, completed_workers=[object(), object()])

    def review_paper(self, paper: SimpleNamespace, *, checkpoint: SimpleNamespace) -> SimpleNamespace:
        assert paper.file_path.exists()
        self.last_orchestration_trace = SimpleNamespace(
            resumed_from_checkpoint=True,
            checkpoint_completed_worker_count=len(checkpoint.completed_workers),
            skipped_worker_ids=["TopicScopeAgent", "LogicChainAgent"],
            resume_start_worker_id="LiteratureSupportAgent",
        )
        return SimpleNamespace(
            dimension_reports=[
                SimpleNamespace(findings=[object(), object()]),
                SimpleNamespace(findings=[]),
            ],
            priority_actions=[object()],
        )


def _build_trace(
    *,
    worker_id: str,
    dimension: Dimension,
    structured_output_status: str = "parsed",
    fallback_used: bool = False,
    llm_error_category: str | None = None,
    llm_request_attempts: int = 1,
    llm_retry_count: int = 0,
    llm_total_tokens: int | None = 32,
) -> WorkerExecutionTrace:
    return WorkerExecutionTrace(
        worker_id=worker_id,
        dimension=dimension,
        score=8.1,
        finding_count=1,
        high_severity_count=0,
        summary="模型输出已生成结构化结论。",
        review_backend=ReviewBackend.MODEL_ONLY.value,
        structured_output_status=structured_output_status,
        fallback_used=fallback_used,
        llm_error_category=llm_error_category,
        llm_request_attempts=llm_request_attempts,
        llm_retry_count=llm_retry_count,
        llm_total_tokens=llm_total_tokens,
    )


def test_run_live_llm_smoke_returns_observability_payload() -> None:
    llm_config = ReviewLLMConfig(
        review_backend=ReviewBackend.MODEL_ONLY,
        provider_id="openai_compatible",
        base_url="https://example.com/v1",
        api_key="sk-test",
        model_name="gpt-4.1-mini",
    )
    worker_runs = [
        _build_trace(
            worker_id="TopicScopeAgent",
            dimension=Dimension.TOPIC_SCOPE,
            llm_request_attempts=1,
            llm_retry_count=0,
            llm_total_tokens=18,
        ),
        _build_trace(
            worker_id="LogicChainAgent",
            dimension=Dimension.LOGIC_CHAIN,
            llm_request_attempts=2,
            llm_retry_count=1,
            llm_total_tokens=26,
        ),
    ]

    payload = run_live_llm_smoke(
        llm_config=llm_config,
        reviewer_builder=lambda _: _StubReviewer(worker_runs),
    )

    assert payload["case_id"] == "topic_precision_case"
    assert payload["review_backend"] == "model_only"
    assert payload["provider_id"] == "openai_compatible"
    assert payload["model_name"] == "gpt-4.1-mini"
    assert payload["resumed_from_checkpoint"] is False
    assert payload["checkpoint_completed_worker_count"] == 0
    assert payload["skipped_worker_count"] == 0
    assert payload["resume_start_worker_id"] is None
    assert payload["all_workers_parsed"] is True
    assert payload["worker_count"] == 2
    assert payload["parsed_worker_count"] == 2
    assert payload["failed_workers"] == []
    assert payload["fallback_worker_ids"] == []
    assert payload["llm_request_attempts"] == 3
    assert payload["llm_retry_count"] == 1
    assert payload["llm_total_tokens"] == 44
    assert payload["finding_count"] == 2
    assert payload["priority_action_count"] == 1
    assert payload["elapsed_seconds"] >= 0.0


def test_live_llm_smoke_main_requires_explicit_provider_config(capsys, monkeypatch) -> None:
    for suffix in ("BASE_URL", "API_KEY", "MODEL_NAME", "PROVIDER_ID", "REVIEW_BACKEND"):
        monkeypatch.delenv(f"PAPERMENTOR_OS_SMOKE_{suffix}", raising=False)
    monkeypatch.setattr("sys.argv", ["run_live_llm_smoke.py"])

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Smoke run requires base_url" in captured.out


def test_live_llm_smoke_main_returns_nonzero_when_any_worker_falls_back(
    capsys,
    monkeypatch,
) -> None:
    worker_runs = [
        _build_trace(
            worker_id="TopicScopeAgent",
            dimension=Dimension.TOPIC_SCOPE,
        ),
        _build_trace(
            worker_id="LogicChainAgent",
            dimension=Dimension.LOGIC_CHAIN,
            structured_output_status="provider_error",
            fallback_used=True,
            llm_error_category="provider_http",
            llm_request_attempts=2,
            llm_retry_count=1,
            llm_total_tokens=11,
        ),
    ]
    monkeypatch.setattr(
        "scripts.run_live_llm_smoke.build_chief_reviewer",
        lambda llm_config: _StubReviewer(worker_runs),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_live_llm_smoke.py",
            "--base-url",
            "https://example.com/v1",
            "--api-key",
            "sk-test",
            "--model-name",
            "gpt-4.1-mini",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 2
    assert '"all_workers_parsed": false' in captured.out
    assert '"fallback_worker_ids": [' in captured.out
    assert '"LogicChainAgent"' in captured.out


def test_run_live_llm_smoke_can_target_single_worker() -> None:
    llm_config = ReviewLLMConfig(
        review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
        provider_id="openai_compatible",
        base_url="https://example.com/v1",
        api_key="sk-test",
        model_name="gpt-4.1-mini",
    )
    worker_runs = [
        _build_trace(
            worker_id="TopicScopeAgent",
            dimension=Dimension.TOPIC_SCOPE,
            llm_request_attempts=1,
            llm_retry_count=0,
            llm_total_tokens=21,
        ),
        _build_trace(
            worker_id="LogicChainAgent",
            dimension=Dimension.LOGIC_CHAIN,
            structured_output_status="provider_error",
            fallback_used=True,
            llm_error_category="provider_network",
            llm_request_attempts=2,
            llm_retry_count=0,
            llm_total_tokens=0,
        ),
    ]

    payload = run_live_llm_smoke(
        llm_config=llm_config,
        worker_id="TopicScopeAgent",
        reviewer_builder=lambda _: _StubReviewer(worker_runs),
    )

    assert payload["selected_worker_id"] == "TopicScopeAgent"
    assert payload["worker_count"] == 1
    assert payload["parsed_worker_count"] == 1
    assert payload["all_workers_parsed"] is True
    assert payload["failed_workers"] == []
    assert payload["llm_request_attempts"] == 1
    assert payload["llm_total_tokens"] == 21


def test_run_live_llm_smoke_single_worker_supports_real_chief_reviewer() -> None:
    payload = run_live_llm_smoke(
        llm_config=ReviewLLMConfig(),
        worker_id="TopicScopeAgent",
        reviewer_builder=lambda _: build_chief_reviewer(),
    )

    assert payload["selected_worker_id"] == "TopicScopeAgent"
    assert payload["worker_count"] == 1
    assert payload["parsed_worker_count"] == 0
    assert payload["all_workers_parsed"] is False
    assert payload["failed_workers"][0]["worker_id"] == "TopicScopeAgent"
    assert payload["resume_after_worker_id"] is None


def test_run_live_llm_smoke_resume_path_supports_real_chief_reviewer() -> None:
    payload = run_live_llm_smoke(
        llm_config=ReviewLLMConfig(),
        resume_after_worker_id="LogicChainAgent",
        reviewer_builder=lambda _: build_chief_reviewer(),
    )

    assert payload["selected_worker_id"] is None
    assert payload["resume_after_worker_id"] == "LogicChainAgent"
    assert payload["resumed_from_checkpoint"] is True
    assert payload["checkpoint_completed_worker_count"] == 2
    assert payload["skipped_worker_count"] == 2
    assert payload["resume_start_worker_id"] == "LiteratureSupportAgent"
    assert payload["worker_count"] == 5
    assert payload["parsed_worker_count"] == 0
    assert payload["all_workers_parsed"] is False


def test_run_live_llm_smoke_supports_resume_path() -> None:
    llm_config = ReviewLLMConfig(
        review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
        provider_id="openai_compatible",
        base_url="https://example.com/v1",
        api_key="sk-test",
        model_name="gpt-4.1-mini",
    )
    worker_runs = [
        _build_trace(
            worker_id="LiteratureSupportAgent",
            dimension=Dimension.LITERATURE_SUPPORT,
            llm_request_attempts=1,
            llm_retry_count=0,
            llm_total_tokens=23,
        ),
        _build_trace(
            worker_id="NoveltyDepthAgent",
            dimension=Dimension.NOVELTY_DEPTH,
            llm_request_attempts=1,
            llm_retry_count=0,
            llm_total_tokens=19,
        ),
        _build_trace(
            worker_id="WritingFormatAgent",
            dimension=Dimension.WRITING_FORMAT,
            llm_request_attempts=1,
            llm_retry_count=0,
            llm_total_tokens=17,
        ),
    ]

    payload = run_live_llm_smoke(
        llm_config=llm_config,
        resume_after_worker_id="LogicChainAgent",
        reviewer_builder=lambda _: _StubResumeReviewer(worker_runs),
    )

    assert payload["selected_worker_id"] is None
    assert payload["resume_after_worker_id"] == "LogicChainAgent"
    assert payload["resumed_from_checkpoint"] is True
    assert payload["checkpoint_completed_worker_count"] == 2
    assert payload["skipped_worker_count"] == 2
    assert payload["resume_start_worker_id"] == "LiteratureSupportAgent"
    assert payload["worker_count"] == 3
    assert payload["parsed_worker_count"] == 3
    assert payload["all_workers_parsed"] is True
    assert payload["llm_request_attempts"] == 3
    assert payload["llm_total_tokens"] == 59
    assert payload["elapsed_seconds"] >= 0.0


def test_run_live_llm_smoke_rejects_resuming_after_final_worker() -> None:
    with pytest.raises(
        LLMConfigurationError,
        match="stop before the final worker",
    ):
        run_live_llm_smoke(
            llm_config=ReviewLLMConfig(),
            resume_after_worker_id="WritingFormatAgent",
            reviewer_builder=lambda _: build_chief_reviewer(),
        )


def test_run_live_llm_smoke_comparison_supports_direct_vs_resume() -> None:
    llm_config = ReviewLLMConfig(
        review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
        provider_id="openai_compatible",
        base_url="https://example.com/v1",
        api_key="sk-test",
        model_name="gpt-4.1-mini",
    )
    baseline_runs = [
        _build_trace(worker_id="TopicScopeAgent", dimension=Dimension.TOPIC_SCOPE, llm_total_tokens=21),
        _build_trace(
            worker_id="LogicChainAgent",
            dimension=Dimension.LOGIC_CHAIN,
            structured_output_status="provider_error",
            fallback_used=True,
            llm_error_category="provider_runtime",
            llm_total_tokens=0,
        ),
    ]
    resumed_runs = [
        _build_trace(worker_id="LiteratureSupportAgent", dimension=Dimension.LITERATURE_SUPPORT, llm_total_tokens=23),
        _build_trace(worker_id="NoveltyDepthAgent", dimension=Dimension.NOVELTY_DEPTH, llm_total_tokens=19),
        _build_trace(worker_id="WritingFormatAgent", dimension=Dimension.WRITING_FORMAT, llm_total_tokens=17),
    ]
    reviewers = iter([
        _StubReviewer(baseline_runs),
        _StubResumeReviewer(resumed_runs),
    ])

    payload = run_live_llm_smoke_comparison(
        llm_config=llm_config,
        compare_resume_after_worker_id="LogicChainAgent",
        reviewer_builder=lambda _: next(reviewers),
    )

    assert payload["compare_resume_after_worker_id"] == "LogicChainAgent"
    assert payload["baseline"]["resumed_from_checkpoint"] is False
    assert payload["baseline"]["parsed_worker_count"] == 1
    assert payload["resume"]["resumed_from_checkpoint"] is True
    assert payload["resume"]["parsed_worker_count"] == 3
    assert payload["parsed_worker_count_delta"] == 2
    assert payload["fallback_worker_count_delta"] == -1


def test_run_live_llm_smoke_comparison_keeps_partial_results_on_phase_error() -> None:
    llm_config = ReviewLLMConfig(
        review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
        provider_id="openai_compatible",
        base_url="https://example.com/v1",
        api_key="sk-test",
        model_name="gpt-4.1-mini",
    )
    reviewers = iter([
        _StubReviewer(
            [
                _build_trace(worker_id="TopicScopeAgent", dimension=Dimension.TOPIC_SCOPE, llm_total_tokens=21),
            ]
        ),
        ValueError("resume branch failed"),
    ])

    def _builder(_: ReviewLLMConfig | None):
        reviewer = next(reviewers)
        if isinstance(reviewer, Exception):
            raise reviewer
        return reviewer

    payload = run_live_llm_smoke_comparison(
        llm_config=llm_config,
        compare_resume_after_worker_id="LogicChainAgent",
        reviewer_builder=_builder,
    )

    assert payload["baseline"]["parsed_worker_count"] == 1
    assert payload["resume"]["parsed_worker_count"] == 0
    assert payload["resume"]["phase_error"] == "resume branch failed"
    assert payload["resume"]["phase_timed_out"] is False
    assert payload["parsed_worker_count_delta"] == -1


def test_live_llm_smoke_main_supports_phase_timeout_argument(
    capsys,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "scripts.run_live_llm_smoke.run_live_llm_smoke_comparison",
        lambda llm_config, case, compare_resume_after_worker_id, phase_timeout_seconds=None: {
            "compare_resume_after_worker_id": compare_resume_after_worker_id,
            "phase_timeout_seconds": phase_timeout_seconds,
            "baseline": {"all_workers_parsed": False, "parsed_worker_count": 1, "fallback_worker_ids": ["LogicChainAgent"]},
            "resume": {"all_workers_parsed": True, "parsed_worker_count": 3, "fallback_worker_ids": []},
            "parsed_worker_count_delta": 2,
            "fallback_worker_count_delta": -1,
        },
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_live_llm_smoke.py",
            "--base-url",
            "https://example.com/v1",
            "--api-key",
            "sk-test",
            "--model-name",
            "gpt-4.1-mini",
            "--compare-resume-after-worker-id",
            "LogicChainAgent",
            "--phase-timeout-seconds",
            "12",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"phase_timeout_seconds": 12.0' in captured.out


def test_live_llm_smoke_main_rejects_worker_and_resume_combination(
    capsys,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_live_llm_smoke.py",
            "--base-url",
            "https://example.com/v1",
            "--api-key",
            "sk-test",
            "--model-name",
            "gpt-4.1-mini",
            "--worker-id",
            "TopicScopeAgent",
            "--resume-after-worker-id",
            "LogicChainAgent",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "does not support combining --worker-id with --resume-after-worker-id" in captured.out


def test_live_llm_smoke_main_supports_compare_resume_argument(
    capsys,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "scripts.run_live_llm_smoke.run_live_llm_smoke_comparison",
        lambda llm_config, case, compare_resume_after_worker_id, phase_timeout_seconds=None: {
            "compare_resume_after_worker_id": compare_resume_after_worker_id,
            "baseline": {"all_workers_parsed": False, "parsed_worker_count": 1, "fallback_worker_ids": ["LogicChainAgent"]},
            "resume": {"all_workers_parsed": True, "parsed_worker_count": 3, "fallback_worker_ids": []},
            "parsed_worker_count_delta": 2,
            "fallback_worker_count_delta": -1,
        },
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_live_llm_smoke.py",
            "--base-url",
            "https://example.com/v1",
            "--api-key",
            "sk-test",
            "--model-name",
            "gpt-4.1-mini",
            "--compare-resume-after-worker-id",
            "LogicChainAgent",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"compare_resume_after_worker_id": "LogicChainAgent"' in captured.out
    assert '"parsed_worker_count_delta": 2' in captured.out
