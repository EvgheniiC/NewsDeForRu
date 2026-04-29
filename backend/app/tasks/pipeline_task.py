import contextvars
import logging
import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.monitoring import last_pipeline_run
from app.monitoring.prometheus_metrics import record_pipeline_finished
from app.monitoring.pipeline_run_context import reset_pipeline_run_id, set_pipeline_run_id
from app.repositories.news_repository import NewsRepository
from app.schemas.news import PipelineRunResponse
from app.services.pipeline_service import PipelineService

logger: logging.Logger = logging.getLogger(__name__)


def _failure_envelope(message: str, run_id: str) -> PipelineRunResponse:
    return PipelineRunResponse(
        fetched=0,
        feeds_failed=0,
        filtered_out=0,
        clustered=0,
        processed=0,
        published=0,
        needs_review=0,
        item_errors=0,
        run_id=run_id,
        ok=False,
        error=message[:500],
    )


def run_pipeline_task(
    db_session: Session, *, swallow_errors: bool | None = None
) -> PipelineRunResponse:
    use_swallow: bool = (
        settings.pipeline_task_swallow_errors if swallow_errors is None else swallow_errors
    )
    run_id: str = str(uuid.uuid4())
    ctx_token: contextvars.Token[str | None] = set_pipeline_run_id(run_id)
    try:
        try:
            repository: NewsRepository = NewsRepository(db_session)
            service: PipelineService = PipelineService(repository=repository)
            result: PipelineRunResponse = service.run(run_id=run_id)
            last_pipeline_run.record_from_response(result)
            record_pipeline_finished(ok=result.ok)
            return result
        except Exception as e:
            logger.exception("Pipeline run failed: %s", e)
            failure: PipelineRunResponse = _failure_envelope(str(e), run_id)
            last_pipeline_run.record_from_response(failure)
            record_pipeline_finished(ok=False)
            if not use_swallow:
                raise
            return failure
    finally:
        reset_pipeline_run_id(ctx_token)
