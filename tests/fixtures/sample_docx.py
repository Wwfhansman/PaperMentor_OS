from __future__ import annotations

from pathlib import Path

from docx import Document
from tests.fixtures.review_cases import MINIMAL_REVIEW_CASE, ReviewCaseSpec


def build_docx_from_case(file_path: Path, case: ReviewCaseSpec) -> Path:
    document = Document()
    document.add_paragraph(case.title)
    document.add_paragraph("摘要", style="Heading 1")
    document.add_paragraph(case.abstract)
    for section in case.sections:
        document.add_paragraph(section.heading, style="Heading 1")
        for paragraph in section.paragraphs:
            document.add_paragraph(paragraph)
    if case.references:
        document.add_paragraph("参考文献", style="Heading 1")
        for reference in case.references:
            document.add_paragraph(reference)
    document.save(file_path)
    return file_path


def build_minimal_review_docx(file_path: Path) -> Path:
    return build_docx_from_case(file_path, MINIMAL_REVIEW_CASE)
