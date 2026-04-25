import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.monitoring import last_pipeline_run
from app.repositories.news_repository import NewsRepository
from app.schemas.news import PipelineRunResponse
from app.services.pipeline_service import PipelineService

logger: logging.Logger = logging.getLogger(__name__)


def _failure_envelope(message: str) -> PipelineRunResponse:
    return PipelineRunResponse(
        fetched=0,
        feeds_failed=0,
        filtered_out=0,
        clustered=0,
        processed=0,
        published=0,
        needs_review=0,
        item_errors=0,
        ok=False,
        error=message[:500],
    )


def run_pipeline_task(
    db_session: Session, *, swallow_errors: bool | None = None
) -> PipelineRunResponse:
    use_swallow: bool = (
        settings.pipeline_task_swallow_errors if swallow_errors is None else swallow_errors
    )
    try:
        repository: NewsRepository = NewsRepository(db_session)
        service: PipelineService = PipelineService(repository=repository)
        result: PipelineRunResponse = service.run()
        last_pipeline_run.record_from_response(result)
        return result
    except Exception as e:
        logger.exception("Pipeline run failed: %s", e)
        failure: PipelineRunResponse = _failure_envelope(str(e))
        last_pipeline_run.record_from_response(failure)
        if not use_swallow:
            raise
        return failure
