from pathlib import Path

from papermentor_os.orchestrator.chief_reviewer import ChiefReviewer
from papermentor_os.schemas.types import Dimension
from tests.fixtures.review_cases import DEBATE_CANDIDATE_CASE
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
