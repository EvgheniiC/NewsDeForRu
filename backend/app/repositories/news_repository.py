import json
from datetime import datetime
from typing import Literal

from sqlalchemy import Select, and_, select
from sqlalchemy.orm import Session

import numpy as np

from app.models.news import (
    ClusterItem,
    ModerationEvent,
    NewsCluster,
    PipelineStatus,
    ProcessedNews,
    RawNewsItem,
    Source,
)


class NewsRepository:
    def __init__(self, db_session: Session) -> None:
        self.db_session: Session = db_session

    def upsert_source(self, source_key: str, name: str, rss_url: str) -> Source:
        query: Select[tuple[Source]] = select(Source).where(Source.source_key == source_key)
        source: Source | None = self.db_session.execute(query).scalar_one_or_none()
        if source is not None:
            if source.name != name or source.rss_url != rss_url:
                source.name = name
                source.rss_url = rss_url
                self.db_session.add(source)
                self.db_session.commit()
                self.db_session.refresh(source)
            return source

        source = Source(source_key=source_key, name=name, rss_url=rss_url)
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

    def get_cluster_by_key(self, cluster_key: str) -> NewsCluster | None:
        query: Select[tuple[NewsCluster]] = select(NewsCluster).where(NewsCluster.cluster_key == cluster_key)
        return self.db_session.execute(query).scalar_one_or_none()

    def list_clusters_with_centroid_since(
        self,
        since: datetime,
        limit: int = 10_000,
    ) -> list[NewsCluster]:
        query: Select[tuple[NewsCluster]] = (
            select(NewsCluster)
            .where(
                and_(
                    NewsCluster.centroid_embedding_json.is_not(None),
                    NewsCluster.updated_at >= since,
                ),
            )
            .order_by(NewsCluster.updated_at.desc())
            .limit(limit)
        )
        return list(self.db_session.execute(query).scalars().all())

    def set_cluster_centroid_embedding(self, cluster_id: int, embedding: list[float]) -> None:
        cluster: NewsCluster | None = self.db_session.get(NewsCluster, cluster_id)
        if cluster is None:
            return
        cluster.centroid_embedding_json = json.dumps(embedding)
        cluster.updated_at = datetime.utcnow()
        self.db_session.add(cluster)
        self.db_session.commit()

    def merge_cluster_centroid_embedding(
        self,
        cluster_id: int,
        new_embedding: list[float],
        previous_item_count: int,
    ) -> None:
        cluster: NewsCluster | None = self.db_session.get(NewsCluster, cluster_id)
        if cluster is None:
            return
        new_arr: np.ndarray = np.asarray(new_embedding, dtype=np.float32)
        if previous_item_count <= 0 or cluster.centroid_embedding_json is None:
            merged: np.ndarray = new_arr
        else:
            old_arr: np.ndarray = np.asarray(
                json.loads(cluster.centroid_embedding_json),
                dtype=np.float32,
            )
            merged = (old_arr * float(previous_item_count) + new_arr) / float(previous_item_count + 1)
        norm: float = float(np.linalg.norm(merged))
        if norm > 1e-9:
            merged = merged / norm
        cluster.centroid_embedding_json = json.dumps(merged.astype(float).tolist())
        cluster.updated_at = datetime.utcnow()
        self.db_session.add(cluster)
        self.db_session.commit()

    def upsert_cluster(self, cluster_key: str, canonical_title: str, summary: str) -> NewsCluster:
        cluster: NewsCluster | None = self.get_cluster_by_key(cluster_key)
        if cluster is None:
            cluster = NewsCluster(
                cluster_key=cluster_key,
                canonical_title=canonical_title[:512],
                summary=summary,
                size=0,
                updated_at=datetime.utcnow(),
            )
            self.db_session.add(cluster)
            self.db_session.commit()
            self.db_session.refresh(cluster)
            return cluster

        cluster.canonical_title = canonical_title[:512]
        cluster.summary = summary
        cluster.updated_at = datetime.utcnow()
        self.db_session.add(cluster)
        self.db_session.commit()
        self.db_session.refresh(cluster)
        return cluster

    def attach_raw_to_cluster(
        self,
        raw_item: RawNewsItem,
        cluster: NewsCluster,
        similarity_score: float = 1.0,
    ) -> ClusterItem:
        query: Select[tuple[ClusterItem]] = select(ClusterItem).where(ClusterItem.raw_item_id == raw_item.id)
        existing: ClusterItem | None = self.db_session.execute(query).scalar_one_or_none()
        if existing is not None:
            if existing.cluster_id != cluster.id:
                existing.cluster_id = cluster.id
                existing.is_primary = False
            existing.similarity_score = similarity_score
            self.db_session.add(existing)
            self.db_session.commit()
            self.db_session.refresh(existing)
            self.recalculate_cluster_size(cluster.id)
            return existing

        item: ClusterItem = ClusterItem(
            cluster_id=cluster.id,
            raw_item_id=raw_item.id,
            is_primary=cluster.size == 0,
            similarity_score=similarity_score,
        )
        self.db_session.add(item)
        self.db_session.commit()
        self.db_session.refresh(item)
        self.recalculate_cluster_size(cluster.id)
        return item

    def recalculate_cluster_size(self, cluster_id: int) -> None:
        cluster: NewsCluster | None = self.db_session.get(NewsCluster, cluster_id)
        if cluster is None:
            return
        query: Select[tuple[ClusterItem]] = select(ClusterItem).where(ClusterItem.cluster_id == cluster_id)
        cluster.size = len(list(self.db_session.execute(query).scalars().all()))
        cluster.updated_at = datetime.utcnow()
        self.db_session.add(cluster)
        self.db_session.commit()

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
        if status == PipelineStatus.PROCESSED:
            raw_item.processed_at = datetime.utcnow()
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

    def apply_moderation(
        self,
        news_id: int,
        status: PipelineStatus,
        audit_action: Literal["approve", "reject"],
    ) -> ProcessedNews | None:
        """Update publication status and record an audit row (manual moderation only)."""
        processed: ProcessedNews | None = self.get_processed_by_id(news_id)
        if processed is None:
            return None
        processed.publication_status = status
        self.db_session.add(processed)
        self.db_session.add(
            ModerationEvent(
                processed_news_id=processed.id,
                action=audit_action,
            )
        )
        self.db_session.commit()
        self.db_session.refresh(processed)
        return processed
