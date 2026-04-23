from sqlalchemy.orm import Session

from app.repositories.news_repository import NewsRepository
from app.schemas.news import PipelineRunResponse
from app.services.pipeline_service import PipelineService


def run_pipeline_task(db_session: Session) -> PipelineRunResponse:
    repository = NewsRepository(db_session)
    service = PipelineService(repository=repository)
    return service.run()
