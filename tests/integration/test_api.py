import importlib
from pathlib import Path

from fastapi.testclient import TestClient

from papermentor_os.api.app import create_app
from papermentor_os.schemas.types import Dimension
from tests.fixtures.review_cases import (
    BOUNDARY_REVIEW_CASE,
    DEBATE_CANDIDATE_CASE,
    REVIEW_CASE_CATALOG,
    STRONG_REVIEW_CASE,
    WEAK_REVIEW_CASE,
    get_review_cases_by_tag,
)
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
    assert payload["trace"]["worker_skills"]
    assert payload["trace"]["worker_runs"]
    assert payload["trace"]["orchestration"]["worker_sequence"] == [
        "TopicScopeAgent",
        "LogicChainAgent",
        "LiteratureSupportAgent",
        "NoveltyDepthAgent",
        "WritingFormatAgent",
    ]
    assert payload["trace"]["debate_candidates"]
    assert payload["trace"]["debate_resolutions"]
    assert payload["trace"]["worker_skills"][0]["rubric_skills"]
    assert payload["trace"]["worker_skills"][0]["policy_skills"]
    assert payload["trace"]["worker_runs"][0]["finding_count"] >= 0
    dimensions = {item["dimension"] for item in payload["report"]["dimension_reports"]}
    assert Dimension.NOVELTY_DEPTH.value in dimensions


def test_pdf_review_endpoint_returns_pdf_file(tmp_path: Path) -> None:
    file_path = tmp_path / "strong_case.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    client = TestClient(create_app())

    response = client.post(
        "/review/docx/pdf",
        json={"file_path": str(file_path)},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "strong_case-review.pdf" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-1.4")


def test_pdf_review_endpoint_cleans_up_temporary_pdf(tmp_path: Path, monkeypatch) -> None:
    file_path = tmp_path / "strong_case.docx"
    build_docx_from_case(file_path, STRONG_REVIEW_CASE)
    captured_pdf_path = tmp_path / "exported-review.pdf"
    app_module = importlib.import_module("papermentor_os.api.app")

    class _NamedTempHandle:
        def __init__(self, path: Path) -> None:
            self.name = str(path)

        def __enter__(self) -> "_NamedTempHandle":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    def _fake_named_temporary_file(*args, **kwargs) -> _NamedTempHandle:
        return _NamedTempHandle(captured_pdf_path)

    monkeypatch.setattr(app_module.tempfile, "NamedTemporaryFile", _fake_named_temporary_file)

    client = TestClient(create_app())
    response = client.post(
        "/review/docx/pdf",
        json={"file_path": str(file_path)},
    )

    assert response.status_code == 200
    assert not captured_pdf_path.exists()


def test_review_case_catalog_contains_baseline_and_debate_cases() -> None:
    case_ids = {case.case_id for case in REVIEW_CASE_CATALOG}
    tags = {tag for case in REVIEW_CASE_CATALOG for tag in case.tags}

    assert "minimal_review_case" in case_ids
    assert STRONG_REVIEW_CASE.case_id in case_ids
    assert WEAK_REVIEW_CASE.case_id in case_ids
    assert BOUNDARY_REVIEW_CASE.case_id in case_ids
    assert "baseline" in tags
    assert "strong_sample" in tags
    assert "boundary_sample" in tags
    assert "debate_candidate" in tags


def test_get_review_cases_by_tag_returns_expected_fixture_groups() -> None:
    strong_cases = get_review_cases_by_tag("strong_sample")
    weak_cases = get_review_cases_by_tag("weak_sample")

    assert STRONG_REVIEW_CASE in strong_cases
    assert WEAK_REVIEW_CASE in weak_cases
    assert BOUNDARY_REVIEW_CASE in weak_cases
