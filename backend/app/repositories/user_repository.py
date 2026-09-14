"""Persistence for unified app users and refresh tokens."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models.app_user import ADMIN_ROLE, READER_ROLE, AppRefreshToken, AppUser
from app.models.email_verification_token import EmailVerificationToken
from app.models.news import ModerationEvent
from app.models.password_reset_token import PasswordResetToken
from app.repositories.user_library_repository import UserLibraryRepository


class UserRepository:
    def __init__(self, db_session: Session) -> None:
        self._db: Session = db_session

    def get_by_id(self, user_id: int) -> AppUser | None:
        q = select(AppUser).where(AppUser.id == user_id)
        return self._db.execute(q).scalar_one_or_none()

    def get_by_email(self, email: str) -> AppUser | None:
        norm: str = email.strip().lower()
        q = select(AppUser).where(AppUser.email == norm)
        return self._db.execute(q).scalar_one_or_none()

    def create_reader(self, *, email: str, password_hash: str) -> AppUser:
        user = AppUser(
            email=email.strip().lower(),
            password_hash=password_hash,
            is_active=True,
            role=READER_ROLE,
            can_moderate=False,
            can_run_pipeline=False,
            email_verified_at=None,
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def create_staff_user(
        self,
        *,
        email: str,
        password_hash: str,
        can_moderate: bool = True,
        can_run_pipeline: bool = True,
    ) -> AppUser:
        now: datetime = datetime.utcnow()
        user = AppUser(
            email=email.strip().lower(),
            password_hash=password_hash,
            is_active=True,
            role=ADMIN_ROLE,
            can_moderate=can_moderate,
            can_run_pipeline=can_run_pipeline,
            email_verified_at=now,
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def update_password(self, user: AppUser, *, password_hash: str) -> AppUser:
        user.password_hash = password_hash
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def grant_staff_privileges(
        self,
        user: AppUser,
        *,
        can_moderate: bool,
        can_run_pipeline: bool,
    ) -> AppUser:
        user.role = ADMIN_ROLE
        user.can_moderate = can_moderate
        user.can_run_pipeline = can_run_pipeline
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def store_refresh_token(self, *, user_id: int, token_hash: str, expires_at: datetime) -> AppRefreshToken:
        row = AppRefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def get_active_refresh_by_hash(self, token_hash: str) -> AppRefreshToken | None:
        q = select(AppRefreshToken).where(
            AppRefreshToken.token_hash == token_hash,
            AppRefreshToken.revoked_at.is_(None),
        )
        row: AppRefreshToken | None = self._db.execute(q).scalar_one_or_none()
        if row is None:
            return None
        if row.expires_at.replace(tzinfo=None) < datetime.utcnow():
            return None
        return row

    def revoke_refresh(self, refresh_id: int) -> None:
        row = self._db.get(AppRefreshToken, refresh_id)
        if row is None:
            return
        row.revoked_at = datetime.utcnow()
        self._db.add(row)
        self._db.commit()

    def delete_user(self, user: AppUser) -> None:
        """Remove the account and related auth rows; anonymize moderation audit."""
        user_id: int = user.id
        self._db.execute(delete(AppRefreshToken).where(AppRefreshToken.user_id == user_id))
        self._db.execute(delete(EmailVerificationToken).where(EmailVerificationToken.user_id == user_id))
        self._db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id))
        UserLibraryRepository(self._db).delete_for_user(user_id)
        self._db.execute(
            update(ModerationEvent).where(ModerationEvent.user_id == user_id).values(user_id=None)
        )
        self._db.expire(user, ["refresh_tokens"])
        self._db.delete(user)
        self._db.commit()
