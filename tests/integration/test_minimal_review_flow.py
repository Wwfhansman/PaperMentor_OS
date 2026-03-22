from pathlib import Path

from papermentor_os.orchestrator.chief_reviewer import ChiefReviewer
from papermentor_os.schemas.types import Dimension, Severity
from tests.fixtures.review_cases import (
    ABBREVIATED_SECTION_HEADER_NOISE_CASE,
    ABSTRACT_RUNNING_HEADER_VARIATION_CASE,
    APPENDIX_VARIATION_CASE,
    APPENDIX_CONTENTS_VARIATION_CASE,
    APPENDIX_FIGURE_LIST_VARIATION_CASE,
    ANNOTATION_BLOCK_VARIATION_CASE,
    AUTHOR_INFO_VARIATION_CASE,
    BACK_MATTER_VARIATION_CASE,
    BILINGUAL_ABSTRACT_CASE,
    BOUNDARY_REVIEW_CASE,
    CAPTION_VARIATION_CASE,
    COMPLEX_TABLE_FRONT_MATTER_CASE,
    COMPLEX_CONTENTS_VARIATION_CASE,
    CONTENTS_HEADER_FOOTER_VARIATION_CASE,
    CONTENTS_FIELD_CODE_VARIATION_CASE,
    CONTENTS_VARIATION_CASE,
    COVER_PAGE_VARIATION_CASE,
    COVER_PAGE_TABLE_VARIATION_CASE,
    DEBATE_CANDIDATE_CASE,
    DECLARATION_VARIATION_CASE,
    DEPARTMENT_INFO_VARIATION_CASE,
    DOCX_ENDNOTE_OBJECT_VARIATION_CASE,
    DOCX_FOOTNOTE_OBJECT_VARIATION_CASE,
    DOCX_TABLE_FRONT_MATTER_CASE,
    EQUATION_CAPTION_VARIATION_CASE,
    ENGLISH_APPENDIX_VARIATION_CASE,
    FOOTER_FOOTNOTE_NOISE_VARIATION_CASE,
    FOOTNOTE_BODY_VARIATION_CASE,
    FRONT_MATTER_COMBO_VARIATION_CASE,
    FRONT_MATTER_MULTILINE_VARIATION_CASE,
    FRONT_MATTER_SPACING_VARIATION_CASE,
    FRONT_MATTER_TABLE_VARIATION_CASE,
    KEYWORD_VARIATION_CASE,
    LITERATURE_PRECISION_CASE,
    LOGIC_PRECISION_CASE,
    METADATA_BLOCK_VARIATION_CASE,
    MIXED_NOTE_OBJECT_VARIATION_CASE,
    MULTILINE_NOTE_OBJECT_VARIATION_CASE,
    NOVELTY_PRECISION_CASE,
    POST_REFERENCE_BIO_VARIATION_CASE,
    REPEATED_PARENT_SECTION_HEADER_NOISE_CASE,
    REPEATED_SECTION_HEADER_NOISE_CASE,
    REPEATED_SUBSECTION_HEADER_NOISE_CASE,
    RUNNING_ENGLISH_HEADER_FOOTER_CASE,
    RUNNING_HEADER_FOOTER_METADATA_CASE,
    STRONG_REVIEW_CASE,
    TABLE_ADJACENT_NOTE_OBJECT_VARIATION_CASE,
    TEMPLATE_VARIATION_CASE,
    TOPIC_PRECISION_CASE,
    UNNUMBERED_ABBREVIATED_SECTION_HEADER_NOISE_CASE,
    WEAK_REVIEW_CASE,
    WRITING_PRECISION_CASE,
)
from tests.fixtures.sample_docx import build_docx_from_case, build_minimal_review_docx


def test_minimal_review_flow_returns_topic_and_writing_reports(tmp_path: Path) -> None:
    file_path = tmp_path / "draft.docx"
    build_minimal_review_docx(file_path)

    reviewer = ChiefReviewer()
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert {item.dimension for item in report.dimension_reports} == {
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    }
    assert report.priority_actions
    assert "review mode" in report.safety_notice
    assert any(
        finding.source_skill_version == "logic-chain-rubric@0.1.0"
        for item in report.dimension_reports
        for finding in item.findings
    )
    assert any(
        item.dimension == Dimension.LITERATURE_SUPPORT
        for item in report.dimension_reports
    )
    assert any(
        item.dimension == Dimension.NOVELTY_DEPTH
        for item in report.dimension_reports
    )
    assert report.priority_actions[0].dimension != Dimension.WRITING_FORMAT


def test_chief_reviewer_collects_debate_candidates_for_ambiguous_case(tmp_path: Path) -> None:
    file_path = tmp_path / "debate_case.docx"
    build_docx_from_case(file_path, DEBATE_CANDIDATE_CASE)

    reviewer = ChiefReviewer()
    report = reviewer.review_docx(Path(file_path))

    debate_dimensions = {case.dimension for case in reviewer.last_debate_candidates}
    assert Dimension.LOGIC_CHAIN in debate_dimensions or Dimension.NOVELTY_DEPTH in debate_dimensions
    assert reviewer.last_debate_resolutions
    assert any(item.debate_used for item in report.dimension_reports if item.dimension in debate_dimensions)


def test_strong_review_case_stays_out_of_high_severity_band(tmp_path: Path) -> None:
    file_path = tmp_path / "strong_case.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)

    reviewer = ChiefReviewer()
    report = reviewer.review_docx(Path(file_path))

    high_severity_dimensions = {
        finding.dimension
        for dimension_report in report.dimension_reports
        for finding in dimension_report.findings
        if finding.severity == Severity.HIGH
    }

    assert not high_severity_dimensions
    assert not reviewer.last_debate_candidates
    assert report.priority_actions == []


def test_weak_review_case_exposes_research_risks_before_writing_issues(tmp_path: Path) -> None:
    file_path = tmp_path / "weak_case.docx"
    build_docx_from_case(file_path, WEAK_REVIEW_CASE)

    reviewer = ChiefReviewer()
    report = reviewer.review_docx(Path(file_path))

    high_severity_dimensions = {
        finding.dimension
        for dimension_report in report.dimension_reports
        for finding in dimension_report.findings
        if finding.severity == Severity.HIGH
    }

    assert set(WEAK_REVIEW_CASE.expected_high_severity_dimensions).issubset(high_severity_dimensions)
    assert report.priority_actions
    assert report.priority_actions[0].dimension == WEAK_REVIEW_CASE.expected_priority_first_dimension
    assert all(action.dimension != Dimension.WRITING_FORMAT for action in report.priority_actions)


def test_boundary_review_case_keeps_selective_debate_on_subjective_dimensions(tmp_path: Path) -> None:
    file_path = tmp_path / "boundary_case.docx"
    build_docx_from_case(file_path, BOUNDARY_REVIEW_CASE)

    reviewer = ChiefReviewer()
    report = reviewer.review_docx(Path(file_path))

    debate_dimensions = {case.dimension for case in reviewer.last_debate_candidates}

    assert set(BOUNDARY_REVIEW_CASE.expected_debate_dimensions).issubset(debate_dimensions)
    assert all(item.dimension in debate_dimensions for item in report.dimension_reports if item.debate_used)
    assert reviewer.last_worker_skill_traces
    assert reviewer.last_worker_execution_traces
    assert reviewer.last_orchestration_trace is not None
    assert reviewer.last_orchestration_trace.debate_candidate_dimensions
    assert reviewer.last_orchestration_trace.debated_dimensions


def test_topic_precision_case_does_not_flag_specific_system_title_as_generic(tmp_path: Path) -> None:
    file_path = tmp_path / "topic_precision_case.docx"
    build_docx_from_case(file_path, TOPIC_PRECISION_CASE)

    reviewer = ChiefReviewer()
    report = reviewer.review_docx(Path(file_path))

    topic_report = next(item for item in report.dimension_reports if item.dimension == Dimension.TOPIC_SCOPE)
    issue_titles = {finding.issue_title for finding in topic_report.findings}

    assert "标题偏泛，范围边界不够具体" not in issue_titles


def test_logic_precision_case_accepts_discussion_and_outlook_as_closing_section(tmp_path: Path) -> None:
    file_path = tmp_path / "logic_precision_case.docx"
    build_docx_from_case(file_path, LOGIC_PRECISION_CASE)

    reviewer = ChiefReviewer()
    report = reviewer.review_docx(Path(file_path))

    logic_report = next(item for item in report.dimension_reports if item.dimension == Dimension.LOGIC_CHAIN)
    issue_titles = {finding.issue_title for finding in logic_report.findings}

    assert "缺少显式结论章节，论证收束不足" not in issue_titles


def test_literature_precision_case_accepts_existing_method_comparison_section(tmp_path: Path) -> None:
    file_path = tmp_path / "literature_precision_case.docx"
    build_docx_from_case(file_path, LITERATURE_PRECISION_CASE)

    reviewer = ChiefReviewer()
    report = reviewer.review_docx(Path(file_path))

    literature_report = next(item for item in report.dimension_reports if item.dimension == Dimension.LITERATURE_SUPPORT)
    issue_titles = {finding.issue_title for finding in literature_report.findings}

    assert "缺少显式相关工作或文献综述部分" not in issue_titles


def test_novelty_precision_case_accepts_comparative_contribution_without_literal_novelty_wording(tmp_path: Path) -> None:
    file_path = tmp_path / "novelty_precision_case.docx"
    build_docx_from_case(file_path, NOVELTY_PRECISION_CASE)

    reviewer = ChiefReviewer()
    report = reviewer.review_docx(Path(file_path))

    novelty_report = next(item for item in report.dimension_reports if item.dimension == Dimension.NOVELTY_DEPTH)
    issue_titles = {finding.issue_title for finding in novelty_report.findings}

    assert "论文没有明确交代创新点或研究贡献" not in issue_titles


def test_writing_precision_case_accepts_compact_but_complete_abstract(tmp_path: Path) -> None:
    file_path = tmp_path / "writing_precision_case.docx"
    build_docx_from_case(file_path, WRITING_PRECISION_CASE)

    reviewer = ChiefReviewer()
    report = reviewer.review_docx(Path(file_path))

    writing_report = next(item for item in report.dimension_reports if item.dimension == Dimension.WRITING_FORMAT)
    issue_titles = {finding.issue_title for finding in writing_report.findings}

    assert "摘要信息量不足" not in issue_titles


def test_template_variation_case_handles_spaced_headings_and_chapter_naming(tmp_path: Path) -> None:
    file_path = tmp_path / "template_variation_case.docx"
    build_docx_from_case(file_path, TEMPLATE_VARIATION_CASE)

    reviewer = ChiefReviewer()
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert report.dimension_reports[0].findings or report.dimension_reports[0].summary


def test_cover_page_variation_case_handles_front_matter_before_title(tmp_path: Path) -> None:
    file_path = tmp_path / "cover_page_variation_case.docx"
    build_docx_from_case(file_path, COVER_PAGE_VARIATION_CASE)

    reviewer = ChiefReviewer()
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert "某某大学本科毕业论文" not in report.overall_summary


def test_cover_page_table_variation_case_handles_table_front_matter_before_title(tmp_path: Path) -> None:
    file_path = tmp_path / "cover_page_table_variation_case.docx"
    build_docx_from_case(file_path, COVER_PAGE_TABLE_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert paper.title == COVER_PAGE_TABLE_VARIATION_CASE.title
    assert "学号 2020123456" not in report.overall_summary
    assert paper.sections[0].heading == "1 绪论"


def test_back_matter_variation_case_skips_acknowledgements_before_references(tmp_path: Path) -> None:
    file_path = tmp_path / "back_matter_variation_case.docx"
    build_docx_from_case(file_path, BACK_MATTER_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "致谢" not in {section.heading for section in paper.sections}
    assert "攻读学位期间取得的成果" not in {section.heading for section in paper.sections}
    assert "Acknowledgements" not in {section.heading for section in paper.sections}
    assert "致谢内容不应进入主正文五维评审结论。" not in section_text


def test_caption_variation_case_keeps_captions_out_of_section_headings(tmp_path: Path) -> None:
    file_path = tmp_path / "caption_variation_case.docx"
    build_docx_from_case(file_path, CAPTION_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "图 1-1 论文评审系统总体架构图" not in {section.heading for section in paper.sections}
    assert "Figure 2-1 Baseline parsing workflow" not in {section.heading for section in paper.sections}
    assert "图 1-1 论文评审系统总体架构图" in section_text
    assert "Table 2-1 Error categories and examples" in section_text


def test_equation_caption_variation_case_keeps_formula_captions_out_of_section_headings(tmp_path: Path) -> None:
    file_path = tmp_path / "equation_caption_variation_case.docx"
    build_docx_from_case(file_path, EQUATION_CAPTION_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "式 1-1 论文评审损失函数定义" not in {section.heading for section in paper.sections}
    assert "Equation 2-1 Review score aggregation" not in {section.heading for section in paper.sections}
    assert "式 1-1 论文评审损失函数定义" in section_text
    assert "Equation (2-2) Evidence consistency score" in section_text


def test_annotation_block_variation_case_keeps_note_blocks_out_of_section_headings(tmp_path: Path) -> None:
    file_path = tmp_path / "annotation_block_variation_case.docx"
    build_docx_from_case(file_path, ANNOTATION_BLOCK_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "注 1-1 图片仅用于展示系统流程" not in {section.heading for section in paper.sections}
    assert "Note 2-1 Scores are normalized" not in {section.heading for section in paper.sections}
    assert "注 1-1 图片仅用于展示系统流程" in section_text
    assert "Remark 2-2 Evidence anchors are sampled" in section_text


def test_footer_footnote_noise_variation_case_filters_page_number_and_marker_noise(tmp_path: Path) -> None:
    file_path = tmp_path / "footer_footnote_noise_variation_case.docx"
    build_docx_from_case(file_path, FOOTER_FOOTNOTE_NOISE_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "- 1 -" not in {section.heading for section in paper.sections}
    assert "ii" not in {section.heading for section in paper.sections}
    assert "- 1 -" not in section_text
    assert "[1]" not in section_text
    assert "①" not in section_text


def test_running_header_footer_metadata_case_filters_repeated_title_and_metadata_rows(tmp_path: Path) -> None:
    file_path = tmp_path / "running_header_footer_metadata_case.docx"
    build_docx_from_case(file_path, RUNNING_HEADER_FOOTER_METADATA_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "某某大学本科毕业论文" not in {section.heading for section in paper.sections}
    assert RUNNING_HEADER_FOOTER_METADATA_CASE.title not in section_text
    assert "学号 2020123456" not in section_text
    assert "专业 软件工程" not in section_text
    assert "指导教师 张老师" not in section_text


def test_running_english_header_footer_case_filters_english_header_and_metadata_rows(tmp_path: Path) -> None:
    file_path = tmp_path / "running_english_header_footer_case.docx"
    build_docx_from_case(file_path, RUNNING_ENGLISH_HEADER_FOOTER_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "Undergraduate Thesis" not in section_text
    assert RUNNING_ENGLISH_HEADER_FOOTER_CASE.title not in section_text
    assert "Student ID 2020123456" not in section_text
    assert "Major Software Engineering" not in section_text
    assert "Advisor Prof. Zhang" not in section_text


def test_abstract_running_header_variation_case_ignores_late_abstract_headers(tmp_path: Path) -> None:
    file_path = tmp_path / "abstract_running_header_variation_case.docx"
    build_docx_from_case(file_path, ABSTRACT_RUNNING_HEADER_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "Abstract" not in {section.heading for section in paper.sections}
    assert "Abstract" not in section_text
    assert any("英文摘要页眉时仍能稳定保留后续论证内容" in text for text in section_text)
    assert "英文摘要页眉时仍能稳定保留后续论证内容" not in paper.abstract


def test_repeated_section_header_noise_case_ignores_running_section_header_duplicates(tmp_path: Path) -> None:
    file_path = tmp_path / "repeated_section_header_noise_case.docx"
    build_docx_from_case(file_path, REPEATED_SECTION_HEADER_NOISE_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert [section.heading for section in paper.sections].count("1 绪论") == 1
    assert [section.heading for section in paper.sections].count("2 已有方法比较") == 1
    assert [section.heading for section in paper.sections].count("3 方法设计") == 1
    assert "1 绪论" not in section_text
    assert "2 已有方法比较" not in section_text
    assert "3 方法设计" not in section_text


def test_footnote_body_variation_case_filters_running_footnote_body_blocks(tmp_path: Path) -> None:
    file_path = tmp_path / "footnote_body_variation_case.docx"
    build_docx_from_case(file_path, FOOTNOTE_BODY_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "[1] 注：实验平台为课程内部服务器，仅用于教学验证。" not in section_text
    assert "① Remark: baseline scores come from the prior semester report." not in section_text
    assert any("遇到脚注正文块时仍能稳定保留后续论证内容" in text for text in section_text)


def test_docx_footnote_object_variation_case_filters_text_duplicated_from_footnotes_part(tmp_path: Path) -> None:
    file_path = tmp_path / "docx_footnote_object_variation_case.docx"
    build_docx_from_case(file_path, DOCX_FOOTNOTE_OBJECT_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "注：实验平台为课程内部服务器，仅用于教学验证。" not in section_text
    assert any("存在真实 docx 脚注对象时仍能稳定保留后续论证内容" in text for text in section_text)


def test_docx_endnote_object_variation_case_filters_text_duplicated_from_endnotes_part(tmp_path: Path) -> None:
    file_path = tmp_path / "docx_endnote_object_variation_case.docx"
    build_docx_from_case(file_path, DOCX_ENDNOTE_OBJECT_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "说明：附加实验参数记录在课程归档仓库中。" not in section_text
    assert any("存在真实 docx 尾注对象时仍能稳定保留后续论证内容" in text for text in section_text)


def test_mixed_note_object_variation_case_filters_note_duplicates_but_keeps_similar_body_sentence(tmp_path: Path) -> None:
    file_path = tmp_path / "mixed_note_object_variation_case.docx"
    build_docx_from_case(file_path, MIXED_NOTE_OBJECT_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "说明：课程内网服务器用于复现实验。" not in section_text
    assert "说明：课程镜像服务器用于补充归档。" not in section_text
    assert "说明：课程内网服务器与课程镜像服务器共同支撑实验复现。" in section_text


def test_multiline_note_object_variation_case_filters_multiline_duplicates_but_keeps_summary_sentence(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "multiline_note_object_variation_case.docx"
    build_docx_from_case(file_path, MULTILINE_NOTE_OBJECT_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "注：实验平台部署在课程内网服务器。" not in section_text
    assert "注：相关配置仅用于教学验证。" not in section_text
    assert "说明：补充日志保存在课程归档仓库。" not in section_text
    assert "说明：归档信息用于结果复核。" not in section_text
    assert "实验平台、相关配置和归档信息共同支撑教学验证与结果复核。" in section_text


def test_table_adjacent_note_object_variation_case_filters_table_duplicates_but_keeps_summary_sentence(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "table_adjacent_note_object_variation_case.docx"
    build_docx_from_case(file_path, TABLE_ADJACENT_NOTE_OBJECT_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "注：课程内网服务器用于复现实验。" not in section_text
    assert "说明：课程镜像服务器用于补充归档。" not in section_text
    assert "课程内网服务器与课程镜像服务器共同支撑实验复现与结果归档。" in section_text


def test_repeated_parent_section_header_noise_case_ignores_parent_header_duplicates_inside_subsections(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "repeated_parent_section_header_noise_case.docx"
    build_docx_from_case(file_path, REPEATED_PARENT_SECTION_HEADER_NOISE_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert [section.heading for section in paper.sections].count("2 相关工作与方法设计") == 1
    assert [section.heading for section in paper.sections].count("2.1 数据集构建") == 1
    assert "2 相关工作与方法设计" not in section_text
    assert any("子章节内部再次遇到上级章节标题时仍能稳定保留后续论证内容" in text for text in section_text)


def test_repeated_subsection_header_noise_case_ignores_subsection_duplicates_inside_deeper_subsections(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "repeated_subsection_header_noise_case.docx"
    build_docx_from_case(file_path, REPEATED_SUBSECTION_HEADER_NOISE_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert [section.heading for section in paper.sections].count("2.1 数据集构建") == 1
    assert [section.heading for section in paper.sections].count("2.1.1 标注原则") == 1
    assert "2.1 数据集构建" not in section_text
    assert any("更细一级小节内部再次遇到子章节标题时仍能稳定保留后续论证内容" in text for text in section_text)


def test_abbreviated_section_header_noise_case_ignores_shortened_section_duplicates_inside_deeper_subsections(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "abbreviated_section_header_noise_case.docx"
    build_docx_from_case(file_path, ABBREVIATED_SECTION_HEADER_NOISE_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert [section.heading for section in paper.sections].count("2.1 数据集构建与标注策略") == 1
    assert [section.heading for section in paper.sections].count("2.1.1 标注原则") == 1
    assert "2.1 数据集构建" not in section_text
    assert any("再次遇到已出现章节标题的缩写时仍能稳定保留后续论证内容" in text for text in section_text)


def test_unnumbered_abbreviated_section_header_noise_case_ignores_shortened_header_without_number_inside_deeper_subsections(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "unnumbered_abbreviated_section_header_noise_case.docx"
    build_docx_from_case(file_path, UNNUMBERED_ABBREVIATED_SECTION_HEADER_NOISE_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert [section.heading for section in paper.sections].count("2.1 数据集构建与标注策略") == 1
    assert [section.heading for section in paper.sections].count("2.1.1 标注原则") == 1
    assert "数据集构建" not in section_text
    assert any("再次遇到已出现编号章节标题的无编号缩写时仍能稳定保留后续论证内容" in text for text in section_text)


def test_contents_variation_case_ignores_table_of_contents_noise(tmp_path: Path) -> None:
    file_path = tmp_path / "contents_variation_case.docx"
    build_docx_from_case(file_path, CONTENTS_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert "目录" not in {section.heading for section in paper.sections}


def test_bilingual_abstract_case_handles_second_abstract_block_without_polluting_body(tmp_path: Path) -> None:
    file_path = tmp_path / "bilingual_abstract_case.docx"
    build_docx_from_case(file_path, BILINGUAL_ABSTRACT_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert "This paper studies bilingual abstract layouts" in paper.abstract
    assert "Abstract" not in {section.heading for section in paper.sections}


def test_declaration_variation_case_skips_statement_pages_before_first_chapter(tmp_path: Path) -> None:
    file_path = tmp_path / "declaration_variation_case.docx"
    build_docx_from_case(file_path, DECLARATION_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert "独创性声明" not in {section.heading for section in paper.sections}
    assert "学术诚信承诺书" not in {section.heading for section in paper.sections}


def test_complex_contents_variation_case_skips_nested_contents_entries(tmp_path: Path) -> None:
    file_path = tmp_path / "complex_contents_variation_case.docx"
    build_docx_from_case(file_path, COMPLEX_CONTENTS_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert "Contents" not in {section.heading for section in paper.sections}
    assert "1.1Research Background\t2" not in {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }


def test_contents_header_footer_variation_case_skips_contents_header_footer_noise(tmp_path: Path) -> None:
    file_path = tmp_path / "contents_header_footer_variation_case.docx"
    build_docx_from_case(file_path, CONTENTS_HEADER_FOOTER_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "某某大学本科毕业论文" not in {section.heading for section in paper.sections}
    assert "本科毕业论文" not in {section.heading for section in paper.sections}
    assert "- 1 -" not in {section.heading for section in paper.sections}
    assert "某某大学本科毕业论文" not in section_text


def test_contents_field_code_variation_case_skips_toc_field_code_noise(tmp_path: Path) -> None:
    file_path = tmp_path / "contents_field_code_variation_case.docx"
    build_docx_from_case(file_path, CONTENTS_FIELD_CODE_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "PAGEREF _Toc482011111 \\h" not in {section.heading for section in paper.sections}
    assert 'HYPERLINK \\l "_Toc482011112"' not in {section.heading for section in paper.sections}
    assert "TOC \\o \"1-3\" \\h \\z \\u" not in section_text


def test_keyword_variation_case_keeps_keyword_blocks_before_first_chapter(tmp_path: Path) -> None:
    file_path = tmp_path / "keyword_variation_case.docx"
    build_docx_from_case(file_path, KEYWORD_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert "关键词：本科论文初审" in paper.abstract
    assert "Key words: thesis review" in paper.abstract
    assert "关键词：本科论文初审；多智能体评审；docx 解析；benchmark" not in {
        section.heading for section in paper.sections
    }


def test_metadata_block_variation_case_skips_metadata_lines_before_first_chapter(tmp_path: Path) -> None:
    file_path = tmp_path / "metadata_block_variation_case.docx"
    build_docx_from_case(file_path, METADATA_BLOCK_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert "关键词：本科论文初审" in paper.abstract
    assert "分类号：TP391.1" not in paper.abstract
    assert "学校代码：10487" not in paper.abstract
    assert "学号：2020123456" not in paper.abstract
    assert "UDC: 004.8" not in {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }


def test_author_info_variation_case_skips_author_lines_before_first_chapter(tmp_path: Path) -> None:
    file_path = tmp_path / "author_info_variation_case.docx"
    build_docx_from_case(file_path, AUTHOR_INFO_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert "关键词：本科论文初审" in paper.abstract
    assert "保密级别：公开" not in paper.abstract
    assert "作者姓名：张三" not in paper.abstract
    assert "指导教师：李老师" not in {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }


def test_appendix_variation_case_skips_appendix_content_from_main_body(tmp_path: Path) -> None:
    file_path = tmp_path / "appendix_variation_case.docx"
    build_docx_from_case(file_path, APPENDIX_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert "附录 A" not in {section.heading for section in paper.sections}
    assert "附录中的提示词和截图不应被纳入主正文的五维评审结论。" not in {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }


def test_english_appendix_variation_case_skips_english_appendix_content_from_main_body(tmp_path: Path) -> None:
    file_path = tmp_path / "english_appendix_variation_case.docx"
    build_docx_from_case(file_path, ENGLISH_APPENDIX_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert "Appendix A Prompt Templates" not in {section.heading for section in paper.sections}
    assert "Appendix B Supplementary Results" not in {section.heading for section in paper.sections}
    assert "Appendix prompt templates should not be included in the main five-dimension review body." not in {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }


def test_department_info_variation_case_skips_department_lines_before_first_chapter(tmp_path: Path) -> None:
    file_path = tmp_path / "department_info_variation_case.docx"
    build_docx_from_case(file_path, DEPARTMENT_INFO_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert "关键词：本科论文初审" in paper.abstract
    assert "学院：计算机科学与技术学院" not in paper.abstract
    assert "专业：软件工程" not in paper.abstract
    assert "班级：2020级1班" not in paper.abstract
    assert "作者单位：某某大学信息学院" not in {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }


def test_front_matter_combo_variation_case_handles_combined_front_matter_and_appendices(tmp_path: Path) -> None:
    file_path = tmp_path / "front_matter_combo_variation_case.docx"
    build_docx_from_case(file_path, FRONT_MATTER_COMBO_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "关键词：本科论文初审" in paper.abstract
    assert "导师组：智能系统导师组" not in paper.abstract
    assert "学位类型：工学学士" not in paper.abstract
    assert "Contents" not in {section.heading for section in paper.sections}
    assert "Appendix A Prompt Templates" not in {section.heading for section in paper.sections}
    assert "附录 B 补充图表" not in {section.heading for section in paper.sections}
    assert "图 B-1 复杂前置区模板示意图" not in section_text


def test_front_matter_spacing_variation_case_handles_space_separated_front_matter(tmp_path: Path) -> None:
    file_path = tmp_path / "front_matter_spacing_variation_case.docx"
    build_docx_from_case(file_path, FRONT_MATTER_SPACING_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert "关键词 本科论文初审" in paper.abstract
    assert "Key words thesis review" in paper.abstract
    assert "学校代码 10487" not in paper.abstract
    assert "导师组 智能系统导师组" not in paper.abstract
    assert "学位类型 工学学士" not in {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }


def test_front_matter_multiline_variation_case_handles_multiline_front_matter(tmp_path: Path) -> None:
    file_path = tmp_path / "front_matter_multiline_variation_case.docx"
    build_docx_from_case(file_path, FRONT_MATTER_MULTILINE_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert "本科论文初审；跨行前置区" in paper.abstract
    assert "thesis review; multiline metadata; parser stability" in paper.abstract
    assert "10487" not in {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }
    assert "智能系统导师组" not in {section.heading for section in paper.sections}


def test_appendix_contents_variation_case_skips_appendix_directory_page(tmp_path: Path) -> None:
    file_path = tmp_path / "appendix_contents_variation_case.docx"
    build_docx_from_case(file_path, APPENDIX_CONTENTS_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "附录目录" not in {section.heading for section in paper.sections}
    assert "附录 A 访谈提纲" not in {section.heading for section in paper.sections}
    assert "附录 B 问卷样例" not in {section.heading for section in paper.sections}
    assert "附录图目录....................................27" not in section_text


def test_front_matter_table_variation_case_handles_tabular_front_matter(tmp_path: Path) -> None:
    file_path = tmp_path / "front_matter_table_variation_case.docx"
    build_docx_from_case(file_path, FRONT_MATTER_TABLE_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert "关键词 本科论文初审" in paper.abstract
    assert "Key words thesis review" in paper.abstract
    assert "学校代码 10487" not in paper.abstract
    assert "导师组 智能系统导师组" not in {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }


def test_appendix_figure_list_variation_case_skips_appendix_figure_lists(tmp_path: Path) -> None:
    file_path = tmp_path / "appendix_figure_list_variation_case.docx"
    build_docx_from_case(file_path, APPENDIX_FIGURE_LIST_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "附录图目录" not in {section.heading for section in paper.sections}
    assert "List of Appendix Tables" not in {section.heading for section in paper.sections}
    assert "Appendix B Supplementary Questionnaire" not in {section.heading for section in paper.sections}
    assert "图 A-1 访谈流程图................................21" not in section_text


def test_docx_table_front_matter_case_extracts_table_front_matter_before_body(tmp_path: Path) -> None:
    file_path = tmp_path / "docx_table_front_matter_case.docx"
    build_docx_from_case(file_path, DOCX_TABLE_FRONT_MATTER_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert "关键词 本科论文初审" in paper.abstract
    assert "Key words thesis review" in paper.abstract
    assert "学校代码 10487" not in paper.abstract
    assert "导师组 智能系统导师组" not in {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }


def test_complex_table_front_matter_case_extracts_merged_and_nested_table_front_matter(tmp_path: Path) -> None:
    file_path = tmp_path / "complex_table_front_matter_case.docx"
    build_docx_from_case(file_path, COMPLEX_TABLE_FRONT_MATTER_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    section_text = {
        paragraph.text
        for section in paper.sections
        for paragraph in section.paragraphs
    }

    assert len(report.dimension_reports) == 5
    assert "关键词 本科论文初审" in paper.abstract
    assert "学校代码 学校代码 10487" not in paper.abstract
    assert "学校代码 10487" not in section_text
    assert "导师组 智能系统导师组 学位类型 工学学士 学位授予单位 某某大学" not in section_text
    assert paper.sections[0].heading == "第一章 绪论"


def test_post_reference_bio_variation_case_stops_references_before_author_pages(tmp_path: Path) -> None:
    file_path = tmp_path / "post_reference_bio_variation_case.docx"
    build_docx_from_case(file_path, POST_REFERENCE_BIO_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert len(paper.references) == 6
    assert all("作者简介" not in reference.raw_text for reference in paper.references)
    assert all("Author Biography" not in reference.raw_text for reference in paper.references)
