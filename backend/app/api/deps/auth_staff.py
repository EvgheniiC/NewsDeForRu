"""Dependencies: resolve staff Bearer token → ``StaffUser``."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db_session
from app.models.staff_user import StaffUser
from app.repositories.staff_repository import StaffRepository
from app.services.staff_tokens import decode_access_subject

_bearer_optional = HTTPBearer(auto_error=False)


def get_current_staff_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_optional),
    ],
    db_session: Annotated[Session, Depends(get_db_session)],
) -> StaffUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id: int = decode_access_subject(
        credentials.credentials,
        secret=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    repo = StaffRepository(db_session)
    user: StaffUser | None = repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account inactive")
    return user


def require_staff_moderator(
    staff: Annotated[StaffUser, Depends(get_current_staff_user)],
) -> StaffUser:
    if not staff.can_moderate:
        raise HTTPException(status_code=403, detail="Moderation is not permitted for this account")
    return staff


def require_staff_pipeline_runner(
    staff: Annotated[StaffUser, Depends(get_current_staff_user)],
) -> StaffUser:
    if not staff.can_run_pipeline:
        raise HTTPException(status_code=403, detail="Pipeline runs are not permitted for this account")
    return staff
