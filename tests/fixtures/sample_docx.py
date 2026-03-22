from __future__ import annotations

from pathlib import Path

from docx import Document
from tests.fixtures.review_cases import MINIMAL_REVIEW_CASE, ReviewCaseSpec


def build_docx_from_case(file_path: Path, case: ReviewCaseSpec) -> Path:
    document = Document()
    for front_matter_paragraph in case.front_matter:
        document.add_paragraph(front_matter_paragraph)
    if case.title_style is not None:
        document.add_paragraph(case.title, style=case.title_style)
    else:
        document.add_paragraph(case.title)
    document.add_paragraph(case.abstract_heading, style=case.heading_style)
    document.add_paragraph(case.abstract)
    for front_matter_paragraph in case.post_abstract_front_matter:
        document.add_paragraph(front_matter_paragraph)
    for section in case.sections:
        document.add_paragraph(section.heading, style=case.heading_style)
        for paragraph in section.paragraphs:
            document.add_paragraph(paragraph)
    if case.references:
        document.add_paragraph(case.reference_heading, style=case.heading_style)
        for reference in case.references:
            document.add_paragraph(reference)
    document.save(file_path)
    return file_path


def build_minimal_review_docx(file_path: Path) -> Path:
    return build_docx_from_case(file_path, MINIMAL_REVIEW_CASE)
