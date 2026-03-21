from pathlib import Path

from fastapi.testclient import TestClient

from papermentor_os.api.app import create_app
from papermentor_os.schemas.types import Dimension
from tests.fixtures.review_cases import DEBATE_CANDIDATE_CASE, REVIEW_CASE_CATALOG
from tests.fixtures.sample_docx import build_docx_from_case


def test_debug_review_endpoint_returns_trace(tmp_path: Path) -> None:
    file_path = tmp_path / "debate_case.docx"
    build_docx_from_case(file_path, DEBATE_CANDIDATE_CASE)
    client = TestClient(create_app())

    response = client.post(
        "/review/docx/debug",
        json={"file_path": str(file_path)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "report" in payload
    assert "trace" in payload
    assert payload["trace"]["debate_candidates"]
    assert payload["trace"]["debate_resolutions"]
    dimensions = {item["dimension"] for item in payload["report"]["dimension_reports"]}
    assert Dimension.NOVELTY_DEPTH.value in dimensions


def test_review_case_catalog_contains_baseline_and_debate_cases() -> None:
    case_ids = {case.case_id for case in REVIEW_CASE_CATALOG}
    tags = {tag for case in REVIEW_CASE_CATALOG for tag in case.tags}

    assert "minimal_review_case" in case_ids
    assert "debate_candidate_case" in case_ids
    assert "baseline" in tags
    assert "debate_candidate" in tags
