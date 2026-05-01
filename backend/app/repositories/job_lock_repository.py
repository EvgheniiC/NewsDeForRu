"""DB-backed mutex for scheduled jobs (used when PostgreSQL advisory locks are unavailable)."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import or_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.job_lock import AppJobLock


class JobLockRepository:
    def __init__(self, db_session: Session) -> None:
        self.db_session: Session = db_session

    def try_acquire(self, job_key: str, holder: str, ttl_seconds: int) -> bool:
        """Return True if this process became the lock owner until ``now + ttl_seconds``."""
        self._ensure_row(job_key)
        now: datetime = datetime.utcnow()
        until: datetime = now + timedelta(seconds=ttl_seconds)
        stmt = (
            update(AppJobLock)
            .where(
                AppJobLock.job_key == job_key,
                or_(AppJobLock.locked_until.is_(None), AppJobLock.locked_until <= now),
            )
            .values(locked_until=until, holder=holder[:128])
        )
        result = self.db_session.execute(stmt)
        self.db_session.commit()
        return result.rowcount == 1

    def release(self, job_key: str) -> None:
        stmt = (
            update(AppJobLock)
            .where(AppJobLock.job_key == job_key)
            .values(locked_until=None, holder="")
        )
        self.db_session.execute(stmt)
        self.db_session.commit()

    def _ensure_row(self, job_key: str) -> None:
        row: AppJobLock | None = self.db_session.get(AppJobLock, job_key)
        if row is not None:
            return
        self.db_session.add(AppJobLock(job_key=job_key, locked_until=None, holder=""))
        try:
            self.db_session.commit()
        except IntegrityError:
            self.db_session.rollback()
