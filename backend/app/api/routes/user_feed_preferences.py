"""Authenticated feed topic choices."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.core.database import get_db_session
from app.models.app_user import AppUser
from app.repositories.user_feed_preference_repository import UserFeedPreferenceRepository
from app.schemas.user_feed_preference import FeedPreferencesBody

router: APIRouter = APIRouter(prefix="/users/me/feed-preferences", tags=["feed-preferences"])


@router.get("", response_model=FeedPreferencesBody)
def get_feed_preferences(
    current: AppUser = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
) -> FeedPreferencesBody:
    repo: UserFeedPreferenceRepository = UserFeedPreferenceRepository(db_session)
    return repo.get_preferences(current.id)


@router.put("", response_model=FeedPreferencesBody)
def put_feed_preferences(
    payload: FeedPreferencesBody,
    current: AppUser = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
) -> FeedPreferencesBody:
    repo: UserFeedPreferenceRepository = UserFeedPreferenceRepository(db_session)
    saved: FeedPreferencesBody = repo.save_preferences(current.id, payload)
    repo.commit()
    return saved
