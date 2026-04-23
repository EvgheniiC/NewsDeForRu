from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.repositories.news_repository import NewsRepository
from app.schemas.news import PipelineRunResponse
from app.services.pipeline_service import PipelineService

router: APIRouter = APIRouter()


@router.post("/run", response_model=PipelineRunResponse)
def run_pipeline(db_session: Session = Depends(get_db_session)) -> PipelineRunResponse:
    repository = NewsRepository(db_session)
    service = PipelineService(repository=repository)
    return service.run()
