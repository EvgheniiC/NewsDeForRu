"""Persist the cover tags a user wants first in the feed."""

from __future__ import annotations

import time

from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.news import CoverTag
from app.models.user_feed_preference import UserFeedPreference
from app.schemas.user_feed_preference import FeedPreferencesBody


class UserFeedPreferenceRepository:
    def __init__(self, db_session: Session) -> None:
        self._db: Session = db_session

    def commit(self) -> None:
        self._db.commit()

    def delete_for_user(self, user_id: int) -> None:
        self._db.execute(delete(UserFeedPreference).where(UserFeedPreference.user_id == user_id))

    def get_preferences(self, user_id: int) -> FeedPreferencesBody:
        row: UserFeedPreference | None = self._row(user_id)
        if row is None:
            return FeedPreferencesBody()
        return self._parse(row.interests_json)

    def interest_tags(self, user_id: int) -> frozenset[CoverTag]:
        return frozenset(self.get_preferences(user_id).interests)

    def save_preferences(self, user_id: int, incoming: FeedPreferencesBody) -> FeedPreferencesBody:
        row: UserFeedPreference | None = self._row(user_id)
        payload: str = incoming.model_dump_json()
        updated_at: int = int(time.time() * 1000)
        if row is None:
            self._db.add(
                UserFeedPreference(user_id=user_id, interests_json=payload, updated_at=updated_at)
            )
        else:
            row.interests_json = payload
            row.updated_at = updated_at
            self._db.add(row)
        return incoming

    def _row(self, user_id: int) -> UserFeedPreference | None:
        return self._db.scalar(select(UserFeedPreference).where(UserFeedPreference.user_id == user_id))

    def _parse(self, raw: str) -> FeedPreferencesBody:
        try:
            return FeedPreferencesBody.model_validate_json(raw)
        except ValidationError:
            return FeedPreferencesBody()
