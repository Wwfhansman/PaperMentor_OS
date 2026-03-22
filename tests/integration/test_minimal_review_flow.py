from pathlib import Path

from papermentor_os.orchestrator.chief_reviewer import ChiefReviewer
from papermentor_os.schemas.types import Dimension, Severity
from tests.fixtures.review_cases import (
    BOUNDARY_REVIEW_CASE,
    CONTENTS_VARIATION_CASE,
    COVER_PAGE_VARIATION_CASE,
    DEBATE_CANDIDATE_CASE,
    LITERATURE_PRECISION_CASE,
    LOGIC_PRECISION_CASE,
    NOVELTY_PRECISION_CASE,
    STRONG_REVIEW_CASE,
    TEMPLATE_VARIATION_CASE,
    TOPIC_PRECISION_CASE,
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


def test_contents_variation_case_ignores_table_of_contents_noise(tmp_path: Path) -> None:
    file_path = tmp_path / "contents_variation_case.docx"
    build_docx_from_case(file_path, CONTENTS_VARIATION_CASE)

    reviewer = ChiefReviewer()
    paper = reviewer.parser.parse_file(file_path)
    report = reviewer.review_docx(Path(file_path))

    assert len(report.dimension_reports) == 5
    assert "目录" not in {section.heading for section in paper.sections}
