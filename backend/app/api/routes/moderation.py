from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.models.news import PipelineStatus, ProcessedNews, RawNewsItem
from app.repositories.news_repository import NewsRepository
from app.schemas.news import ModerationActionRequest, ProcessedNewsResponse
from app.services.telegram_notifier import send_moderation_approved_notice

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
    repository: NewsRepository = NewsRepository(db_session)
    before: ProcessedNews | None = repository.get_processed_by_id(news_id)
    if before is None:
        raise HTTPException(status_code=404, detail="News item not found.")

    from_moderation_queue: bool = before.publication_status == PipelineStatus.NEEDS_REVIEW
    target_status: PipelineStatus = (
        PipelineStatus.PUBLISHED if request.action == "approve" else PipelineStatus.FILTERED_OUT
    )
    item: ProcessedNews | None = repository.apply_moderation(
        news_id=news_id,
        status=target_status,
        audit_action=request.action,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="News item not found.")

    if request.action == "approve" and from_moderation_queue:
        raw: RawNewsItem | None = item.raw_item
        relevance_score: float = float(raw.relevance_score) if raw is not None else 0.0
        send_moderation_approved_notice(
            title_ru=item.title,
            one_sentence_summary=item.one_sentence_summary,
            confidence_score=item.confidence_score,
            relevance_score=relevance_score,
            source_url=item.source_url,
            image_url=item.image_url,
            processed_id=item.id,
        )

    return ProcessedNewsResponse.model_validate(item)
