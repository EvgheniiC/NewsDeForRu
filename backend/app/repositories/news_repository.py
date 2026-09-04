import json
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from sqlalchemy import Select, and_, exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

import numpy as np

from app.core.config import settings
from app.models.news import (
    ClusterItem,
    ModerationEvent,
    NewsCluster,
    NewsTopic,
    PipelineStatus,
    ProcessedNews,
    RawNewsItem,
    Source,
)
from app.services.publisher_editorial import PUBLISHER_EDITORIAL_SOURCE_KEYS
from app.services.relevance_filter_service import OFFICIAL_DATA_SOURCE_KEYS
from app.services.rss_sources import (
    is_source_allowed_for_publication,
    publication_allowed_sql_filter,
)
from app.services.urgent_news import is_breaking_news


class NewsRepository:
    def __init__(self, db_session: Session) -> None:
        self.db_session: Session = db_session

    def _publication_source_filter(self) -> Any:
        return publication_allowed_sql_filter(
            settings.rss_enabled_source_keys,
            allow_unverified=settings.rss_allow_unverified_catalog_sources,
        )

    def upsert_source(
        self,
        source_key: str,
        name: str,
        rss_url: str,
        *,
        default_licence: str | None = None,
        default_licence_url: str | None = None,
        copyright_holder: str | None = None,
        original_language: str | None = None,
        changes_notice: str | None = None,
        rights_verified: bool = False,
        text_only: bool = True,
    ) -> Source:
        query: Select[tuple[Source]] = select(Source).where(Source.source_key == source_key)
        source: Source | None = self.db_session.execute(query).scalar_one_or_none()
        if source is not None:
            new_values: dict[str, object] = {
                "name": name,
                "rss_url": rss_url,
                "default_licence": default_licence,
                "default_licence_url": default_licence_url,
                "copyright_holder": copyright_holder,
                "original_language": original_language,
                "changes_notice": changes_notice,
                "rights_verified": rights_verified,
                "text_only": text_only,
            }
            changed: bool = any(getattr(source, key) != value for key, value in new_values.items())
            if changed:
                for key, value in new_values.items():
                    setattr(source, key, value)
                self.db_session.add(source)
                self.db_session.commit()
                self.db_session.refresh(source)
            return source

        source = Source(
            source_key=source_key,
            name=name,
            rss_url=rss_url,
            default_licence=default_licence,
            default_licence_url=default_licence_url,
            copyright_holder=copyright_holder,
            original_language=original_language,
            changes_notice=changes_notice,
            rights_verified=rights_verified,
            text_only=text_only,
        )
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

    def find_latest_raw_item_for_guid_prefix(
        self,
        source_id: int,
        guid_prefix: str,
    ) -> RawNewsItem | None:
        query: Select[tuple[RawNewsItem]] = (
            select(RawNewsItem)
            .where(
                RawNewsItem.source_id == source_id,
                RawNewsItem.guid.startswith(guid_prefix),
            )
            .order_by(RawNewsItem.id.desc())
            .limit(1)
        )
        return self.db_session.execute(query).scalar_one_or_none()

    def create_raw_item(
        self,
        source_id: int,
        guid: str,
        title: str,
        summary: str,
        url: str,
        published_at: datetime,
        image_url: str | None = None,
        original_language: str | None = None,
        retrieved_at: datetime | None = None,
        licence: str | None = None,
        licence_url: str | None = None,
        copyright_holder: str | None = None,
        changes_notice: str | None = None,
        source_revision: str | None = None,
        rights_verified: bool = False,
    ) -> RawNewsItem:
        item: RawNewsItem = RawNewsItem(
            source_id=source_id,
            guid=guid,
            title=title,
            summary=summary,
            url=url,
            image_url=image_url,
            published_at=published_at,
            original_language=original_language,
            retrieved_at=retrieved_at or datetime.utcnow(),
            licence=licence,
            licence_url=licence_url,
            copyright_holder=copyright_holder,
            is_translated=True,
            is_ai_summarised=True,
            changes_notice=changes_notice,
            third_party_material_excluded=True,
            source_revision=source_revision or guid,
            rights_verified=rights_verified,
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
            .options(selectinload(RawNewsItem.source))
            .order_by(RawNewsItem.published_at.desc())
        )
        return list(self.db_session.execute(query).scalars().all())

    def requeue_filtered_breaking_news(self, *, lookback: timedelta) -> int:
        """Return recently filtered raw items that match breaking-news rules back to ingested."""
        since: datetime = datetime.now(timezone.utc) - lookback
        query: Select[tuple[RawNewsItem]] = (
            select(RawNewsItem)
            .where(
                RawNewsItem.pipeline_status == PipelineStatus.FILTERED_OUT,
                RawNewsItem.created_at >= since,
            )
            .options(selectinload(RawNewsItem.source))
        )
        requeued: int = 0
        for raw_item in self.db_session.execute(query).scalars().all():
            if not is_breaking_news(raw_item.title, raw_item.summary):
                continue
            source_key: str | None = (
                raw_item.source.source_key if raw_item.source is not None else None
            )
            if not is_source_allowed_for_publication(
                source_key,
                rights_verified=raw_item.rights_verified,
                enabled_source_keys=settings.rss_enabled_source_keys,
                allow_unverified=settings.rss_allow_unverified_catalog_sources,
            ):
                continue
            raw_item.pipeline_status = PipelineStatus.INGESTED
            raw_item.relevance_score = 0.0
            raw_item.relevance_reason = ""
            self.db_session.add(raw_item)
            requeued += 1
        if requeued:
            self.db_session.commit()
        return requeued

    def requeue_filtered_official_data(self, *, lookback: timedelta) -> int:
        """Re-open recently filtered official-statistics items after source bypass is enabled."""
        since: datetime = datetime.now(timezone.utc) - lookback
        query: Select[tuple[RawNewsItem]] = (
            select(RawNewsItem)
            .join(Source, Source.id == RawNewsItem.source_id)
            .where(
                RawNewsItem.pipeline_status == PipelineStatus.FILTERED_OUT,
                RawNewsItem.created_at >= since,
                Source.source_key.in_(tuple(OFFICIAL_DATA_SOURCE_KEYS)),
            )
            .options(selectinload(RawNewsItem.source))
        )
        requeued: int = 0
        for raw_item in self.db_session.execute(query).scalars().all():
            # Do not re-open items dropped because LLM produced an empty fallback card.
            if (raw_item.relevance_reason or "").startswith("llm_validation_fallback"):
                continue
            raw_item.pipeline_status = PipelineStatus.INGESTED
            raw_item.relevance_score = 0.0
            raw_item.relevance_reason = ""
            self.db_session.add(raw_item)
            requeued += 1
        if requeued:
            self.db_session.commit()
        return requeued

    def requeue_filtered_publisher_sources(self, *, lookback: timedelta) -> int:
        """Re-open recently filtered publisher RSS after Google Test bypass is enabled."""
        if not settings.rss_allow_unverified_catalog_sources:
            return 0
        publisher_keys: tuple[str, ...] = tuple(PUBLISHER_EDITORIAL_SOURCE_KEYS)
        if not publisher_keys:
            return 0
        since: datetime = datetime.now(timezone.utc) - lookback
        query: Select[tuple[RawNewsItem]] = (
            select(RawNewsItem)
            .join(Source, Source.id == RawNewsItem.source_id)
            .where(
                RawNewsItem.pipeline_status == PipelineStatus.FILTERED_OUT,
                RawNewsItem.created_at >= since,
                Source.source_key.in_(publisher_keys),
            )
            .options(selectinload(RawNewsItem.source))
        )
        requeued: int = 0
        for raw_item in self.db_session.execute(query).scalars().all():
            if (raw_item.relevance_reason or "").startswith("llm_validation_fallback"):
                continue
            raw_item.pipeline_status = PipelineStatus.INGESTED
            raw_item.relevance_score = 0.0
            raw_item.relevance_reason = ""
            self.db_session.add(raw_item)
            requeued += 1
        if requeued:
            self.db_session.commit()
        return requeued

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

    def list_published(
        self,
        limit: int = 50,
        *,
        topic: NewsTopic | None = None,
        urgent_only: bool = False,
        positive_only: bool = False,
        cursor_id: int | None = None,
        published_at_since: datetime | None = None,
    ) -> tuple[list[ProcessedNews], bool]:
        """Return published items (newest RSS publication first) and whether another page exists.

        Optional ``cursor_id`` is the ``id`` of the last item from the previous page;
        this page continues with strictly older rows in (published_at desc, id desc) order.
        """
        fetch_limit: int = limit + 1
        base: Select[tuple[ProcessedNews]] = (
            select(ProcessedNews)
            .join(RawNewsItem, ProcessedNews.raw_item_id == RawNewsItem.id)
            .join(Source, Source.id == RawNewsItem.source_id)
            .where(
                ProcessedNews.publication_status == PipelineStatus.PUBLISHED,
                self._publication_source_filter(),
            )
            .options(selectinload(ProcessedNews.raw_item).selectinload(RawNewsItem.source))
        )
        if urgent_only:
            base = base.where(ProcessedNews.is_urgent.is_(True))
        elif positive_only:
            base = base.where(ProcessedNews.is_positive.is_(True))
        elif topic is not None:
            base = base.where(ProcessedNews.topic == topic)
        if published_at_since is not None:
            base = base.where(RawNewsItem.published_at >= published_at_since)

        if cursor_id is not None:
            anchor: ProcessedNews | None = self.get_processed_by_id_with_raw(cursor_id)
            if anchor is None or anchor.publication_status != PipelineStatus.PUBLISHED:
                return [], False
            if not self.is_processed_visible_in_feed(anchor):
                return [], False
            if urgent_only and not anchor.is_urgent:
                return [], False
            if positive_only and not anchor.is_positive:
                return [], False
            if topic is not None and anchor.topic != topic:
                return [], False
            raw_anchor: RawNewsItem | None = anchor.raw_item
            if raw_anchor is None:
                return [], False
            if published_at_since is not None and raw_anchor.published_at < published_at_since:
                return [], False

            pub_at: datetime = raw_anchor.published_at
            aid: int = anchor.id
            base = base.where(
                or_(
                    RawNewsItem.published_at < pub_at,
                    and_(RawNewsItem.published_at == pub_at, ProcessedNews.id < aid),
                )
            )

        query = base.order_by(RawNewsItem.published_at.desc(), ProcessedNews.id.desc()).limit(fetch_limit)
        rows: list[ProcessedNews] = list(self.db_session.execute(query).scalars().all())
        has_more: bool = len(rows) > limit
        if has_more:
            rows = rows[:limit]
        return rows, has_more

    def count_distinct_sources_in_cluster(self, cluster_id: int) -> int:
        stmt = (
            select(func.count(func.distinct(RawNewsItem.source_id)))
            .select_from(ClusterItem)
            .join(RawNewsItem, RawNewsItem.id == ClusterItem.raw_item_id)
            .where(ClusterItem.cluster_id == cluster_id)
        )
        result: int | None = self.db_session.execute(stmt).scalar_one_or_none()
        return int(result or 0)

    def list_published_since_with_raw(
        self,
        *,
        published_at_since: datetime,
        limit: int = 500,
    ) -> list[ProcessedNews]:
        query: Select[tuple[ProcessedNews]] = (
            select(ProcessedNews)
            .join(RawNewsItem, ProcessedNews.raw_item_id == RawNewsItem.id)
            .join(Source, Source.id == RawNewsItem.source_id)
            .where(
                and_(
                    ProcessedNews.publication_status == PipelineStatus.PUBLISHED,
                    RawNewsItem.published_at >= published_at_since,
                    self._publication_source_filter(),
                ),
            )
            .options(selectinload(ProcessedNews.raw_item).selectinload(RawNewsItem.source))
            .order_by(RawNewsItem.published_at.desc())
            .limit(limit)
        )
        return list(self.db_session.execute(query).scalars().all())

    def is_processed_visible_in_feed(self, item: ProcessedNews) -> bool:
        """Return True when a processed row may be shown on the public feed / detail API."""
        if item.publication_status != PipelineStatus.PUBLISHED:
            return False
        raw_item: RawNewsItem | None = item.raw_item
        source_key: str | None = None
        if raw_item is not None and raw_item.source is not None:
            source_key = raw_item.source.source_key
        return is_source_allowed_for_publication(
            source_key,
            rights_verified=item.rights_verified,
            enabled_source_keys=settings.rss_enabled_source_keys,
            allow_unverified=settings.rss_allow_unverified_catalog_sources,
        )

    def list_needs_review(self) -> list[ProcessedNews]:
        from app.utils.feed_period import moderation_queue_since_utc_naive

        since: datetime = moderation_queue_since_utc_naive()
        query: Select[tuple[ProcessedNews]] = (
            select(ProcessedNews)
            .where(
                and_(
                    ProcessedNews.publication_status == PipelineStatus.NEEDS_REVIEW,
                    ProcessedNews.created_at >= since,
                ),
            )
            .options(selectinload(ProcessedNews.raw_item).selectinload(RawNewsItem.source))
            .order_by(ProcessedNews.created_at.desc())
        )
        return list(self.db_session.execute(query).scalars().all())

    def get_processed_by_id(self, news_id: int) -> ProcessedNews | None:
        query: Select[tuple[ProcessedNews]] = select(ProcessedNews).where(ProcessedNews.id == news_id)
        return self.db_session.execute(query).scalar_one_or_none()

    def get_processed_by_id_with_raw(self, news_id: int) -> ProcessedNews | None:
        query: Select[tuple[ProcessedNews]] = (
            select(ProcessedNews)
            .where(ProcessedNews.id == news_id)
            .options(selectinload(ProcessedNews.raw_item).selectinload(RawNewsItem.source))
        )
        return self.db_session.execute(query).scalar_one_or_none()

    def list_telegram_digest_candidates(
        self,
        *,
        min_importance: int,
        limit: int,
        max_scan: int,
    ) -> list[ProcessedNews]:
        """Auto-published items only (no moderation approve row), for scheduled Telegram digests.

        At most one row per ``cluster_id`` (skips duplicate clusters; ``cluster_id IS NULL`` rows are
        not deduped against each other).
        """
        approve_exists = exists().where(
            ModerationEvent.processed_news_id == ProcessedNews.id,
            ModerationEvent.action == "approve",
        )
        query: Select[tuple[ProcessedNews]] = (
            select(ProcessedNews)
            .join(RawNewsItem, ProcessedNews.raw_item_id == RawNewsItem.id)
            .join(Source, Source.id == RawNewsItem.source_id)
            .where(
                ProcessedNews.publication_status == PipelineStatus.PUBLISHED,
                ProcessedNews.importance_ai_score >= min_importance,
                ProcessedNews.telegram_notified_at.is_(None),
                ProcessedNews.is_urgent.is_(False),
                ~approve_exists,
                self._publication_source_filter(),
            )
            .options(selectinload(ProcessedNews.raw_item).selectinload(RawNewsItem.source))
            .order_by(
                ProcessedNews.importance_ai_score.desc(),
                ProcessedNews.created_at.desc(),
            )
            .limit(max_scan)
        )
        rows: list[ProcessedNews] = list(self.db_session.execute(query).scalars().all())
        picked: list[ProcessedNews] = []
        seen_cluster_ids: set[int] = set()
        for row in rows:
            cid: int | None = row.cluster_id
            if cid is not None:
                if cid in seen_cluster_ids:
                    continue
                seen_cluster_ids.add(cid)
            picked.append(row)
            if len(picked) >= limit:
                break
        return picked

    def mark_telegram_notified(self, news_id: int) -> None:
        row: ProcessedNews | None = self.get_processed_by_id(news_id)
        if row is None:
            return
        row.telegram_notified_at = datetime.utcnow()
        self.db_session.add(row)
        self.db_session.commit()

    def mark_push_notified(self, news_id: int) -> None:
        row: ProcessedNews | None = self.get_processed_by_id(news_id)
        if row is None:
            return
        row.push_notified_at = datetime.utcnow()
        self.db_session.add(row)
        self.db_session.commit()

    def get_raw_item_by_id(self, raw_id: int) -> RawNewsItem | None:
        query: Select[tuple[RawNewsItem]] = (
            select(RawNewsItem).where(RawNewsItem.id == raw_id).options(selectinload(RawNewsItem.source))
        )
        return self.db_session.execute(query).scalar_one_or_none()

    def get_processed_by_raw_item_id(self, raw_item_id: int) -> ProcessedNews | None:
        query: Select[tuple[ProcessedNews]] = select(ProcessedNews).where(
            ProcessedNews.raw_item_id == raw_item_id
        )
        return self.db_session.execute(query).scalar_one_or_none()

    def get_cluster_by_id(self, cluster_id: int) -> NewsCluster | None:
        query: Select[tuple[NewsCluster]] = select(NewsCluster).where(NewsCluster.id == cluster_id)
        return self.db_session.execute(query).scalar_one_or_none()

    def update_processed_metadata(
        self,
        news_id: int,
        *,
        topic: NewsTopic | None = None,
        is_urgent: bool | None = None,
        is_positive: bool | None = None,
        user_id: int | None = None,
    ) -> ProcessedNews | None:
        """Update topic/flags for a processed item and record an audit row when values change."""
        processed: ProcessedNews | None = self.get_processed_by_id(news_id)
        if processed is None:
            return None

        changed: bool = False
        if topic is not None and processed.topic != topic:
            processed.topic = topic
            changed = True
        if is_urgent is not None and processed.is_urgent != is_urgent:
            processed.is_urgent = is_urgent
            changed = True
        if is_positive is not None and processed.is_positive != is_positive:
            processed.is_positive = is_positive
            changed = True

        if not changed:
            return processed

        self.db_session.add(processed)
        self.db_session.add(
            ModerationEvent(
                processed_news_id=processed.id,
                action="metadata_update",
                user_id=user_id,
            )
        )
        self.db_session.commit()
        self.db_session.refresh(processed)
        return processed

    def apply_moderation(
        self,
        news_id: int,
        status: PipelineStatus,
        audit_action: Literal["approve", "reject"],
        user_id: int | None = None,
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
                user_id=user_id,
            )
        )
        self.db_session.commit()
        self.db_session.refresh(processed)
        return processed
