"""Chosen feed topics for one account."""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserFeedPreference(Base):
    """One JSON document per user: selected illustration tags, in choice order."""

    __tablename__ = "user_feed_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    interests_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
