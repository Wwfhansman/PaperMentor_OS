from papermentor_os.evals import build_expectation_from_case, load_benchmark_cases, render_benchmark_markdown
from papermentor_os.evals.models import BenchmarkSummary
from tests.fixtures.review_cases import WEAK_REVIEW_CASE


def test_build_expectation_from_case_includes_issue_titles() -> None:
    expectation = build_expectation_from_case(WEAK_REVIEW_CASE)

    assert expectation.case_id == WEAK_REVIEW_CASE.case_id
    assert "摘要没有明确点出研究问题" in expectation.expected_issue_titles


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
