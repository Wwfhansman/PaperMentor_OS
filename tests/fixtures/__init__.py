"""Test fixtures and helpers for PaperMentor OS."""

from tests.fixtures.review_cases import (
    DEBATE_CANDIDATE_CASE,
    MINIMAL_REVIEW_CASE,
    ReviewCaseSpec,
    SectionSpec,
)
from tests.fixtures.sample_docx import build_docx_from_case, build_minimal_review_docx

__all__ = [
    "DEBATE_CANDIDATE_CASE",
    "MINIMAL_REVIEW_CASE",
    "ReviewCaseSpec",
    "SectionSpec",
    "build_docx_from_case",
    "build_minimal_review_docx",
]
