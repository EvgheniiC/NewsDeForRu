from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.engagement import UserEngagementEvent


class PipelineStatus(StrEnum):
    INGESTED = "ingested"
    FILTERED_OUT = "filtered_out"
    CLUSTERED = "clustered"
    PROCESSED = "processed"
    NEEDS_REVIEW = "needs_review"
    PUBLISHED = "published"


class UserRole(StrEnum):
    OWNER = "owner"
    TENANT = "tenant"
    BUYER = "buyer"


class NewsTopic(StrEnum):
    POLITICS = "politics"
    ECONOMY = "economy"
    LIFE = "life"


class FeedPeriod(StrEnum):
    """Calendar windows in Europe/Berlin for list filters."""

    TODAY = "today"
    LAST_3_DAYS = "last_3_days"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"


class ImpactPresentation(StrEnum):
    """How impact-on-reader is shown: three angles, one block, or hidden."""

    MULTI = "multi"
    SINGLE = "single"
    NONE = "none"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    rss_url: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class RawNewsItem(Base):
    __tablename__ = "raw_news_items"
    __table_args__ = (UniqueConstraint("source_id", "guid", name="uq_raw_news_source_guid"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    guid: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    pipeline_status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus), default=PipelineStatus.INGESTED, nullable=False
    )
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    relevance_reason: Mapped[str] = mapped_column(String(256), default="", nullable=False)
    cluster_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    source: Mapped[Source] = relationship()
    cluster_items: Mapped[list["ClusterItem"]] = relationship(back_populates="raw_item")


class ProcessedNews(Base):
    __tablename__ = "processed_news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    raw_item_id: Mapped[int] = mapped_column(ForeignKey("raw_news_items.id"), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    one_sentence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    plain_language: Mapped[str] = mapped_column(Text, nullable=False)
    impact_presentation: Mapped[ImpactPresentation] = mapped_column(
        Enum(
            ImpactPresentation,
            native_enum=False,
            length=16,
            values_callable=lambda t: [m.value for m in t],
        ),
        default=ImpactPresentation.MULTI,
        nullable=False,
    )
    impact_unified: Mapped[str] = mapped_column(Text, default="", nullable=False)
    impact_owner: Mapped[str] = mapped_column(Text, nullable=False)
    impact_tenant: Mapped[str] = mapped_column(Text, nullable=False)
    impact_buyer: Mapped[str] = mapped_column(Text, nullable=False)
    action_items: Mapped[str] = mapped_column(Text, nullable=False)
    bonus_block: Mapped[str] = mapped_column(Text, default="", nullable=False)
    spoiler: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cluster_id: Mapped[int | None] = mapped_column(ForeignKey("news_clusters.id"), nullable=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    publication_status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus), default=PipelineStatus.NEEDS_REVIEW, nullable=False
    )
    read_time_minutes: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    topic: Mapped[NewsTopic] = mapped_column(
        Enum(
            NewsTopic,
            native_enum=False,
            length=32,
            values_callable=lambda t: [m.value for m in t],
        ),
        default=NewsTopic.LIFE,
        nullable=False,
    )
    is_urgent: Mapped[bool] = mapped_column(default=False, nullable=False)
    importance_ai_score: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    raw_item: Mapped[RawNewsItem] = relationship()
    cluster: Mapped["NewsCluster | None"] = relationship(back_populates="processed_items")
    moderation_events: Mapped[list["ModerationEvent"]] = relationship(
        back_populates="processed_news",
    )
    user_engagement_events: Mapped[list["UserEngagementEvent"]] = relationship(
        back_populates="processed_news",
    )


class ModerationEvent(Base):
    __tablename__ = "moderation_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    processed_news_id: Mapped[int] = mapped_column(
        ForeignKey("processed_news.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    processed_news: Mapped[ProcessedNews] = relationship(back_populates="moderation_events")


class NewsCluster(Base):
    __tablename__ = "news_clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cluster_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    canonical_title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    centroid_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    centroid_embedding_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    items: Mapped[list["ClusterItem"]] = relationship(back_populates="cluster")
    processed_items: Mapped[list[ProcessedNews]] = relationship(back_populates="cluster")


class ClusterItem(Base):
    __tablename__ = "cluster_items"
    __table_args__ = (
        UniqueConstraint("cluster_id", "raw_item_id", name="uq_cluster_item_pair"),
        UniqueConstraint("raw_item_id", name="uq_cluster_item_raw"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("news_clusters.id"), nullable=False, index=True)
    raw_item_id: Mapped[int] = mapped_column(ForeignKey("raw_news_items.id"), nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    cluster: Mapped[NewsCluster] = relationship(back_populates="items")
    raw_item: Mapped[RawNewsItem] = relationship(back_populates="cluster_items")
