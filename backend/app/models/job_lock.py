"""Lightweight DB row for multi-instance mutex (SQLite / non-advisory backends)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AppJobLock(Base):
    __tablename__ = "app_job_locks"

    job_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    holder: Mapped[str] = mapped_column(String(128), default="", nullable=False)
