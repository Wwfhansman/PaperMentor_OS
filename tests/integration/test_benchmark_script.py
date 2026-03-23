import json

from papermentor_os.agents.literature_support import LiteratureSupportAgent
from papermentor_os.agents.logic_chain import LogicChainAgent
from papermentor_os.agents.novelty_depth import NoveltyDepthAgent
from papermentor_os.agents.topic_scope import TopicScopeAgent
from papermentor_os.agents.writing_format import WritingFormatAgent
from papermentor_os.llm import FakeLLMProvider, LLMClient, ProviderConfig
from papermentor_os.llm import ReviewBackend, ReviewLLMConfig
from papermentor_os.orchestrator.chief_reviewer import ChiefReviewer
from scripts.run_benchmark import main, run_benchmark
from tests.fixtures.review_cases import (
    LITERATURE_PRECISION_CASE,
    LOGIC_PRECISION_CASE,
    NOVELTY_PRECISION_CASE,
    TOPIC_PRECISION_CASE,
    WRITING_PRECISION_CASE,
)


def test_run_benchmark_returns_summary_for_evaluation_fixtures() -> None:
    payload = run_benchmark()

    assert payload["total_cases"] >= 44
    assert "issue_title_recall" in payload
    assert "issue_title_false_positive_rate" in payload
    assert "case_results" in payload
    case_ids = {item["case_id"] for item in payload["case_results"]}
    assert "contents_variation_case" in case_ids
    assert "complex_contents_variation_case" in case_ids
    assert "contents_header_footer_variation_case" in case_ids
    assert "caption_variation_case" in case_ids
    assert "equation_caption_variation_case" in case_ids
    assert "annotation_block_variation_case" in case_ids
    assert "footer_footnote_noise_variation_case" in case_ids
    assert "footnote_body_variation_case" in case_ids
    assert "docx_footnote_object_variation_case" in case_ids
    assert "docx_endnote_object_variation_case" in case_ids
    assert "mixed_note_object_variation_case" in case_ids
    assert "multiline_note_object_variation_case" in case_ids
    assert "table_adjacent_note_object_variation_case" in case_ids
    assert "running_header_footer_metadata_case" in case_ids
    assert "running_english_header_footer_case" in case_ids
    assert "abstract_running_header_variation_case" in case_ids
    assert "repeated_section_header_noise_case" in case_ids
    assert "repeated_parent_section_header_noise_case" in case_ids
    assert "repeated_subsection_header_noise_case" in case_ids
    assert "abbreviated_section_header_noise_case" in case_ids
    assert "unnumbered_abbreviated_section_header_noise_case" in case_ids
    assert "contents_field_code_variation_case" in case_ids
    assert "cover_page_variation_case" in case_ids
    assert "cover_page_table_variation_case" in case_ids
    assert "back_matter_variation_case" in case_ids
    assert "post_reference_bio_variation_case" in case_ids
    assert "keyword_variation_case" in case_ids
    assert "metadata_block_variation_case" in case_ids
    assert "author_info_variation_case" in case_ids
    assert "appendix_variation_case" in case_ids
    assert "english_appendix_variation_case" in case_ids
    assert "department_info_variation_case" in case_ids
    assert "bilingual_abstract_case" in case_ids
    assert "declaration_variation_case" in case_ids
    assert "front_matter_combo_variation_case" in case_ids
    assert "front_matter_multiline_variation_case" in case_ids
    assert "front_matter_spacing_variation_case" in case_ids
    assert "front_matter_table_variation_case" in case_ids
    assert "docx_table_front_matter_case" in case_ids
    assert "complex_table_front_matter_case" in case_ids
    assert "appendix_contents_variation_case" in case_ids
    assert "appendix_figure_list_variation_case" in case_ids
    assert "literature_precision_case" in case_ids
    assert "logic_precision_case" in case_ids
    assert "novelty_precision_case" in case_ids
    assert "template_variation_case" in case_ids
    assert "writing_precision_case" in case_ids
    assert "strong_review_case" in case_ids
    assert "topic_precision_case" in case_ids
    assert "weak_review_case" in case_ids
    assert "boundary_review_case" in case_ids


def test_run_benchmark_supports_markdown_output(capsys, monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["run_benchmark.py", "--format", "markdown"])

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "# PaperMentor OS Benchmark" in captured.out


def test_run_benchmark_returns_failure_code_when_threshold_is_not_met(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["run_benchmark.py", "--min-issue-title-recall", "1.1"],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Invalid threshold value." in captured.out


def test_run_benchmark_returns_regression_exit_code_when_gate_fails(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.run_benchmark.run_benchmark",
        lambda tag="evaluation_fixture": {
            "total_cases": 1,
            "fully_passed_cases": 0,
            "high_severity_dimension_recall": 0.8,
            "priority_first_dimension_accuracy": 1.0,
            "debate_dimension_recall": 0.5,
            "issue_title_recall": 0.7,
            "issue_title_false_positive_rate": 0.2,
            "case_results": [],
        },
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_benchmark.py",
            "--max-issue-title-fpr",
            "0.1",
            "--min-issue-title-recall",
            "0.9",
            "--min-debate-recall",
            "0.8",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "failed_checks" in captured.out


def test_run_benchmark_supports_multiple_variants(monkeypatch) -> None:
    monkeypatch.setattr("scripts.run_benchmark.build_chief_reviewer", lambda llm_config=None: ChiefReviewer())

    payload = run_benchmark(
        variants=["rule", "model_with_fallback"],
        llm_config=ReviewLLMConfig(
            provider_id="openai_compatible",
            base_url="https://example.com/v1",
            model_name="gpt-4.1-mini",
        ),
    )

    assert "variant_summaries" in payload
    assert len(payload["variant_summaries"]) == 2
    assert payload["variant_summaries"][0]["variant_id"] == "rule"
    assert payload["variant_summaries"][1]["variant_id"] == "model_with_fallback"
    assert payload["variant_summaries"][0]["expectation_override_case_count"] == 0
    assert payload["variant_summaries"][1]["expectation_override_case_count"] == 51


def test_run_benchmark_supports_checkpoint_resume_path(monkeypatch) -> None:
    monkeypatch.setattr("scripts.run_benchmark.build_chief_reviewer", lambda llm_config=None: ChiefReviewer())

    payload = run_benchmark(
        tag="model_semantic_fixture",
        resume_after_worker_id="LogicChainAgent",
    )

    assert payload["total_cases"] == 5
    assert payload["resumed_case_count"] == 5
    assert payload["checkpoint_completed_worker_count"] == 10
    assert payload["skipped_worker_count"] == 10
    assert all(case_result["resumed_from_checkpoint"] for case_result in payload["case_results"])
    assert all(case_result["checkpoint_completed_worker_count"] == 2 for case_result in payload["case_results"])
    assert all(case_result["skipped_worker_count"] == 2 for case_result in payload["case_results"])


def test_run_benchmark_supports_fake_model_semantic_expectations() -> None:
    def _reviewer_builder(llm_config: ReviewLLMConfig | None) -> ChiefReviewer:
        assert llm_config is not None
        assert llm_config.review_backend == ReviewBackend.MODEL_ONLY
        topic_provider = FakeLLMProvider(
            responses=[
                json.dumps(
                    {
                        "summary": "模型判断选题对象明确，但研究问题定义还可以再收束。",
                        "score": 8.2,
                        "findings": [
                            {
                                "issue_title": "模型判断研究问题定义还可以再收束",
                                "severity": "medium",
                                "confidence": 0.82,
                                "diagnosis": "摘要给出了研究方向和评审场景，但对核心问题边界的措辞还不够集中。",
                                "why_it_matters": "研究问题再收束一点，后续方法与实验指标会更容易对齐。",
                                "next_action": "在摘要第二句单独写清楚要解决的导师初审效率问题及评价边界。",
                                "evidence_anchor_id": "abstract",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断选题对象清晰。",
                        "score": 8.8,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断选题对象清晰。",
                        "score": 8.8,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断选题对象清晰。",
                        "score": 8.8,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断选题对象清晰。",
                        "score": 8.8,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        logic_provider = FakeLLMProvider(
            responses=[
                json.dumps(
                    {
                        "summary": "模型判断论证链整体闭环较完整。",
                        "score": 8.7,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断论证链主干完整，但结论段对验证结果的回收还可以更集中。",
                        "score": 8.1,
                        "findings": [
                            {
                                "issue_title": "模型判断结论段对验证结果的回收还可以更集中",
                                "severity": "medium",
                                "confidence": 0.8,
                                "diagnosis": "结论段已经总结了论文价值，但对实验验证结果的回收仍然偏概括。",
                                "why_it_matters": "结论段如果不能明确回收验证结果，论证链最后一环会显得偏松。",
                                "next_action": "在结论首段补一句，明确对应实验章节中哪些结果支撑了核心论断。",
                                "evidence_anchor_id": "abstract",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断论证链整体闭环较完整。",
                        "score": 8.7,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断论证链整体闭环较完整。",
                        "score": 8.7,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断论证链整体闭环较完整。",
                        "score": 8.7,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        literature_provider = FakeLLMProvider(
            responses=[
                json.dumps(
                    {
                        "summary": "模型判断文献支撑整体充分。",
                        "score": 8.6,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断文献支撑整体充分。",
                        "score": 8.6,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断文献支撑基础较稳，但相关工作比较段还可以更明确收束差异点。",
                        "score": 8.0,
                        "findings": [
                            {
                                "issue_title": "模型判断相关工作比较段还可以更明确收束差异点",
                                "severity": "medium",
                                "confidence": 0.79,
                                "diagnosis": "相关工作已经覆盖主要参考对象，但对当前方案与已有方法差异的归纳还不够聚焦。",
                                "why_it_matters": "如果比较段只罗列已有方法，评审者会更难快速判断本文文献定位是否成立。",
                                "next_action": "在相关工作末尾补一段，明确写出本文相对已有方案的两个核心差异点。",
                                "evidence_anchor_id": "references",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断文献支撑整体充分。",
                        "score": 8.6,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断文献支撑整体充分。",
                        "score": 8.6,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        novelty_provider = FakeLLMProvider(
            responses=[
                json.dumps(
                    {
                        "summary": "模型判断创新点表达较清楚。",
                        "score": 8.5,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断创新点表达较清楚。",
                        "score": 8.5,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断创新点表达较清楚。",
                        "score": 8.5,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断创新点成立基础较稳，但表述还可以再压缩成更集中的一句。",
                        "score": 8.1,
                        "findings": [
                            {
                                "issue_title": "模型判断创新点表述还可以再压缩成更集中的一句",
                                "severity": "medium",
                                "confidence": 0.78,
                                "diagnosis": "摘要和方法部分已经提到创新方向，但创新点句子仍然有些分散。",
                                "why_it_matters": "创新点如果不够集中，导师初审时会更难快速判断研究深度和贡献边界。",
                                "next_action": "把创新点浓缩成一句主陈述，再用下一句补充其相对 baseline 的具体增益。",
                                "evidence_anchor_id": "abstract",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断创新点表达较清楚。",
                        "score": 8.5,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        writing_provider = FakeLLMProvider(
            responses=[
                json.dumps(
                    {
                        "summary": "模型判断写作表达总体清楚。",
                        "score": 8.4,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断写作表达总体清楚。",
                        "score": 8.4,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断写作表达总体清楚。",
                        "score": 8.4,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断写作表达总体清楚。",
                        "score": 8.4,
                        "findings": [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "summary": "模型判断摘要表达整体清晰，但句间衔接还可以更紧凑。",
                        "score": 8.0,
                        "findings": [
                            {
                                "issue_title": "模型判断摘要句间衔接还可以更紧凑",
                                "severity": "medium",
                                "confidence": 0.77,
                                "diagnosis": "摘要的信息点已经覆盖问题、方法和验证，但句间转折还略显松散。",
                                "why_it_matters": "摘要衔接更紧凑，导师初审时能更快抓住论文主线和重点。",
                                "next_action": "把摘要重写为问题、方法、验证、结论四句式，减少并列短句的跳跃感。",
                                "evidence_anchor_id": "abstract",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        return ChiefReviewer(
            topic_scope_agent=TopicScopeAgent(
                llm_client=LLMClient(topic_provider),
                llm_config=ProviderConfig(
                    provider_id="fake",
                    model_name="semantic-topic-fake-model",
                    prompt_char_budget=4000,
                ),
                review_backend=ReviewBackend.MODEL_ONLY,
            ),
            logic_chain_agent=LogicChainAgent(
                llm_client=LLMClient(logic_provider),
                llm_config=ProviderConfig(
                    provider_id="fake",
                    model_name="semantic-logic-fake-model",
                    prompt_char_budget=4000,
                ),
                review_backend=ReviewBackend.MODEL_ONLY,
            ),
            literature_support_agent=LiteratureSupportAgent(
                llm_client=LLMClient(literature_provider),
                llm_config=ProviderConfig(
                    provider_id="fake",
                    model_name="semantic-literature-fake-model",
                    prompt_char_budget=4000,
                ),
                review_backend=ReviewBackend.MODEL_ONLY,
            ),
            novelty_depth_agent=NoveltyDepthAgent(
                llm_client=LLMClient(novelty_provider),
                llm_config=ProviderConfig(
                    provider_id="fake",
                    model_name="semantic-novelty-fake-model",
                    prompt_char_budget=4000,
                ),
                review_backend=ReviewBackend.MODEL_ONLY,
            ),
            writing_format_agent=WritingFormatAgent(
                llm_client=LLMClient(writing_provider),
                llm_config=ProviderConfig(
                    provider_id="fake",
                    model_name="semantic-writing-fake-model",
                    prompt_char_budget=4000,
                ),
                review_backend=ReviewBackend.MODEL_ONLY,
            ),
        )

    payload = run_benchmark(
        tag="model_semantic_fixture",
        variants=["model_only"],
        llm_config=ReviewLLMConfig(
            provider_id="openai_compatible",
            base_url="https://example.com/v1",
            model_name="gpt-4.1-mini",
        ),
        reviewer_builder=_reviewer_builder,
    )

    assert payload["variant_id"] == "model_only"
    assert payload["expectation_override_case_count"] == 5
    assert payload["total_cases"] == 5
    assert payload["fully_passed_cases"] == 5
    assert payload["priority_first_dimension_accuracy"] == 1.0
    assert payload["issue_title_recall"] == 1.0
    assert payload["issue_title_false_positive_rate"] == 0.0
    case_results = {item["case_id"]: item for item in payload["case_results"]}
    assert case_results[TOPIC_PRECISION_CASE.case_id]["actual_issue_titles"] == ["模型判断研究问题定义还可以再收束"]
    assert case_results[TOPIC_PRECISION_CASE.case_id]["unexpected_issue_titles"] == []
    assert case_results[TOPIC_PRECISION_CASE.case_id]["llm_request_attempts"] == 5
    assert case_results[LOGIC_PRECISION_CASE.case_id]["actual_issue_titles"] == ["模型判断结论段对验证结果的回收还可以更集中"]
    assert case_results[LOGIC_PRECISION_CASE.case_id]["unexpected_issue_titles"] == []
    assert case_results[LOGIC_PRECISION_CASE.case_id]["llm_request_attempts"] == 5
    assert case_results[LITERATURE_PRECISION_CASE.case_id]["actual_issue_titles"] == ["模型判断相关工作比较段还可以更明确收束差异点"]
    assert case_results[LITERATURE_PRECISION_CASE.case_id]["unexpected_issue_titles"] == []
    assert case_results[LITERATURE_PRECISION_CASE.case_id]["llm_request_attempts"] == 5
    assert case_results[NOVELTY_PRECISION_CASE.case_id]["actual_issue_titles"] == ["模型判断创新点表述还可以再压缩成更集中的一句"]
    assert case_results[NOVELTY_PRECISION_CASE.case_id]["unexpected_issue_titles"] == []
    assert case_results[NOVELTY_PRECISION_CASE.case_id]["llm_request_attempts"] == 5
    assert case_results[WRITING_PRECISION_CASE.case_id]["actual_issue_titles"] == ["模型判断摘要句间衔接还可以更紧凑"]
    assert case_results[WRITING_PRECISION_CASE.case_id]["unexpected_issue_titles"] == []
    assert case_results[WRITING_PRECISION_CASE.case_id]["llm_request_attempts"] == 5


def test_run_benchmark_passes_variant_id_into_expectation_builder(monkeypatch) -> None:
    captured_variant_ids: list[str] = []

    def _fake_build_expectation_from_case(case, *, variant_id="rule"):
        captured_variant_ids.append(variant_id)
        from papermentor_os.evals import BenchmarkExpectation

        return BenchmarkExpectation(case_id=case.case_id)

    monkeypatch.setattr("scripts.run_benchmark.build_chief_reviewer", lambda llm_config=None: ChiefReviewer())
    monkeypatch.setattr("scripts.run_benchmark.build_expectation_from_case", _fake_build_expectation_from_case)

    run_benchmark(
        variants=["rule", "model_with_fallback"],
        llm_config=ReviewLLMConfig(
            provider_id="openai_compatible",
            base_url="https://example.com/v1",
            model_name="gpt-4.1-mini",
        ),
    )

    assert "rule" in captured_variant_ids
    assert "model_with_fallback" in captured_variant_ids


def test_run_benchmark_markdown_supports_comparison_output(capsys, monkeypatch) -> None:
    monkeypatch.setattr("scripts.run_benchmark.build_chief_reviewer", lambda llm_config=None: ChiefReviewer())
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_benchmark.py",
            "--format",
            "markdown",
            "--variant",
            "rule",
            "--variant",
            "model_with_fallback",
            "--llm-base-url",
            "https://example.com/v1",
            "--llm-model-name",
            "gpt-4.1-mini",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "# PaperMentor OS Benchmark Comparison" in captured.out


def test_run_benchmark_supports_pricing_arguments(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.run_benchmark.run_benchmark",
        lambda tag="evaluation_fixture", pricing_config=None: {
            "variant_id": "model_only",
            "review_backend": "model_only",
            "llm_request_attempts": 1,
            "llm_retry_count": 0,
            "llm_fallback_count": 0,
            "llm_error_count": 0,
            "llm_error_categories": {},
            "llm_usage_observation_count": 1,
            "llm_prompt_tokens": 1000,
            "llm_completion_tokens": 500,
            "llm_total_tokens": 1500,
            "llm_input_cost_estimate_usd": pricing_config.input_price_per_1k_tokens_usd if pricing_config else None,
            "llm_output_cost_estimate_usd": pricing_config.output_price_per_1k_tokens_usd if pricing_config else None,
            "llm_total_cost_estimate_usd": (
                (pricing_config.input_price_per_1k_tokens_usd if pricing_config else 0.0)
                + (pricing_config.output_price_per_1k_tokens_usd if pricing_config else 0.0)
            ),
            "total_cases": 1,
            "fully_passed_cases": 1,
            "elapsed_seconds": 1.0,
            "average_case_duration_ms": 10.0,
            "high_severity_dimension_recall": 1.0,
            "priority_first_dimension_accuracy": 1.0,
            "debate_dimension_recall": 1.0,
            "issue_title_recall": 1.0,
            "issue_title_false_positive_rate": 0.0,
            "case_results": [],
        },
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_benchmark.py",
            "--format",
            "markdown",
            "--llm-input-price-per-1k-tokens",
            "0.002",
            "--llm-output-price-per-1k-tokens",
            "0.006",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "LLM input cost estimate usd: 0.002000" in captured.out
    assert "LLM output cost estimate usd: 0.006000" in captured.out


def test_run_benchmark_passes_resume_after_worker_id_argument(capsys, monkeypatch) -> None:
    captured_resume_after_worker_id: list[str | None] = []

    def _fake_run_benchmark(tag="evaluation_fixture", resume_after_worker_id=None):
        captured_resume_after_worker_id.append(resume_after_worker_id)
        return {
            "variant_id": "rule",
            "review_backend": "rule_only",
            "resumed_case_count": 1,
            "checkpoint_completed_worker_count": 2,
            "skipped_worker_count": 2,
            "total_cases": 1,
            "fully_passed_cases": 1,
            "elapsed_seconds": 1.0,
            "average_case_duration_ms": 10.0,
            "high_severity_dimension_recall": 1.0,
            "priority_first_dimension_accuracy": 1.0,
            "debate_dimension_recall": 1.0,
            "issue_title_recall": 1.0,
            "issue_title_false_positive_rate": 0.0,
            "case_results": [],
        }

    monkeypatch.setattr("scripts.run_benchmark.run_benchmark", _fake_run_benchmark)
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_benchmark.py",
            "--format",
            "markdown",
            "--resume-after-worker-id",
            "LogicChainAgent",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured_resume_after_worker_id == ["LogicChainAgent"]
    assert "Resumed cases: 1" in captured.out


def test_run_benchmark_returns_failure_code_for_invalid_llm_configuration(
    capsys,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_benchmark.py",
            "--variant",
            "model_only",
            "--llm-base-url",
            "http://127.0.0.1:4000/v1",
            "--llm-model-name",
            "gpt-4.1-mini",
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "private network" in captured.out
