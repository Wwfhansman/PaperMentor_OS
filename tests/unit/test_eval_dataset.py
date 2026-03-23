from papermentor_os.evals import (
    build_expectation_from_case,
    case_has_expectation_override,
    load_benchmark_cases,
    render_benchmark_markdown,
)
from papermentor_os.evals.models import BenchmarkSummary
from tests.fixtures.review_cases import (
    ABSTRACT_RUNNING_HEADER_VARIATION_CASE,
    APPENDIX_VARIATION_CASE,
    BenchmarkExpectationOverride,
    DOCX_ENDNOTE_OBJECT_VARIATION_CASE,
    LOGIC_PRECISION_CASE,
    LITERATURE_PRECISION_CASE,
    NOVELTY_PRECISION_CASE,
    ReviewCaseSpec,
    SectionSpec,
    TEMPLATE_VARIATION_CASE,
    TOPIC_PRECISION_CASE,
    WEAK_REVIEW_CASE,
    WRITING_PRECISION_CASE,
)


def test_build_expectation_from_case_includes_issue_titles() -> None:
    expectation = build_expectation_from_case(WEAK_REVIEW_CASE)

    assert expectation.case_id == WEAK_REVIEW_CASE.case_id
    assert "摘要没有明确点出研究问题" in expectation.expected_issue_titles


def test_build_expectation_from_case_supports_variant_specific_overrides() -> None:
    case = ReviewCaseSpec(
        case_id="variant_override_case",
        tags=("evaluation_fixture",),
        title="测试标题",
        abstract="测试摘要",
        sections=(SectionSpec(heading="1 绪论", paragraphs=("测试段落",)),),
        references=(),
        expected_dimensions=(),
        expected_high_severity_dimensions=(),
        expected_issue_titles=("规则版问题",),
        benchmark_expectation_overrides=(
            BenchmarkExpectationOverride(
                variant_id="model_only",
                expected_high_severity_dimensions=(),
                expected_issue_titles=("模型版问题",),
            ),
        ),
    )

    rule_expectation = build_expectation_from_case(case, variant_id="rule")
    model_expectation = build_expectation_from_case(case, variant_id="model_only")

    assert rule_expectation.expected_issue_titles == ["规则版问题"]
    assert model_expectation.expected_issue_titles == ["模型版问题"]


def test_case_has_expectation_override_detects_model_variant_seed_cases() -> None:
    assert case_has_expectation_override(WEAK_REVIEW_CASE, variant_id="model_with_fallback") is True
    assert case_has_expectation_override(TEMPLATE_VARIATION_CASE, variant_id="model_with_fallback") is True
    assert (
        case_has_expectation_override(
            ABSTRACT_RUNNING_HEADER_VARIATION_CASE,
            variant_id="model_with_fallback",
        )
        is True
    )
    assert case_has_expectation_override(APPENDIX_VARIATION_CASE, variant_id="model_with_fallback") is True
    assert (
        case_has_expectation_override(
            DOCX_ENDNOTE_OBJECT_VARIATION_CASE,
            variant_id="model_with_fallback",
        )
        is True
    )
    assert case_has_expectation_override(WEAK_REVIEW_CASE, variant_id="rule") is False
    assert case_has_expectation_override(TOPIC_PRECISION_CASE, variant_id="model_only") is True
    assert case_has_expectation_override(LOGIC_PRECISION_CASE, variant_id="model_only") is True
    assert case_has_expectation_override(LITERATURE_PRECISION_CASE, variant_id="model_only") is True
    assert case_has_expectation_override(NOVELTY_PRECISION_CASE, variant_id="model_only") is True
    assert case_has_expectation_override(WRITING_PRECISION_CASE, variant_id="model_only") is True


def test_all_evaluation_fixture_cases_have_model_with_fallback_override() -> None:
    cases = load_benchmark_cases(tag="evaluation_fixture")

    assert all(
        case_has_expectation_override(case, variant_id="model_with_fallback")
        for case in cases
    )


def test_load_benchmark_cases_supports_model_semantic_fixture_tag() -> None:
    cases = load_benchmark_cases(tag="model_semantic_fixture")

    assert [case.case_id for case in cases] == [
        "topic_precision_case",
        "logic_precision_case",
        "literature_precision_case",
        "novelty_precision_case",
        "writing_precision_case",
    ]


def test_load_benchmark_cases_filters_by_tag() -> None:
    cases = load_benchmark_cases(tag="evaluation_fixture")

    case_ids = {case.case_id for case in cases}
    assert "abstract_running_header_variation_case" in case_ids
    assert "bilingual_abstract_case" in case_ids
    assert "annotation_block_variation_case" in case_ids
    assert "back_matter_variation_case" in case_ids
    assert "caption_variation_case" in case_ids
    assert "footer_footnote_noise_variation_case" in case_ids
    assert "equation_caption_variation_case" in case_ids
    assert "footnote_body_variation_case" in case_ids
    assert "docx_footnote_object_variation_case" in case_ids
    assert "docx_endnote_object_variation_case" in case_ids
    assert "mixed_note_object_variation_case" in case_ids
    assert "multiline_note_object_variation_case" in case_ids
    assert "table_adjacent_note_object_variation_case" in case_ids
    assert "running_header_footer_metadata_case" in case_ids
    assert "running_english_header_footer_case" in case_ids
    assert "repeated_section_header_noise_case" in case_ids
    assert "repeated_parent_section_header_noise_case" in case_ids
    assert "repeated_subsection_header_noise_case" in case_ids
    assert "abbreviated_section_header_noise_case" in case_ids
    assert "unnumbered_abbreviated_section_header_noise_case" in case_ids
    assert "complex_contents_variation_case" in case_ids
    assert "contents_header_footer_variation_case" in case_ids
    assert "contents_field_code_variation_case" in case_ids
    assert "cover_page_table_variation_case" in case_ids
    assert "declaration_variation_case" in case_ids
    assert "post_reference_bio_variation_case" in case_ids
    assert "front_matter_combo_variation_case" in case_ids
    assert "front_matter_multiline_variation_case" in case_ids
    assert "front_matter_spacing_variation_case" in case_ids
    assert "front_matter_table_variation_case" in case_ids
    assert "docx_table_front_matter_case" in case_ids
    assert "complex_table_front_matter_case" in case_ids
    assert "appendix_contents_variation_case" in case_ids
    assert "appendix_figure_list_variation_case" in case_ids
    assert "keyword_variation_case" in case_ids
    assert "metadata_block_variation_case" in case_ids
    assert "author_info_variation_case" in case_ids
    assert "appendix_variation_case" in case_ids
    assert "english_appendix_variation_case" in case_ids
    assert "department_info_variation_case" in case_ids
    assert "strong_review_case" in case_ids
    assert "weak_review_case" in case_ids
    assert "boundary_review_case" in case_ids


def test_render_benchmark_markdown_outputs_readable_summary() -> None:
    markdown = render_benchmark_markdown(
        BenchmarkSummary(
            total_cases=1,
            fully_passed_cases=1,
            llm_request_attempts=2,
            llm_retry_count=1,
            llm_error_count=1,
            llm_error_categories={"provider_network": 1},
            llm_usage_observation_count=1,
            llm_prompt_tokens=1000,
            llm_completion_tokens=500,
            llm_total_tokens=1500,
            llm_input_cost_estimate_usd=0.002,
            llm_output_cost_estimate_usd=0.003,
            llm_total_cost_estimate_usd=0.005,
            high_severity_dimension_recall=1.0,
            priority_first_dimension_accuracy=1.0,
            debate_dimension_recall=1.0,
            issue_title_recall=1.0,
            issue_title_false_positive_rate=0.0,
            case_results=[],
        )
    )

    assert "# PaperMentor OS Benchmark" in markdown
    assert "High severity dimension recall: 1.00" in markdown
    assert "LLM error categories: provider_network=1" in markdown
    assert "LLM total cost estimate usd: 0.005000" in markdown
