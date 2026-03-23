from papermentor_os.evals import BenchmarkExpectation, BenchmarkPricingConfig, ReviewBenchmark
from papermentor_os.schemas.debate import DebateCase
from papermentor_os.schemas.report import (
    AdvisorView,
    DimensionReport,
    EvidenceAnchor,
    FinalReport,
    PriorityAction,
    ReviewFinding,
    StudentGuidance,
)
from papermentor_os.schemas.trace import OrchestrationTrace, WorkerExecutionTrace
from papermentor_os.schemas.types import Dimension, Severity


def _build_report() -> FinalReport:
    return FinalReport(
        overall_summary="summary",
        dimension_reports=[
            DimensionReport(
                dimension=Dimension.TOPIC_SCOPE,
                score=5.0,
                summary="topic summary",
                findings=[
                    ReviewFinding(
                        dimension=Dimension.TOPIC_SCOPE,
                        issue_title="摘要没有明确点出研究问题",
                        severity=Severity.HIGH,
                        confidence=0.8,
                        evidence_anchor=EvidenceAnchor(
                            anchor_id="abstract",
                            location_label="摘要",
                            quote="本文设计了一个系统。",
                        ),
                        diagnosis="diagnosis",
                        why_it_matters="why",
                        next_action="明确研究问题",
                        source_agent="TopicScopeAgent",
                        source_skill_version="topic-clarity-rubric@0.1.0",
                    )
                ],
                debate_used=False,
            ),
            DimensionReport(
                dimension=Dimension.LOGIC_CHAIN,
                score=6.0,
                summary="logic summary",
                findings=[
                    ReviewFinding(
                        dimension=Dimension.LOGIC_CHAIN,
                        issue_title="论证链缺少明确的验证环节",
                        severity=Severity.HIGH,
                        confidence=0.8,
                        evidence_anchor=EvidenceAnchor(
                            anchor_id="sec-001",
                            location_label="章节结构",
                            quote="未识别到实验章节。",
                        ),
                        diagnosis="diagnosis",
                        why_it_matters="why",
                        next_action="补实验章节",
                        source_agent="LogicChainAgent",
                        source_skill_version="logic-chain-rubric@0.1.0",
                    )
                ],
                debate_used=True,
            ),
        ],
        priority_actions=[
            PriorityAction(
                title="摘要没有明确点出研究问题",
                severity=Severity.HIGH,
                dimension=Dimension.TOPIC_SCOPE,
                why_it_matters="why",
                next_action="明确研究问题",
                anchor_id="abstract",
            )
        ],
        student_guidance=StudentGuidance(next_steps=["明确研究问题"]),
        advisor_view=AdvisorView(quick_summary="quick", watch_points=[]),
        safety_notice="notice",
    )


def test_review_benchmark_evaluates_case_expectations() -> None:
    benchmark = ReviewBenchmark()
    report = _build_report()
    expectation = BenchmarkExpectation(
        case_id="weak_case",
        expected_high_severity_dimensions=[Dimension.TOPIC_SCOPE, Dimension.LOGIC_CHAIN],
        expected_priority_first_dimension=Dimension.TOPIC_SCOPE,
        expected_debate_dimensions=[Dimension.LOGIC_CHAIN],
        expected_issue_titles=[
            "摘要没有明确点出研究问题",
            "论证链缺少明确的验证环节",
        ],
    )

    result = benchmark.evaluate_case(
        report,
        expectation,
        debate_candidates=[
            DebateCase(
                dimension=Dimension.LOGIC_CHAIN,
                trigger_reason="score is in the borderline band",
                score=6.0,
                confidence_floor=0.8,
                candidate_issue_titles=["论证链缺少明确的验证环节"],
                recommended_action="queue this dimension for selective debate once multi-review support is added",
            )
        ],
    )

    assert result.high_severity_dimension_recall == 1.0
    assert result.priority_first_dimension_match is True
    assert result.debate_dimension_recall == 1.0
    assert result.issue_title_recall == 1.0
    assert result.issue_title_false_positive_rate == 0.0
    assert result.passed is True


def test_review_benchmark_summarizes_multiple_results() -> None:
    benchmark = ReviewBenchmark()
    results = [
        benchmark.evaluate_case(
            _build_report(),
            BenchmarkExpectation(
                case_id="case_a",
                expected_high_severity_dimensions=[Dimension.TOPIC_SCOPE],
                expected_priority_first_dimension=Dimension.TOPIC_SCOPE,
                expected_issue_titles=[
                    "摘要没有明确点出研究问题",
                    "论证链缺少明确的验证环节",
                ],
            ),
        ),
        benchmark.evaluate_case(
            _build_report(),
            BenchmarkExpectation(
                case_id="case_b",
                expected_high_severity_dimensions=[Dimension.TOPIC_SCOPE, Dimension.NOVELTY_DEPTH],
                expected_debate_dimensions=[Dimension.NOVELTY_DEPTH],
                expected_issue_titles=["摘要没有明确点出研究问题"],
            ),
        ),
    ]

    summary = benchmark.summarize(results)

    assert summary.total_cases == 2
    assert summary.fully_passed_cases == 1
    assert summary.high_severity_dimension_recall == 2 / 3
    assert summary.priority_first_dimension_accuracy == 1.0
    assert summary.debate_dimension_recall == 0.0
    assert summary.issue_title_recall == 1.0
    assert summary.issue_title_false_positive_rate == 1 / 4


def test_review_benchmark_reports_missing_and_unexpected_issue_titles() -> None:
    benchmark = ReviewBenchmark()
    result = benchmark.evaluate_case(
        _build_report(),
        BenchmarkExpectation(
            case_id="case_c",
            expected_issue_titles=[
                "摘要没有明确点出研究问题",
                "缺少显式结论章节，论证收束不足",
            ],
        ),
    )

    assert result.issue_title_recall == 0.5
    assert result.missing_issue_titles == ["缺少显式结论章节，论证收束不足"]
    assert result.unexpected_issue_titles == ["论证链缺少明确的验证环节"]
    assert result.issue_title_false_positive_rate == 0.5
    assert result.passed is False


def test_review_benchmark_aggregates_llm_runtime_observability() -> None:
    benchmark = ReviewBenchmark()
    result = benchmark.evaluate_case(
        _build_report(),
        BenchmarkExpectation(case_id="case_llm"),
        worker_execution_traces=[
            WorkerExecutionTrace(
                worker_id="TopicScopeAgent",
                dimension=Dimension.TOPIC_SCOPE,
                score=6.0,
                finding_count=1,
                high_severity_count=1,
                debate_candidate=False,
                debate_used=False,
                summary="topic",
                review_backend="model_with_fallback",
                structured_output_status="parsed",
                fallback_used=False,
                llm_request_attempts=2,
                llm_retry_count=1,
                llm_prompt_tokens=120,
                llm_completion_tokens=60,
                llm_total_tokens=180,
            ),
            WorkerExecutionTrace(
                worker_id="LogicChainAgent",
                dimension=Dimension.LOGIC_CHAIN,
                score=6.0,
                finding_count=1,
                high_severity_count=1,
                debate_candidate=False,
                debate_used=False,
                summary="logic",
                review_backend="model_with_fallback",
                llm_error_category="provider_network",
                structured_output_status="error:LLMProviderError",
                fallback_used=True,
                llm_request_attempts=2,
                llm_retry_count=1,
            ),
        ],
    )

    assert result.llm_request_attempts == 4
    assert result.llm_retry_count == 2
    assert result.llm_fallback_count == 1
    assert result.llm_error_count == 1
    assert result.llm_error_categories == {"provider_network": 1}
    assert result.llm_usage_observation_count == 1
    assert result.llm_total_tokens == 180


def test_review_benchmark_estimates_llm_costs() -> None:
    benchmark = ReviewBenchmark()
    results = [
        BenchmarkExpectation(case_id="case_pricing"),
    ]

    case_result = benchmark.evaluate_case(
        _build_report(),
        results[0],
        worker_execution_traces=[
            WorkerExecutionTrace(
                worker_id="TopicScopeAgent",
                dimension=Dimension.TOPIC_SCOPE,
                score=6.0,
                finding_count=1,
                high_severity_count=1,
                debate_candidate=False,
                debate_used=False,
                summary="topic",
                review_backend="model_only",
                structured_output_status="parsed",
                fallback_used=False,
                llm_request_attempts=1,
                llm_retry_count=0,
                llm_prompt_tokens=1000,
                llm_completion_tokens=500,
                llm_total_tokens=1500,
            )
        ],
    )

    summary = benchmark.summarize_variant(
        [case_result],
        variant_id="model_only",
        review_backend="model_only",
        pricing_config=BenchmarkPricingConfig(
            input_price_per_1k_tokens_usd=0.002,
            output_price_per_1k_tokens_usd=0.006,
        ),
    )

    assert summary.llm_input_cost_estimate_usd == 0.002
    assert summary.llm_output_cost_estimate_usd == 0.003
    assert summary.llm_total_cost_estimate_usd == 0.005


def test_review_benchmark_tracks_checkpoint_resume_observability() -> None:
    benchmark = ReviewBenchmark()
    result = benchmark.evaluate_case(
        _build_report(),
        BenchmarkExpectation(case_id="case_resume"),
        orchestration_trace=OrchestrationTrace(
            stage="draft",
            discipline="computer_science",
            worker_sequence=[
                "TopicScopeAgent",
                "LogicChainAgent",
                "LiteratureSupportAgent",
                "NoveltyDepthAgent",
                "WritingFormatAgent",
            ],
            resumed_from_checkpoint=True,
            checkpoint_completed_worker_count=2,
            resumed_worker_ids=["TopicScopeAgent", "LogicChainAgent"],
            skipped_worker_ids=["TopicScopeAgent", "LogicChainAgent"],
            resume_start_worker_id="LiteratureSupportAgent",
            total_findings=2,
            debate_candidate_dimensions=[],
            debated_dimensions=[],
        ),
    )

    summary = benchmark.summarize_variant([result])

    assert result.resumed_from_checkpoint is True
    assert result.checkpoint_completed_worker_count == 2
    assert result.skipped_worker_count == 2
    assert summary.resumed_case_count == 1
    assert summary.checkpoint_completed_worker_count == 2
    assert summary.skipped_worker_count == 2
