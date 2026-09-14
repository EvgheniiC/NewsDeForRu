"""Authenticated sync of useful/saved and read news."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.core.database import get_db_session
from app.models.app_user import AppUser
from app.repositories.user_library_repository import UserLibraryRepository
from app.schemas.user_library import LibraryGetResponse, LibraryPutRequest, LibraryPutResponse

router: APIRouter = APIRouter(prefix="/users/me/library", tags=["user-library"])


@router.get("", response_model=LibraryGetResponse)
def get_library(
    current: AppUser = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
) -> LibraryGetResponse:
    repo = UserLibraryRepository(db_session)
    response = LibraryGetResponse(saved=repo.list_saved(current.id), read=repo.list_read(current.id))
    repo.commit()
    return response


@router.put("", response_model=LibraryPutResponse)
def put_library(
    payload: LibraryPutRequest,
    current: AppUser = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
) -> LibraryPutResponse:
    repo = UserLibraryRepository(db_session)
    skipped_saved: list[int] = repo.apply_saved_deltas(current.id, payload.saved)
    skipped_read: list[int] = repo.apply_read_upserts(current.id, payload.read)
    skipped: list[int] = []
    seen: set[int] = set()
    for news_id in skipped_saved + skipped_read:
        if news_id in seen:
            continue
        seen.add(news_id)
        skipped.append(news_id)
    saved_count: int = len(repo.list_saved(current.id))
    read_count: int = len(repo.list_read(current.id))
    repo.commit()
    return LibraryPutResponse(
        saved_count=saved_count,
        read_count=read_count,
        skipped_news_ids=skipped,
    )
