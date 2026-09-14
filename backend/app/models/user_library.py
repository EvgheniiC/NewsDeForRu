"""Per-account saved (useful) and read news, synced across devices."""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserSavedNews(Base):
    """Useful/saved marks. ``removed_at`` is a tombstone for last-write-wins unmarks."""

    __tablename__ = "user_saved_news"
    __table_args__ = (UniqueConstraint("user_id", "processed_news_id", name="uq_user_saved_news_user_news"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    processed_news_id: Mapped[int] = mapped_column(
        ForeignKey("processed_news.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    marked_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    removed_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True, default=None)


class UserReadNews(Base):
    __tablename__ = "user_read_news"
    __table_args__ = (UniqueConstraint("user_id", "processed_news_id", name="uq_user_read_news_user_news"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    processed_news_id: Mapped[int] = mapped_column(
        ForeignKey("processed_news.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    read_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
