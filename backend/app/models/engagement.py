"""User engagement/analytics rows (anonymous UUID + processed news IDs)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.news import ProcessedNews


class EngagementEventType(StrEnum):
    USEFUL = "useful"
    OPEN_PREVIEW = "open_preview"
    OPEN_SOURCE = "open_source"
    READ_COMPLETE_PREVIEW = "read_complete_preview"
    READ_COMPLETE_ARTICLE = "read_complete_article"
    NAVIGATE_NEXT = "navigate_next"


class UserEngagementEvent(Base):
    __tablename__ = "user_engagement_events"
    __table_args__ = (
        UniqueConstraint("client_event_id", name="uq_user_engagement_events_client_event_id"),
        Index("ix_user_engagement_anon_news_type", "anonymous_user_id", "processed_news_id", "event_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    anonymous_user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    processed_news_id: Mapped[int] = mapped_column(
        ForeignKey("processed_news.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    client_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    processed_news: Mapped["ProcessedNews"] = relationship(back_populates="user_engagement_events")
