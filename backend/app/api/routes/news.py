from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.models.news import ImpactPresentation, NewsTopic, UserRole
from app.repositories.news_repository import NewsRepository
from app.schemas.news import (
    NewsFeedItem,
    ProcessedNewsResponse,
    RoleImpactResponse,
    normalize_one_sentence_for_api,
)

router: APIRouter = APIRouter()


@router.get("", response_model=list[NewsFeedItem])
def list_news(
    limit: int = Query(default=30, ge=1, le=100),
    topic: NewsTopic | None = Query(
        default=None,
        description="Filter by primary topic. Ignored when urgent=true.",
    ),
    urgent: bool = Query(
        default=False,
        description="Only items flagged as urgent / breaking (⚡ Срочно).",
    ),
    db_session: Session = Depends(get_db_session),
) -> list[NewsFeedItem]:
    repository = NewsRepository(db_session)
    topic_filter: NewsTopic | None = None if urgent else topic
    news_items = repository.list_published(
        limit=limit,
        topic=topic_filter,
        urgent_only=urgent,
    )
    return [
        NewsFeedItem(
            id=item.id,
            title=item.title,
            subtitle=normalize_one_sentence_for_api(item.one_sentence_summary),
            read_time_minutes=item.read_time_minutes,
            topic=item.topic,
            is_urgent=item.is_urgent,
            created_at=item.created_at,
        )
        for item in news_items
    ]


@router.get("/{news_id}", response_model=ProcessedNewsResponse)
def get_news(news_id: int, db_session: Session = Depends(get_db_session)) -> ProcessedNewsResponse:
    repository = NewsRepository(db_session)
    item = repository.get_processed_by_id(news_id)
    if item is None:
        raise HTTPException(status_code=404, detail="News item not found.")
    return ProcessedNewsResponse.model_validate(item)


@router.get("/{news_id}/impact", response_model=RoleImpactResponse)
def get_news_impact(
    news_id: int,
    role: UserRole = Query(default=UserRole.TENANT),
    db_session: Session = Depends(get_db_session),
) -> RoleImpactResponse:
    repository = NewsRepository(db_session)
    item = repository.get_processed_by_id(news_id)
    if item is None:
        raise HTTPException(status_code=404, detail="News item not found.")
    if item.impact_presentation != ImpactPresentation.MULTI:
        raise HTTPException(
            status_code=404,
            detail="Role-based impact is only available for multi-perspective items.",
        )

    role_to_text: dict[UserRole, str] = {
        UserRole.OWNER: item.impact_owner,
        UserRole.TENANT: item.impact_tenant,
        UserRole.BUYER: item.impact_buyer,
    }
    return RoleImpactResponse(role=role, text=role_to_text[role])
