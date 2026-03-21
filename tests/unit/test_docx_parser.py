from pathlib import Path

from docx import Document

from papermentor_os.parsers.docx_parser import DocxPaperParser
from papermentor_os.schemas.types import Discipline, PaperStage


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

