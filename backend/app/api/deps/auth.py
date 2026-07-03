"""Resolve Bearer JWT → ``AppUser`` and enforce editorial permissions."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db_session
from app.models.app_user import AppUser
from app.repositories.user_repository import UserRepository
from app.services.staff_tokens import decode_access_token

_bearer_optional = HTTPBearer(auto_error=False)

JWT_AUDIENCE_USER: str = "user"


def _resolve_user_from_credentials(
    credentials: HTTPAuthorizationCredentials | None,
    db_session: Session,
) -> AppUser | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        user_id: int = decode_access_token(
            credentials.credentials,
            secret=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            expected_audience=JWT_AUDIENCE_USER,
        )
    except HTTPException:
        return None
    repo = UserRepository(db_session)
    user: AppUser | None = repo.get_by_id(user_id)
    if user is None or not user.is_active:
        return None
    return user


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_optional),
    ],
    db_session: Annotated[Session, Depends(get_db_session)],
) -> AppUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id: int = decode_access_token(
        credentials.credentials,
        secret=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expected_audience=JWT_AUDIENCE_USER,
    )
    repo = UserRepository(db_session)
    user: AppUser | None = repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account inactive")
    return user


def get_optional_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_optional),
    ],
    db_session: Annotated[Session, Depends(get_db_session)],
) -> AppUser | None:
    return _resolve_user_from_credentials(credentials, db_session)


def require_moderator(
    user: Annotated[AppUser, Depends(get_current_user)],
) -> AppUser:
    if not user.can_moderate:
        raise HTTPException(status_code=403, detail="Moderation is not permitted for this account")
    return user


def require_pipeline_runner(
    user: Annotated[AppUser, Depends(get_current_user)],
) -> AppUser:
    if not user.can_run_pipeline:
        raise HTTPException(status_code=403, detail="Pipeline runs are not permitted for this account")
    return user
