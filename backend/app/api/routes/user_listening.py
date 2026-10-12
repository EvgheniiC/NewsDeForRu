"""Authenticated sync of the listen queue and playback progress."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.core.database import get_db_session
from app.models.app_user import AppUser
from app.repositories.user_listening_repository import UserListeningRepository
from app.schemas.user_listening import ListeningPutResponse, ListeningStateBody

router: APIRouter = APIRouter(prefix="/users/me/listening", tags=["user-listening"])


@router.get("", response_model=ListeningStateBody)
def get_listening(
    current: AppUser = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
) -> ListeningStateBody:
    repo: UserListeningRepository = UserListeningRepository(db_session)
    return repo.get_state(current.id)


@router.put("", response_model=ListeningPutResponse)
def put_listening(
    payload: ListeningStateBody,
    current: AppUser = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
) -> ListeningPutResponse:
    repo: UserListeningRepository = UserListeningRepository(db_session)
    response: ListeningPutResponse = repo.save_state(current.id, payload)
    if response.applied:
        repo.commit()
    return response
