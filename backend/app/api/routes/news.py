from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.models.news import UserRole
from app.repositories.news_repository import NewsRepository
from app.schemas.news import NewsFeedItem, ProcessedNewsResponse, RoleImpactResponse

router: APIRouter = APIRouter()


@router.get("", response_model=list[NewsFeedItem])
def list_news(
    limit: int = Query(default=30, ge=1, le=100),
    db_session: Session = Depends(get_db_session),
) -> list[NewsFeedItem]:
    repository = NewsRepository(db_session)
    news_items = repository.list_published(limit=limit)
    return [
        NewsFeedItem(
            id=item.id,
            title=item.title,
            subtitle=item.one_sentence_summary,
            read_time_minutes=item.read_time_minutes,
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

    role_to_text: dict[UserRole, str] = {
        UserRole.OWNER: item.impact_owner,
        UserRole.TENANT: item.impact_tenant,
        UserRole.BUYER: item.impact_buyer,
    }
    return RoleImpactResponse(role=role, text=role_to_text[role])
