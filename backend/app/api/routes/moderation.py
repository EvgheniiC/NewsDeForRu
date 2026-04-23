from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.models.news import PipelineStatus
from app.repositories.news_repository import NewsRepository
from app.schemas.news import ModerationActionRequest, ProcessedNewsResponse

router: APIRouter = APIRouter()


@router.get("/queue", response_model=list[ProcessedNewsResponse])
def list_queue(db_session: Session = Depends(get_db_session)) -> list[ProcessedNewsResponse]:
    repository = NewsRepository(db_session)
    return [ProcessedNewsResponse.model_validate(item) for item in repository.list_needs_review()]


@router.post("/{news_id}/action", response_model=ProcessedNewsResponse)
def moderate_news(
    news_id: int,
    request: ModerationActionRequest,
    db_session: Session = Depends(get_db_session),
) -> ProcessedNewsResponse:
    repository = NewsRepository(db_session)
    target_status = (
        PipelineStatus.PUBLISHED if request.action == "approve" else PipelineStatus.FILTERED_OUT
    )
    item = repository.set_publication_status(news_id=news_id, status=target_status)
    if item is None:
        raise HTTPException(status_code=404, detail="News item not found.")
    return ProcessedNewsResponse.model_validate(item)
