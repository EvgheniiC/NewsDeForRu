"""Login, refresh, logout, ``/me`` for staff operators."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps.auth_staff import get_current_staff_user
from app.core.config import settings
from app.core.database import get_db_session
from app.models.staff_user import StaffUser
from app.repositories.staff_repository import StaffRepository
from app.schemas.auth_staff import LoginRequest, LogoutRequest, RefreshRequest, StaffMeResponse, StaffTokenPairResponse
from app.services.passwords import verify_password
from app.services.staff_tokens import issue_access_token, new_refresh_plain, refresh_token_hash_hex

router: APIRouter = APIRouter(prefix="/auth", tags=["auth"])
_logger: logging.Logger = logging.getLogger(__name__)


def _issue_tokens_for_user(repo: StaffRepository, user_id: int) -> StaffTokenPairResponse:
    access_token, _expires = issue_access_token(
        user_id=user_id,
        secret=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=settings.jwt_access_expire_minutes),
        audience="staff",
    )
    refresh_plain: str = new_refresh_plain()
    hashed: str = refresh_token_hash_hex(refresh_plain)
    refresh_expires = timedelta(days=settings.jwt_refresh_expire_days)
    expire_at_naive = datetime.utcnow() + refresh_expires
    repo.store_refresh_token(user_id=user_id, token_hash=hashed, expires_at=expire_at_naive)
    return StaffTokenPairResponse(access_token=access_token, refresh_token=refresh_plain)


@router.post("/login", response_model=StaffTokenPairResponse)
def staff_login(payload: LoginRequest, db_session: Session = Depends(get_db_session)) -> StaffTokenPairResponse:
    repo = StaffRepository(db_session)
    user: StaffUser | None = repo.get_by_email(payload.email)
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    response: StaffTokenPairResponse = _issue_tokens_for_user(repo, user.id)
    _logger.info("staff_login_success user_id=%s", user.id)
    return response


@router.post("/refresh", response_model=StaffTokenPairResponse)
def staff_refresh(payload: RefreshRequest, db_session: Session = Depends(get_db_session)) -> StaffTokenPairResponse:
    repo = StaffRepository(db_session)
    hashed: str = refresh_token_hash_hex(payload.refresh_token)
    row = repo.get_active_refresh_by_hash(hashed)
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    owner: StaffUser | None = repo.get_by_id(row.staff_user_id)
    if owner is None or not owner.is_active:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    repo.revoke_refresh(row.id)
    tokens: StaffTokenPairResponse = _issue_tokens_for_user(repo, owner.id)
    _logger.info("staff_refresh_success user_id=%s", owner.id)
    return tokens


@router.post("/logout")
def staff_logout(payload: LogoutRequest, db_session: Session = Depends(get_db_session)) -> dict[str, str]:
    repo = StaffRepository(db_session)
    hashed: str = refresh_token_hash_hex(payload.refresh_token)
    row = repo.get_active_refresh_by_hash(hashed)
    if row is not None:
        repo.revoke_refresh(row.id)
    return {"detail": "ok"}


@router.get("/me", response_model=StaffMeResponse)
def staff_me(current: StaffUser = Depends(get_current_staff_user)) -> StaffMeResponse:
    return StaffMeResponse(
        id=current.id,
        email=current.email,
        can_moderate=current.can_moderate,
        can_run_pipeline=current.can_run_pipeline,
    )
