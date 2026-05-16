"""Operators (staff accounts) — moderation and manual pipeline."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StaffUser(Base):
    __tablename__ = "staff_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_moderate: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_run_pipeline: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    refresh_tokens: Mapped[list["StaffRefreshToken"]] = relationship(
        back_populates="staff_user",
        cascade="all, delete-orphan",
    )


class StaffRefreshToken(Base):
    __tablename__ = "staff_refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    staff_user_id: Mapped[int] = mapped_column(
        ForeignKey("staff_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)

    staff_user: Mapped[StaffUser] = relationship(back_populates="refresh_tokens")
