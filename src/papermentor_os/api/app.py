from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from starlette.background import BackgroundTask

from papermentor_os.orchestrator.chief_reviewer import ChiefReviewer
from papermentor_os.reporting.pdf_exporter import PdfReportExporter
from papermentor_os.schemas.report import FinalReport
from papermentor_os.schemas.trace import DebugReviewResponse, ReviewTrace
from papermentor_os.schemas.types import Discipline, PaperStage


class ReviewDocxRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: str
    stage: PaperStage = PaperStage.DRAFT
    discipline: Discipline = Discipline.COMPUTER_SCIENCE


def create_app() -> FastAPI:
    app = FastAPI(title="PaperMentor OS", version="0.1.0")
    reviewer = ChiefReviewer()
    pdf_exporter = PdfReportExporter()

    def _validate_docx_path(file_path: str) -> Path:
        path = Path(file_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="docx file not found")
        if path.suffix.lower() != ".docx":
            raise HTTPException(status_code=400, detail="only .docx is supported in V1")
        return path

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/review/docx", response_model=FinalReport)
    def review_docx(request: ReviewDocxRequest) -> FinalReport:
        path = _validate_docx_path(request.file_path)
        try:
            return reviewer.review_docx(
                path,
                stage=request.stage,
                discipline=request.discipline,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/review/docx/debug", response_model=DebugReviewResponse)
    def review_docx_debug(request: ReviewDocxRequest) -> DebugReviewResponse:
        path = _validate_docx_path(request.file_path)
        try:
            report = reviewer.review_docx(
                path,
                stage=request.stage,
                discipline=request.discipline,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        return DebugReviewResponse(
            report=report,
            trace=ReviewTrace(
                worker_skills=reviewer.last_worker_skill_traces,
                worker_runs=reviewer.last_worker_execution_traces,
                orchestration=reviewer.last_orchestration_trace,
                debate_candidates=reviewer.last_debate_candidates,
                debate_resolutions=reviewer.last_debate_resolutions,
            ),
        )

    @app.post("/review/docx/pdf")
    def review_docx_pdf(request: ReviewDocxRequest) -> FileResponse:
        path = _validate_docx_path(request.file_path)
        try:
            paper = reviewer.parser.parse_file(
                path,
                stage=request.stage,
                discipline=request.discipline,
            )
            report = reviewer.review_paper(paper)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        with tempfile.NamedTemporaryFile(
            prefix=f"{path.stem}-review-",
            suffix=".pdf",
            delete=False,
        ) as handle:
            pdf_path = Path(handle.name)

        pdf_exporter.export(
            report,
            paper_title=paper.title,
            output_path=pdf_path,
        )
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"{path.stem}-review.pdf",
            background=BackgroundTask(pdf_path.unlink, missing_ok=True),
        )

    return app


app = create_app()
