from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.models.news import FeedPeriod, ImpactPresentation, NewsTopic, ProcessedNews, UserRole
from app.repositories.news_repository import NewsRepository
from app.utils.feed_period import period_start_utc_naive
from app.schemas.news import (
    FullArticleResponse,
    NewsFeedItem,
    NewsFeedPageResponse,
    ProcessedNewsResponse,
    RoleImpactResponse,
    TopNewsFeedItem,
    TopNewsRankMeta,
    TopNewsTodayResponse,
    normalize_one_sentence_for_api,
)
from app.services.full_article_service import FullArticleService, FullArticleUnavailableError
from app.services.news_attribution import build_processed_news_response, published_at_and_source_name
from app.services.top_news_scoring import total_top_score

router: APIRouter = APIRouter()


@router.get("", response_model=NewsFeedPageResponse)
def list_news(
    limit: int = Query(default=30, ge=1, le=100),
    cursor: int | None = Query(
        default=None,
        description="Continue after this news id (exclusive); from previous ``next_cursor``.",
    ),
    topic: NewsTopic | None = Query(
        default=None,
        description="Filter by primary topic. Ignored when urgent=true.",
    ),
    urgent: bool = Query(
        default=False,
        description="Only items flagged as urgent / breaking (⚡ Срочно).",
    ),
    positive_only: bool = Query(
        default=False,
        description="Only uplifting / constructive stories (☀️ ТПН). Ignored when urgent=true.",
    ),
    period: FeedPeriod | None = Query(
        default=None,
        description="Lower bound on RSS publication time: today, last 3 calendar days, this ISO week, or this month (Europe/Berlin).",
    ),
    db_session: Session = Depends(get_db_session),
) -> NewsFeedPageResponse:
    repository = NewsRepository(db_session)
    topic_filter: NewsTopic | None = None if urgent or positive_only else topic
    since = period_start_utc_naive(period)
    news_rows, has_more = repository.list_published(
        limit=limit,
        topic=topic_filter,
        urgent_only=urgent,
        positive_only=positive_only,
        cursor_id=cursor,
        published_at_since=since,
    )
    items_list: list[NewsFeedItem] = []
    for item in news_rows:
        pub_at, source_name = published_at_and_source_name(item)
        items_list.append(
            NewsFeedItem(
                id=item.id,
                title=item.title,
                subtitle=normalize_one_sentence_for_api(item.one_sentence_summary),
                image_url=item.image_url,
                read_time_minutes=item.read_time_minutes,
                topic=item.topic,
                is_urgent=item.is_urgent,
                is_positive=item.is_positive,
                published_at=pub_at,
                source_name=source_name,
                created_at=item.created_at,
            )
        )
    next_cursor: int | None = items_list[-1].id if has_more and items_list else None
    return NewsFeedPageResponse(items=items_list, next_cursor=next_cursor)


@router.get("/top-today", response_model=TopNewsTodayResponse)
def list_top_news_today(
    limit: int = Query(default=5, ge=1, le=20),
    db_session: Session = Depends(get_db_session),
) -> TopNewsTodayResponse:
    """Published stories from calendar *today* (Berlin), ranked by mentions + freshness + AI importance."""
    repository: NewsRepository = NewsRepository(db_session)
    since: datetime | None = period_start_utc_naive(FeedPeriod.TODAY)
    start: datetime = since if since is not None else datetime(1970, 1, 1)
    candidates: list[ProcessedNews] = repository.list_published_since_with_raw(
        published_at_since=start,
        limit=500,
    )
    now_utc: datetime = datetime.now(timezone.utc).replace(tzinfo=None)
    scored: list[tuple[int, int, ProcessedNews, TopNewsRankMeta]] = []
    for item in candidates:
        raw = item.raw_item
        if raw is None:
            continue
        cluster_id: int | None = item.cluster_id
        if cluster_id is None:
            source_count: int = 1
        else:
            distinct: int = repository.count_distinct_sources_in_cluster(cluster_id)
            source_count = max(distinct, 1)
        total, mp, fp, ai = total_top_score(
            distinct_source_count=source_count,
            published_at_utc_naive=raw.published_at,
            now_utc_naive=now_utc,
            ai_importance_1_to_10=item.importance_ai_score,
        )
        meta: TopNewsRankMeta = TopNewsRankMeta(
            total_score=total,
            source_count=source_count,
            mentions_points=mp,
            freshness_points=fp,
            ai_importance=ai,
        )
        scored.append((total, item.id, item, meta))
    scored.sort(key=lambda row: (-row[0], -row[1]))
    top: list[tuple[int, int, ProcessedNews, TopNewsRankMeta]] = scored[:limit]
    items_out: list[TopNewsFeedItem] = []
    for _, _, row, meta in top:
        pub_at, source_name = published_at_and_source_name(row)
        items_out.append(
            TopNewsFeedItem(
                id=row.id,
                title=row.title,
                subtitle=normalize_one_sentence_for_api(row.one_sentence_summary),
                image_url=row.image_url,
                read_time_minutes=row.read_time_minutes,
                topic=row.topic,
                is_urgent=row.is_urgent,
                is_positive=row.is_positive,
                published_at=pub_at,
                source_name=source_name,
                created_at=row.created_at,
                rank=meta,
            )
        )
    return TopNewsTodayResponse(items=items_out)


@router.get("/{news_id}", response_model=ProcessedNewsResponse)
def get_news(news_id: int, db_session: Session = Depends(get_db_session)) -> ProcessedNewsResponse:
    repository = NewsRepository(db_session)
    item = repository.get_processed_by_id_with_raw(news_id)
    if item is None:
        raise HTTPException(status_code=404, detail="News item not found.")
    if item is None:
        raise HTTPException(status_code=404, detail="News item not found.")
    return build_processed_news_response(item)


@router.get("/{news_id}/full-article", response_model=FullArticleResponse)
def get_news_full_article(
    news_id: int,
    db_session: Session = Depends(get_db_session),
) -> FullArticleResponse:
    """Return cached Russian full article or fetch, translate, and store on first request."""
    service: FullArticleService = FullArticleService(db_session)
    try:
        body_ru, cached = service.get_or_create_full_article_ru(news_id)
    except FullArticleUnavailableError as e:
        detail: str = str(e)
        status: int = 404 if "not found" in detail.lower() else 503
        raise HTTPException(status_code=status, detail=detail) from e
    return FullArticleResponse(news_id=news_id, full_article_ru=body_ru, cached=cached)


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
