from __future__ import annotations

from contextlib import asynccontextmanager
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict
from starlette.background import BackgroundTask

from papermentor_os.api.run_registry import InMemoryReviewRunRegistry, ReviewRunClaimError
from papermentor_os.llm import (
    LLMConfigurationError,
    LLMError,
    LLMProviderError,
    LLMStructuredOutputError,
    ReviewLLMConfig,
)
from papermentor_os.reviewer_factory import build_chief_reviewer
from papermentor_os.reporting.pdf_exporter import PdfReportExporter
from papermentor_os.schemas.report import FinalReport
from papermentor_os.schemas.run import (
    AsyncReviewAcceptedResponse,
    ReviewRunClaimResponse,
    ReviewRunError,
    ReviewRunEventsResponse,
    ReviewRunResponse,
)
from papermentor_os.schemas.trace import DebugReviewResponse, ReviewTrace
from papermentor_os.schemas.types import Discipline, PaperStage


class ReviewDocxRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: str
    stage: PaperStage = PaperStage.DRAFT
    discipline: Discipline = Discipline.COMPUTER_SCIENCE
    llm: ReviewLLMConfig | None = None


def create_app(
    *,
    run_snapshot_dir: Path | None = None,
    run_retention_seconds: float | None = None,
    run_instance_id: str | None = None,
    run_lease_seconds: float = 30.0,
    server_llm_config: ReviewLLMConfig | None = None,
) -> FastAPI:
    resolved_server_llm_config = server_llm_config or _load_server_llm_config_from_env()

    def _validate_docx_path(file_path: str) -> Path:
        path = Path(file_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="docx file not found")
        if path.suffix.lower() != ".docx":
            raise HTTPException(status_code=400, detail="only .docx is supported in V1")
        return path

    def _build_review_error_detail(error: Exception) -> dict[str, Any]:
        if isinstance(error, LLMConfigurationError):
            return {
                "status_code": 400,
                "detail": {
                    "code": "llm_configuration_error",
                    "message": str(error),
                    "retryable": False,
                },
            }
        if isinstance(error, LLMProviderError):
            return {
                "status_code": 502,
                "detail": {
                    "code": "llm_provider_error",
                    "message": "LLM provider request failed before review completion.",
                    "retryable": True,
                },
            }
        if isinstance(error, LLMStructuredOutputError):
            return {
                "status_code": 502,
                "detail": {
                    "code": "llm_structured_output_error",
                    "message": "LLM provider returned invalid structured output.",
                    "retryable": True,
                },
            }
        if isinstance(error, LLMError):
            return {
                "status_code": 502,
                "detail": {
                    "code": "llm_runtime_error",
                    "message": "LLM review failed before review completion.",
                    "retryable": True,
                },
            }
        if isinstance(error, ValueError):
            return {
                "status_code": 400,
                "detail": {
                    "code": "invalid_request",
                    "message": str(error),
                    "retryable": False,
                },
            }
        raise error

    def _raise_review_http_error(error: Exception) -> None:
        error_detail = _build_review_error_detail(error)
        raise HTTPException(
            status_code=error_detail["status_code"],
            detail=error_detail["detail"],
        ) from error

    def _map_run_error(error: Exception) -> ReviewRunError:
        error_detail = _build_review_error_detail(error)
        detail = error_detail["detail"]
        return ReviewRunError(
            code=detail["code"],
            message=detail["message"],
            retryable=detail.get("retryable", False),
        )

    def _build_review_trace(reviewer) -> ReviewTrace:
        return ReviewTrace(
            worker_skills=reviewer.last_worker_skill_traces,
            worker_runs=reviewer.last_worker_execution_traces,
            orchestration=reviewer.last_orchestration_trace,
            debate_candidates=reviewer.last_debate_candidates,
            debate_resolutions=reviewer.last_debate_resolutions,
            debate_resolution_traces=reviewer.last_debate_resolution_traces,
        )

    def _format_sse(
        event: str,
        data: str,
        *,
        event_id: int | None = None,
        retry_ms: int | None = None,
    ) -> str:
        lines: list[str] = []
        if event_id is not None:
            lines.append(f"id: {event_id}")
        if retry_ms is not None:
            lines.append(f"retry: {retry_ms}")
        lines.append(f"event: {event}")
        lines.append(f"data: {data}")
        return "\n".join(lines) + "\n\n"

    def _resolve_sse_start_sequence_id(
        *,
        after_sequence_id: int | None,
        last_event_id: str | None,
    ) -> int:
        if after_sequence_id is not None:
            return after_sequence_id
        if last_event_id is None:
            return 0
        try:
            parsed = int(last_event_id)
        except ValueError as error:
            raise HTTPException(status_code=400, detail="invalid Last-Event-ID header") from error
        if parsed < 0:
            raise HTTPException(status_code=400, detail="invalid Last-Event-ID header")
        return parsed

    def _dump_sse_json(payload: dict[str, Any]) -> str:
        return json.dumps(payload, separators=(",", ":"))

    def _resolve_heartbeat_interval_ms(
        *,
        heartbeat_interval_ms: int | None,
        idle_timeout_seconds: float,
    ) -> int:
        if heartbeat_interval_ms is None:
            resolved = max(int(idle_timeout_seconds * 1000), 1)
        else:
            resolved = heartbeat_interval_ms
        if resolved < 100 or resolved > 60000:
            raise HTTPException(
                status_code=400,
                detail="heartbeat_interval_ms must be between 100 and 60000",
            )
        return resolved

    run_registry = InMemoryReviewRunRegistry(
        reviewer_builder=build_chief_reviewer,
        trace_builder=_build_review_trace,
        error_mapper=_map_run_error,
        snapshot_dir=run_snapshot_dir or (Path(tempfile.gettempdir()) / "papermentor_os_review_runs"),
        retention_seconds=run_retention_seconds,
        instance_id=run_instance_id,
        lease_seconds=run_lease_seconds,
        server_resume_llm_config=resolved_server_llm_config,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            yield
        finally:
            run_registry.close()

    app = FastAPI(title="PaperMentor OS", version="0.1.0", lifespan=lifespan)
    pdf_exporter = PdfReportExporter()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/review/docx", response_model=FinalReport)
    def review_docx(request: ReviewDocxRequest) -> FinalReport:
        path = _validate_docx_path(request.file_path)
        try:
            reviewer = build_chief_reviewer(request.llm)
            return reviewer.review_docx(
                path,
                stage=request.stage,
                discipline=request.discipline,
            )
        except Exception as error:
            _raise_review_http_error(error)

    @app.post("/review/docx/debug", response_model=DebugReviewResponse)
    def review_docx_debug(request: ReviewDocxRequest) -> DebugReviewResponse:
        path = _validate_docx_path(request.file_path)
        try:
            reviewer = build_chief_reviewer(request.llm)
            report = reviewer.review_docx(
                path,
                stage=request.stage,
                discipline=request.discipline,
            )
        except Exception as error:
            _raise_review_http_error(error)

        return DebugReviewResponse(
            report=report,
            trace=_build_review_trace(reviewer),
        )

    @app.post("/review/docx/async", response_model=AsyncReviewAcceptedResponse, status_code=202)
    def review_docx_async(request: ReviewDocxRequest) -> AsyncReviewAcceptedResponse:
        path = _validate_docx_path(request.file_path)
        try:
            return run_registry.submit_docx(
                file_path=path,
                stage=request.stage,
                discipline=request.discipline,
                llm_config=request.llm,
            )
        except Exception as error:
            _raise_review_http_error(error)

    @app.get("/review/runs/{run_id}", response_model=ReviewRunResponse)
    def get_review_run(run_id: str) -> ReviewRunResponse:
        payload = run_registry.get_run(run_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="review run not found")
        return payload

    @app.post("/review/runs/{run_id}/claim", response_model=ReviewRunClaimResponse)
    def claim_review_run(run_id: str) -> ReviewRunClaimResponse:
        try:
            payload = run_registry.claim_run(run_id)
        except ReviewRunClaimError as error:
            status_code = 409 if error.code == "active_foreign_lease" else 400
            raise HTTPException(
                status_code=status_code,
                detail={
                    "code": error.code,
                    "message": error.message,
                },
            ) from error
        if payload is None:
            raise HTTPException(status_code=404, detail="review run not found")
        return payload

    @app.get("/review/runs/{run_id}/events", response_model=ReviewRunEventsResponse)
    def get_review_run_events(run_id: str, after_sequence_id: int | None = None) -> ReviewRunEventsResponse:
        payload = run_registry.get_events(run_id, after_sequence_id=after_sequence_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="review run not found")
        return payload

    @app.get("/review/runs/{run_id}/events/stream")
    def stream_review_run_events(
        run_id: str,
        after_sequence_id: int | None = None,
        poll_interval_ms: int = 200,
        idle_timeout_seconds: float = 15.0,
        heartbeat_interval_ms: int | None = None,
        last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    ) -> StreamingResponse:
        if run_registry.get_run(run_id) is None:
            raise HTTPException(status_code=404, detail="review run not found")
        start_sequence_id = _resolve_sse_start_sequence_id(
            after_sequence_id=after_sequence_id,
            last_event_id=last_event_id,
        )
        resolved_heartbeat_interval_ms = _resolve_heartbeat_interval_ms(
            heartbeat_interval_ms=heartbeat_interval_ms,
            idle_timeout_seconds=idle_timeout_seconds,
        )

        def _event_stream():
            last_sequence_id = start_sequence_id
            heartbeat_deadline = time.monotonic() + (resolved_heartbeat_interval_ms / 1000)
            while True:
                event_payload = run_registry.get_events(run_id, after_sequence_id=last_sequence_id)
                if event_payload is None:
                    return
                if event_payload.events:
                    for item in event_payload.events:
                        last_sequence_id = item.sequence_id
                        yield _format_sse(
                            "review_run_event",
                            item.model_dump_json(),
                            event_id=item.sequence_id,
                            retry_ms=max(poll_interval_ms, 1),
                        )
                    heartbeat_deadline = time.monotonic() + (resolved_heartbeat_interval_ms / 1000)

                run_payload = run_registry.get_run(run_id)
                if run_payload is None:
                    return
                if run_payload.run.state in {"completed", "failed"} and not event_payload.events:
                    break
                if run_payload.run.state in {"completed", "failed"} and event_payload.events:
                    break
                if time.monotonic() >= heartbeat_deadline:
                    yield _format_sse(
                        "heartbeat",
                        _dump_sse_json(
                            {
                                "run_id": run_id,
                                "last_sequence_id": last_sequence_id,
                                "run_state": run_payload.run.state,
                            }
                        ),
                        retry_ms=resolved_heartbeat_interval_ms,
                    )
                    heartbeat_deadline = time.monotonic() + (resolved_heartbeat_interval_ms / 1000)
                time.sleep(max(poll_interval_ms, 1) / 1000)

            final_event = (
                "review_run_failed"
                if run_payload.run.state == "failed"
                else "review_run_completed"
            )
            final_payload = {
                "run_id": run_id,
                "last_sequence_id": last_sequence_id,
                "final_state": run_payload.run.state,
            }
            if run_payload.error is not None:
                final_payload["error"] = run_payload.error.model_dump(mode="json")
            yield _format_sse(
                final_event,
                _dump_sse_json(final_payload),
                event_id=last_sequence_id if last_sequence_id > 0 else None,
            )

        return StreamingResponse(
            _event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "X-PaperMentor-SSE-Heartbeat-Ms": str(resolved_heartbeat_interval_ms),
            },
        )

    @app.post("/review/docx/pdf")
    def review_docx_pdf(request: ReviewDocxRequest) -> FileResponse:
        path = _validate_docx_path(request.file_path)
        try:
            reviewer = build_chief_reviewer(request.llm)
            paper = reviewer.parser.parse_file(
                path,
                stage=request.stage,
                discipline=request.discipline,
            )
            report = reviewer.review_paper(paper)
        except Exception as error:
            _raise_review_http_error(error)

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


def _load_server_llm_config_from_env() -> ReviewLLMConfig | None:
    env_values = {
        "provider_id": os.getenv("PAPERMENTOR_OS_SERVER_LLM_PROVIDER_ID"),
        "base_url": os.getenv("PAPERMENTOR_OS_SERVER_LLM_BASE_URL"),
        "api_key": os.getenv("PAPERMENTOR_OS_SERVER_LLM_API_KEY"),
        "model_name": os.getenv("PAPERMENTOR_OS_SERVER_LLM_MODEL_NAME"),
        "review_backend": os.getenv("PAPERMENTOR_OS_SERVER_LLM_REVIEW_BACKEND"),
    }
    if not any(env_values.values()):
        return None

    missing_vars = [
        env_name
        for env_name, value in {
            "PAPERMENTOR_OS_SERVER_LLM_BASE_URL": env_values["base_url"],
            "PAPERMENTOR_OS_SERVER_LLM_API_KEY": env_values["api_key"],
            "PAPERMENTOR_OS_SERVER_LLM_MODEL_NAME": env_values["model_name"],
        }.items()
        if not value
    ]
    if missing_vars:
        raise RuntimeError(
            "server resume LLM config is incomplete; missing "
            + ", ".join(sorted(missing_vars))
        )

    review_backend = ReviewBackend(
        env_values["review_backend"] or ReviewBackend.MODEL_WITH_FALLBACK.value
    )
    if review_backend == ReviewBackend.RULE_ONLY:
        raise RuntimeError("server resume LLM config cannot use rule_only backend")

    return ReviewLLMConfig(
        review_backend=review_backend,
        provider_id=env_values["provider_id"] or "openai_compatible",
        base_url=env_values["base_url"],
        api_key=env_values["api_key"],
        model_name=env_values["model_name"],
    )


app = create_app()
