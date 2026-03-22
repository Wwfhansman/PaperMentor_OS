from pathlib import Path

from docx import Document

from papermentor_os.parsers.docx_parser import DocxPaperParser
from papermentor_os.schemas.types import Discipline, PaperStage
from tests.fixtures.review_cases import CONTENTS_VARIATION_CASE, COVER_PAGE_VARIATION_CASE, TEMPLATE_VARIATION_CASE
from tests.fixtures.sample_docx import build_docx_from_case


def test_docx_parser_extracts_title_abstract_sections_and_references(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.docx"
    document = Document()
    document.add_paragraph("基于知识图谱的论文评审辅助系统设计")
    document.add_paragraph("摘要", style="Heading 1")
    document.add_paragraph("本文针对本科毕业论文初审反馈滞后的问题，提出一套结构化评审系统。")
    document.add_paragraph("1 绪论", style="Heading 1")
    document.add_paragraph("随着毕业论文指导工作量上升，早期诊断需求越来越突出。")
    document.add_paragraph("2 系统设计", style="Heading 1")
    document.add_paragraph("本文设计了多智能体评审流程，并通过证据账本约束结论。")
    document.add_paragraph("参考文献", style="Heading 1")
    document.add_paragraph("[1] Author. Example Paper. 2024.")
    document.save(file_path)

    parser = DocxPaperParser()
    paper = parser.parse_file(
        file_path,
        stage=PaperStage.DRAFT,
        discipline=Discipline.COMPUTER_SCIENCE,
    )

    assert paper.title == "基于知识图谱的论文评审辅助系统设计"
    assert "结构化评审系统" in paper.abstract
    assert len(paper.sections) == 2
    assert paper.sections[0].heading == "1 绪论"
    assert paper.sections[0].paragraphs[0].anchor_id == "sec-001-p-001"
    assert len(paper.references) == 1


def test_docx_parser_handles_spaced_abstract_and_reference_titles(tmp_path: Path) -> None:
    file_path = tmp_path / "template_variation.docx"
    build_docx_from_case(file_path, TEMPLATE_VARIATION_CASE)

    parser = DocxPaperParser()
    paper = parser.parse_file(
        file_path,
        stage=PaperStage.DRAFT,
        discipline=Discipline.COMPUTER_SCIENCE,
    )

    assert "模板差异适配问题" in paper.abstract
    assert paper.sections[0].heading == "第一章 绪论"
    assert len(paper.references) == 6


def test_docx_parser_handles_cover_page_content_before_title(tmp_path: Path) -> None:
    file_path = tmp_path / "cover_page_variation.docx"
    build_docx_from_case(file_path, COVER_PAGE_VARIATION_CASE)

    parser = DocxPaperParser()
    paper = parser.parse_file(
        file_path,
        stage=PaperStage.DRAFT,
        discipline=Discipline.COMPUTER_SCIENCE,
    )

    assert paper.title == COVER_PAGE_VARIATION_CASE.title
    assert "封面与标题布局方式" in paper.abstract
    assert paper.sections[0].heading == "1 绪论"


def test_docx_parser_ignores_table_of_contents_entries_between_abstract_and_body(tmp_path: Path) -> None:
    file_path = tmp_path / "contents_variation.docx"
    build_docx_from_case(file_path, CONTENTS_VARIATION_CASE)

    parser = DocxPaperParser()
    paper = parser.parse_file(
        file_path,
        stage=PaperStage.DRAFT,
        discipline=Discipline.COMPUTER_SCIENCE,
    )

    headings = [section.heading for section in paper.sections]

    assert "目录" not in headings
    assert headings[0] == "第一章 绪论"
    assert len(paper.sections) == 5
