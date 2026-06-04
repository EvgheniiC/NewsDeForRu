"""Register, login, refresh, logout, ``/me`` for unified app accounts."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps.auth import JWT_AUDIENCE_USER, get_current_user
from app.core.config import settings
from app.core.database import get_db_session
from app.models.app_user import AppUser
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    TokenPairResponse,
)
from app.services.password_reset_service import request_password_reset, reset_password_with_token
from app.services.passwords import hash_password, verify_password
from app.services.staff_tokens import issue_access_token, new_refresh_plain, refresh_token_hash_hex

router: APIRouter = APIRouter(prefix="/auth", tags=["auth"])
_logger: logging.Logger = logging.getLogger(__name__)


def _issue_tokens_for_user(repo: UserRepository, user_id: int) -> TokenPairResponse:
    access_token, _expires = issue_access_token(
        user_id=user_id,
        secret=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=settings.jwt_access_expire_minutes),
        audience=JWT_AUDIENCE_USER,
    )
    refresh_plain: str = new_refresh_plain()
    hashed: str = refresh_token_hash_hex(refresh_plain)
    refresh_expires = timedelta(days=settings.jwt_refresh_expire_days)
    expire_at_naive = datetime.utcnow() + refresh_expires
    repo.store_refresh_token(user_id=user_id, token_hash=hashed, expires_at=expire_at_naive)
    return TokenPairResponse(access_token=access_token, refresh_token=refresh_plain)


@router.post("/register", response_model=TokenPairResponse)
def register(
    payload: RegisterRequest,
    db_session: Session = Depends(get_db_session),
) -> TokenPairResponse:
    repo = UserRepository(db_session)
    if repo.get_by_email(str(payload.email)) is not None:
        raise HTTPException(status_code=409, detail="Email is already registered")
    pw_hash: str = hash_password(payload.password)
    user: AppUser = repo.create_reader(email=str(payload.email), password_hash=pw_hash)
    tokens: TokenPairResponse = _issue_tokens_for_user(repo, user.id)
    _logger.info("user_register_success user_id=%s", user.id)
    return tokens


@router.post("/login", response_model=TokenPairResponse)
def login(payload: LoginRequest, db_session: Session = Depends(get_db_session)) -> TokenPairResponse:
    repo = UserRepository(db_session)
    user: AppUser | None = repo.get_by_email(payload.email)
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    response: TokenPairResponse = _issue_tokens_for_user(repo, user.id)
    _logger.info("user_login_success user_id=%s", user.id)
    return response


@router.post("/refresh", response_model=TokenPairResponse)
def refresh(payload: RefreshRequest, db_session: Session = Depends(get_db_session)) -> TokenPairResponse:
    repo = UserRepository(db_session)
    hashed: str = refresh_token_hash_hex(payload.refresh_token)
    row = repo.get_active_refresh_by_hash(hashed)
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    owner: AppUser | None = repo.get_by_id(row.user_id)
    if owner is None or not owner.is_active:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    repo.revoke_refresh(row.id)
    tokens: TokenPairResponse = _issue_tokens_for_user(repo, owner.id)
    _logger.info("user_refresh_success user_id=%s", owner.id)
    return tokens


@router.post("/logout")
def logout(payload: LogoutRequest, db_session: Session = Depends(get_db_session)) -> dict[str, str]:
    repo = UserRepository(db_session)
    hashed: str = refresh_token_hash_hex(payload.refresh_token)
    row = repo.get_active_refresh_by_hash(hashed)
    if row is not None:
        repo.revoke_refresh(row.id)
    return {"detail": "ok"}


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    db_session: Session = Depends(get_db_session),
) -> ForgotPasswordResponse:
    result = request_password_reset(db_session, str(payload.email))
    return ForgotPasswordResponse(detail=result.message, dev_reset_link=result.dev_reset_link)


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(
    payload: ResetPasswordRequest,
    db_session: Session = Depends(get_db_session),
) -> ResetPasswordResponse:
    try:
        reset_password_with_token(db_session, payload.token, payload.new_password)
    except ValueError as exc:
        code: str = str(exc)
        if code == "expired_token":
            raise HTTPException(status_code=400, detail="Reset link has expired. Request a new one.") from exc
        raise HTTPException(status_code=400, detail="Invalid or already used reset link.") from exc
    return ResetPasswordResponse(detail="Password updated. You can sign in with the new password.")


@router.get("/me", response_model=MeResponse)
def me(current: AppUser = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        id=current.id,
        email=current.email,
        role=current.role,
        can_moderate=current.can_moderate,
        can_run_pipeline=current.can_run_pipeline,
    )
