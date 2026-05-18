"""Resolve reader Bearer JWT → ``ReaderUser``."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db_session
from app.models.reader_user import ReaderUser
from app.repositories.reader_repository import ReaderRepository
from app.services.staff_tokens import decode_access_token

_bearer_optional = HTTPBearer(auto_error=False)


def get_current_reader_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_optional),
    ],
    db_session: Annotated[Session, Depends(get_db_session)],
) -> ReaderUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id: int = decode_access_token(
        credentials.credentials,
        secret=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expected_audience="reader",
    )
    repo = ReaderRepository(db_session)
    user: ReaderUser | None = repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account inactive")
    return user
