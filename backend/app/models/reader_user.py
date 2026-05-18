"""Registered readers (optional app accounts; separate from staff operators)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ReaderUser(Base):
    __tablename__ = "reader_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    refresh_tokens: Mapped[list["ReaderRefreshToken"]] = relationship(
        back_populates="reader_user",
        cascade="all, delete-orphan",
    )


class ReaderRefreshToken(Base):
    __tablename__ = "reader_refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reader_user_id: Mapped[int] = mapped_column(
        ForeignKey("reader_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)

    reader_user: Mapped[ReaderUser] = relationship(back_populates="refresh_tokens")
