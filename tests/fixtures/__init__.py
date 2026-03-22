"""Test fixtures and helpers for PaperMentor OS."""

from tests.fixtures.review_cases import (
    BOUNDARY_REVIEW_CASE,
    COVER_PAGE_VARIATION_CASE,
    CONTENTS_VARIATION_CASE,
    DEBATE_CANDIDATE_CASE,
    LITERATURE_PRECISION_CASE,
    LOGIC_PRECISION_CASE,
    MINIMAL_REVIEW_CASE,
    NOVELTY_PRECISION_CASE,
    REVIEW_CASE_CATALOG,
    STRONG_REVIEW_CASE,
    TEMPLATE_VARIATION_CASE,
    TOPIC_PRECISION_CASE,
    ReviewCaseSpec,
    SectionSpec,
    WEAK_REVIEW_CASE,
    WRITING_PRECISION_CASE,
    get_review_cases_by_tag,
)
from tests.fixtures.sample_docx import build_docx_from_case, build_minimal_review_docx

__all__ = [
    "BOUNDARY_REVIEW_CASE",
    "COVER_PAGE_VARIATION_CASE",
    "CONTENTS_VARIATION_CASE",
    "DEBATE_CANDIDATE_CASE",
    "LITERATURE_PRECISION_CASE",
    "LOGIC_PRECISION_CASE",
    "MINIMAL_REVIEW_CASE",
    "NOVELTY_PRECISION_CASE",
    "REVIEW_CASE_CATALOG",
    "STRONG_REVIEW_CASE",
    "TEMPLATE_VARIATION_CASE",
    "TOPIC_PRECISION_CASE",
    "ReviewCaseSpec",
    "SectionSpec",
    "WEAK_REVIEW_CASE",
    "WRITING_PRECISION_CASE",
    "build_docx_from_case",
    "build_minimal_review_docx",
    "get_review_cases_by_tag",
]
