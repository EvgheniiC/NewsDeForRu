from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps.auth import require_moderator
from app.core.database import get_db_session
from app.models.app_user import AppUser
from app.models.news import PipelineStatus, ProcessedNews
from app.repositories.news_repository import NewsRepository
from app.schemas.news import ModerationActionRequest, NewsMetadataPatchRequest, ProcessedNewsResponse
from app.services.telegram_notifier import send_moderation_approved_notice

router: APIRouter = APIRouter()


@router.get("/queue", response_model=list[ProcessedNewsResponse])
def list_queue(
    db_session: Session = Depends(get_db_session),
    _user: AppUser = Depends(require_moderator),
) -> list[ProcessedNewsResponse]:
    repository = NewsRepository(db_session)
    return [ProcessedNewsResponse.model_validate(item) for item in repository.list_needs_review()]


@router.patch("/{news_id}/metadata", response_model=ProcessedNewsResponse)
def patch_news_metadata(
    news_id: int,
    request: NewsMetadataPatchRequest,
    db_session: Session = Depends(get_db_session),
    actor: AppUser = Depends(require_moderator),
) -> ProcessedNewsResponse:
    repository: NewsRepository = NewsRepository(db_session)
    before: ProcessedNews | None = repository.get_processed_by_id(news_id)
    if before is None:
        raise HTTPException(status_code=404, detail="News item not found.")
    if before.publication_status != PipelineStatus.NEEDS_REVIEW:
        raise HTTPException(
            status_code=409,
            detail="Metadata can only be edited while the item is in the moderation queue.",
        )

    item: ProcessedNews | None = repository.update_processed_metadata(
        news_id=news_id,
        topic=request.topic,
        is_urgent=request.is_urgent,
        is_positive=request.is_positive,
        user_id=actor.id,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="News item not found.")
    return ProcessedNewsResponse.model_validate(item)


@router.post("/{news_id}/action", response_model=ProcessedNewsResponse)
def moderate_news(
    news_id: int,
    request: ModerationActionRequest,
    db_session: Session = Depends(get_db_session),
    actor: AppUser = Depends(require_moderator),
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
        user_id=actor.id,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="News item not found.")

    if request.action == "approve" and from_moderation_queue:
        sent_mod: bool = send_moderation_approved_notice(
            title_ru=item.title,
            topic=item.topic,
            one_sentence_summary=item.one_sentence_summary,
            source_url=item.source_url,
            image_url=item.image_url,
            processed_id=item.id,
        )
        if sent_mod:
            repository.mark_telegram_notified(item.id)

    return ProcessedNewsResponse.model_validate(item)
