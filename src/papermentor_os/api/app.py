from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

from papermentor_os.orchestrator.chief_reviewer import ChiefReviewer
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
                debate_candidates=reviewer.last_debate_candidates,
                debate_resolutions=reviewer.last_debate_resolutions,
            ),
        )

    return app


app = create_app()
