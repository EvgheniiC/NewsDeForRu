from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.news import PipelineStatus, ProcessedNews, RawNewsItem, Source


class NewsRepository:
    def __init__(self, db_session: Session) -> None:
        self.db_session: Session = db_session

    def get_or_create_source(self, name: str, rss_url: str) -> Source:
        query: Select[tuple[Source]] = select(Source).where(Source.name == name)
        source: Source | None = self.db_session.execute(query).scalar_one_or_none()
        if source is not None:
            return source

        source = Source(name=name, rss_url=rss_url)
        self.db_session.add(source)
        self.db_session.commit()
        self.db_session.refresh(source)
        return source

    def has_raw_item(self, source_id: int, guid: str) -> bool:
        query: Select[tuple[RawNewsItem]] = select(RawNewsItem).where(
            RawNewsItem.source_id == source_id,
            RawNewsItem.guid == guid,
        )
        return self.db_session.execute(query).scalar_one_or_none() is not None

    def create_raw_item(
        self,
        source_id: int,
        guid: str,
        title: str,
        summary: str,
        url: str,
        published_at: datetime,
    ) -> RawNewsItem:
        item: RawNewsItem = RawNewsItem(
            source_id=source_id,
            guid=guid,
            title=title,
            summary=summary,
            url=url,
            published_at=published_at,
        )
        self.db_session.add(item)
        self.db_session.commit()
        self.db_session.refresh(item)
        return item

    def list_raw_items_for_processing(self) -> list[RawNewsItem]:
        query: Select[tuple[RawNewsItem]] = (
            select(RawNewsItem)
            .where(RawNewsItem.pipeline_status == PipelineStatus.INGESTED)
            .order_by(RawNewsItem.published_at.desc())
        )
        return list(self.db_session.execute(query).scalars().all())

    def update_raw_status(
        self,
        raw_item: RawNewsItem,
        status: PipelineStatus,
        relevance_score: float = 0.0,
        relevance_reason: str = "",
        cluster_key: str | None = None,
    ) -> None:
        raw_item.pipeline_status = status
        raw_item.relevance_score = relevance_score
        raw_item.relevance_reason = relevance_reason
        raw_item.cluster_key = cluster_key
        self.db_session.add(raw_item)
        self.db_session.commit()

    def create_processed_news(self, processed: ProcessedNews) -> ProcessedNews:
        self.db_session.add(processed)
        self.db_session.commit()
        self.db_session.refresh(processed)
        return processed

    def list_published(self, limit: int = 50) -> list[ProcessedNews]:
        query: Select[tuple[ProcessedNews]] = (
            select(ProcessedNews)
            .where(ProcessedNews.publication_status == PipelineStatus.PUBLISHED)
            .order_by(ProcessedNews.created_at.desc())
            .limit(limit)
        )
        return list(self.db_session.execute(query).scalars().all())

    def list_needs_review(self) -> list[ProcessedNews]:
        query: Select[tuple[ProcessedNews]] = (
            select(ProcessedNews)
            .where(ProcessedNews.publication_status == PipelineStatus.NEEDS_REVIEW)
            .order_by(ProcessedNews.created_at.desc())
        )
        return list(self.db_session.execute(query).scalars().all())

    def get_processed_by_id(self, news_id: int) -> ProcessedNews | None:
        query: Select[tuple[ProcessedNews]] = select(ProcessedNews).where(ProcessedNews.id == news_id)
        return self.db_session.execute(query).scalar_one_or_none()

    def set_publication_status(self, news_id: int, status: PipelineStatus) -> ProcessedNews | None:
        processed: ProcessedNews | None = self.get_processed_by_id(news_id)
        if processed is None:
            return None
        processed.publication_status = status
        self.db_session.add(processed)
        self.db_session.commit()
        self.db_session.refresh(processed)
        return processed
