"""Persistence for staff users and refresh tokens."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.staff_user import StaffRefreshToken, StaffUser


class StaffRepository:
    def __init__(self, db_session: Session) -> None:
        self._db: Session = db_session

    def get_by_id(self, user_id: int) -> StaffUser | None:
        q = select(StaffUser).where(StaffUser.id == user_id)
        return self._db.execute(q).scalar_one_or_none()

    def get_by_email(self, email: str) -> StaffUser | None:
        norm: str = email.strip().lower()
        q = select(StaffUser).where(StaffUser.email == norm)
        return self._db.execute(q).scalar_one_or_none()

    def create_staff_user(
        self,
        *,
        email: str,
        password_hash: str,
        can_moderate: bool = True,
        can_run_pipeline: bool = True,
    ) -> StaffUser:
        user = StaffUser(
            email=email.strip().lower(),
            password_hash=password_hash,
            is_active=True,
            can_moderate=can_moderate,
            can_run_pipeline=can_run_pipeline,
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def store_refresh_token(self, *, user_id: int, token_hash: str, expires_at: datetime) -> StaffRefreshToken:
        row = StaffRefreshToken(
            staff_user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def get_active_refresh_by_hash(self, token_hash: str) -> StaffRefreshToken | None:
        q = select(StaffRefreshToken).where(
            StaffRefreshToken.token_hash == token_hash,
            StaffRefreshToken.revoked_at.is_(None),
        )
        row: StaffRefreshToken | None = self._db.execute(q).scalar_one_or_none()
        if row is None:
            return None
        if row.expires_at.replace(tzinfo=None) < datetime.utcnow():
            return None
        return row

    def revoke_refresh(self, refresh_id: int) -> None:
        row = self._db.get(StaffRefreshToken, refresh_id)
        if row is None:
            return
        row.revoked_at = datetime.utcnow()
        self._db.add(row)
        self._db.commit()
