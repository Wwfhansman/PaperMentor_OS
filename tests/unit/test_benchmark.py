from papermentor_os.evals import BenchmarkExpectation, ReviewBenchmark
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
