from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


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


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    rss_url: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class RawNewsItem(Base):
    __tablename__ = "raw_news_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    guid: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    pipeline_status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus), default=PipelineStatus.INGESTED, nullable=False
    )
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    relevance_reason: Mapped[str] = mapped_column(String(256), default="", nullable=False)
    cluster_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    source: Mapped[Source] = relationship()


class ProcessedNews(Base):
    __tablename__ = "processed_news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    raw_item_id: Mapped[int] = mapped_column(ForeignKey("raw_news_items.id"), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    one_sentence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    plain_language: Mapped[str] = mapped_column(Text, nullable=False)
    impact_owner: Mapped[str] = mapped_column(Text, nullable=False)
    impact_tenant: Mapped[str] = mapped_column(Text, nullable=False)
    impact_buyer: Mapped[str] = mapped_column(Text, nullable=False)
    action_items: Mapped[str] = mapped_column(Text, nullable=False)
    bonus_block: Mapped[str] = mapped_column(Text, default="", nullable=False)
    spoiler: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    publication_status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus), default=PipelineStatus.NEEDS_REVIEW, nullable=False
    )
    read_time_minutes: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    raw_item: Mapped[RawNewsItem] = relationship()
