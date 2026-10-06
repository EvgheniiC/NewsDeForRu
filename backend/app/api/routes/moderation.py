from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps.auth import require_moderator
from app.core.database import get_db_session
from app.models.app_user import AppUser
from app.models.news import PipelineStatus, ProcessedNews
from app.repositories.engagement_repository import count_app_visits_on
from app.repositories.news_repository import NewsRepository
from app.schemas.news import (
    ModerationActionRequest,
    ModerationDailyStatsResponse,
    NewsMetadataPatchRequest,
    ProcessedNewsResponse,
)
from app.services.news_attribution import attribution_from_processed, build_processed_news_response
from app.services.telegram_notifier import send_moderation_approved_notice
from app.services.push_notifier import send_urgent_push_notice
from app.utils.feed_period import berlin_calendar_day_bounds_utc_naive, berlin_today

router: APIRouter = APIRouter()


@router.get("/queue", response_model=list[ProcessedNewsResponse])
def list_queue(
    db_session: Session = Depends(get_db_session),
    _user: AppUser = Depends(require_moderator),
) -> list[ProcessedNewsResponse]:
    repository = NewsRepository(db_session)
    return [build_processed_news_response(item) for item in repository.list_needs_review()]


@router.get("/daily-stats", response_model=ModerationDailyStatsResponse)
def daily_stats(
    day: date | None = Query(
        default=None,
        alias="date",
        description="Calendar day in Europe/Berlin (YYYY-MM-DD). Defaults to today.",
    ),
    db_session: Session = Depends(get_db_session),
    _user: AppUser = Depends(require_moderator),
) -> ModerationDailyStatsResponse:
    selected_day: date = berlin_today() if day is None else day
    day_start, day_end = berlin_calendar_day_bounds_utc_naive(selected_day)
    repository: NewsRepository = NewsRepository(db_session)
    published_count: int = repository.count_feed_published_between(
        published_at_start=day_start,
        published_at_end=day_end,
    )
    moderation_count: int = repository.count_needs_review_created_between(
        created_at_start=day_start,
        created_at_end=day_end,
    )
    visit_count: int = count_app_visits_on(db_session, selected_day)
    return ModerationDailyStatsResponse(
        date=selected_day,
        published_count=published_count,
        moderation_count=moderation_count,
        visit_count=visit_count,
    )


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
            detail="Copy and metadata can only be edited while the item is in the moderation queue.",
        )

    item: ProcessedNews | None = repository.update_processed_metadata(
        news_id=news_id,
        topic=request.topic,
        cover_tag=request.cover_tag,
        is_urgent=request.is_urgent,
        is_positive=request.is_positive,
        title=request.title,
        one_sentence_summary=request.one_sentence_summary,
        user_id=actor.id,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="News item not found.")
    loaded: ProcessedNews | None = repository.get_processed_by_id_with_raw(news_id)
    if loaded is None:
        raise HTTPException(status_code=404, detail="News item not found.")
    return build_processed_news_response(loaded)


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
    # A moderator decision publishes drafts that have no publisher licence.
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
        notice_item: ProcessedNews | None = repository.get_processed_by_id_with_raw(news_id)
        _published_at, notice_source_name, notice_source_url = (
            attribution_from_processed(notice_item)
            if notice_item is not None
            else (item.created_at, "", "")
        )
        sent_mod: bool = send_moderation_approved_notice(
            title_ru=item.title,
            topic=item.topic,
            cover_tag=item.cover_tag,
            one_sentence_summary=item.one_sentence_summary,
            source_url=notice_source_url,
            source_name=notice_source_name,
            changes_notice=item.changes_notice or "",
            processed_id=item.id,
        )
        if sent_mod:
            repository.mark_telegram_notified(item.id)
        if item.is_urgent:
            sent_push_mod: bool = send_urgent_push_notice(
                title_ru=item.title,
                one_sentence_summary=item.one_sentence_summary,
                processed_id=item.id,
                source_name=notice_source_name,
                source_url=notice_source_url,
                use_urgent_retries=True,
            )
            if sent_push_mod:
                repository.mark_push_notified(item.id)

    loaded: ProcessedNews | None = repository.get_processed_by_id_with_raw(news_id)
    if loaded is None:
        raise HTTPException(status_code=404, detail="News item not found.")
    return build_processed_news_response(loaded)
