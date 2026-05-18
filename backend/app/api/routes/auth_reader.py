"""Register, login, refresh, logout, ``/me`` for reader (app) accounts."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps.auth_reader import get_current_reader_user
from app.core.config import settings
from app.core.database import get_db_session
from app.models.reader_user import ReaderUser
from app.repositories.reader_repository import ReaderRepository
from app.schemas.auth_reader import (
    ReaderLoginRequest,
    ReaderLogoutRequest,
    ReaderMeResponse,
    ReaderRefreshRequest,
    ReaderRegisterRequest,
    ReaderTokenPairResponse,
)
from app.services.passwords import hash_password, verify_password
from app.services.staff_tokens import issue_access_token, new_refresh_plain, refresh_token_hash_hex

router: APIRouter = APIRouter(prefix="/reader/auth", tags=["reader-auth"])
_logger: logging.Logger = logging.getLogger(__name__)


def _issue_tokens_for_reader(repo: ReaderRepository, user_id: int) -> ReaderTokenPairResponse:
    access_token, _expires = issue_access_token(
        user_id=user_id,
        secret=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=settings.jwt_access_expire_minutes),
        audience="reader",
    )
    refresh_plain: str = new_refresh_plain()
    hashed: str = refresh_token_hash_hex(refresh_plain)
    refresh_expires = timedelta(days=settings.jwt_refresh_expire_days)
    expire_at_naive = datetime.utcnow() + refresh_expires
    repo.store_refresh_token(user_id=user_id, token_hash=hashed, expires_at=expire_at_naive)
    return ReaderTokenPairResponse(access_token=access_token, refresh_token=refresh_plain)


@router.post("/register", response_model=ReaderTokenPairResponse)
def reader_register(
    payload: ReaderRegisterRequest,
    db_session: Session = Depends(get_db_session),
) -> ReaderTokenPairResponse:
    repo = ReaderRepository(db_session)
    if repo.get_by_email(str(payload.email)) is not None:
        raise HTTPException(status_code=409, detail="Email is already registered")
    pw_hash: str = hash_password(payload.password)
    user: ReaderUser = repo.create_reader(email=str(payload.email), password_hash=pw_hash)
    tokens: ReaderTokenPairResponse = _issue_tokens_for_reader(repo, user.id)
    _logger.info("reader_register_success user_id=%s", user.id)
    return tokens


@router.post("/login", response_model=ReaderTokenPairResponse)
def reader_login(payload: ReaderLoginRequest, db_session: Session = Depends(get_db_session)) -> ReaderTokenPairResponse:
    repo = ReaderRepository(db_session)
    user: ReaderUser | None = repo.get_by_email(str(payload.email))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    response: ReaderTokenPairResponse = _issue_tokens_for_reader(repo, user.id)
    _logger.info("reader_login_success user_id=%s", user.id)
    return response


@router.post("/refresh", response_model=ReaderTokenPairResponse)
def reader_refresh(
    payload: ReaderRefreshRequest,
    db_session: Session = Depends(get_db_session),
) -> ReaderTokenPairResponse:
    repo = ReaderRepository(db_session)
    hashed: str = refresh_token_hash_hex(payload.refresh_token)
    row = repo.get_active_refresh_by_hash(hashed)
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    owner: ReaderUser | None = repo.get_by_id(row.reader_user_id)
    if owner is None or not owner.is_active:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    repo.revoke_refresh(row.id)
    tokens: ReaderTokenPairResponse = _issue_tokens_for_reader(repo, owner.id)
    _logger.info("reader_refresh_success user_id=%s", owner.id)
    return tokens


@router.post("/logout")
def reader_logout(payload: ReaderLogoutRequest, db_session: Session = Depends(get_db_session)) -> dict[str, str]:
    repo = ReaderRepository(db_session)
    hashed: str = refresh_token_hash_hex(payload.refresh_token)
    row = repo.get_active_refresh_by_hash(hashed)
    if row is not None:
        repo.revoke_refresh(row.id)
    return {"detail": "ok"}


@router.get("/me", response_model=ReaderMeResponse)
def reader_me(current: ReaderUser = Depends(get_current_reader_user)) -> ReaderMeResponse:
    return ReaderMeResponse(id=current.id, email=current.email)
