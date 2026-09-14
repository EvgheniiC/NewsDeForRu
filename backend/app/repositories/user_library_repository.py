"""Persist per-user saved/read news with last-write-wins timestamps."""

from __future__ import annotations

import time

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.user_library import UserReadNews, UserSavedNews
from app.repositories.engagement_repository import find_existing_news_ids
from app.schemas.user_library import LibraryReadItem, LibrarySavedDelta, LibrarySavedItem

USEFUL_RETENTION_MS: int = 60 * 24 * 60 * 60 * 1000
READ_RETENTION_MS: int = 30 * 24 * 60 * 60 * 1000


def _now_ms() -> int:
    return int(time.time() * 1000)


class UserLibraryRepository:
    def __init__(self, db_session: Session) -> None:
        self._db: Session = db_session

    def delete_for_user(self, user_id: int) -> None:
        self._db.execute(delete(UserSavedNews).where(UserSavedNews.user_id == user_id))
        self._db.execute(delete(UserReadNews).where(UserReadNews.user_id == user_id))

    def list_saved(self, user_id: int) -> list[LibrarySavedItem]:
        cutoff: int = _now_ms() - USEFUL_RETENTION_MS
        self._purge_expired_saved(user_id, cutoff)
        rows: list[UserSavedNews] = list(
            self._db.scalars(
                select(UserSavedNews).where(
                    UserSavedNews.user_id == user_id,
                    UserSavedNews.removed_at.is_(None),
                    UserSavedNews.marked_at >= cutoff,
                )
            ).all()
        )
        items: list[LibrarySavedItem] = [
            LibrarySavedItem(news_id=row.processed_news_id, marked_at=row.marked_at) for row in rows
        ]
        items.sort(key=lambda item: item.marked_at, reverse=True)
        return items

    def list_read(self, user_id: int) -> list[LibraryReadItem]:
        cutoff: int = _now_ms() - READ_RETENTION_MS
        self._purge_expired_read(user_id, cutoff)
        rows: list[UserReadNews] = list(
            self._db.scalars(
                select(UserReadNews).where(
                    UserReadNews.user_id == user_id,
                    UserReadNews.read_at >= cutoff,
                )
            ).all()
        )
        items: list[LibraryReadItem] = [
            LibraryReadItem(news_id=row.processed_news_id, read_at=row.read_at) for row in rows
        ]
        items.sort(key=lambda item: item.read_at, reverse=True)
        return items

    def apply_saved_deltas(self, user_id: int, deltas: list[LibrarySavedDelta]) -> list[int]:
        if not deltas:
            return []
        news_ids: set[int] = {delta.news_id for delta in deltas}
        existing: set[int] = find_existing_news_ids(self._db, news_ids)
        skipped: list[int] = []
        cutoff: int = _now_ms() - USEFUL_RETENTION_MS
        for delta in deltas:
            if delta.news_id not in existing:
                skipped.append(delta.news_id)
                continue
            if delta.marked_at < cutoff:
                continue
            if delta.removed:
                self._apply_saved_remove(user_id, delta.news_id, delta.marked_at)
            else:
                self._apply_saved_upsert(user_id, delta.news_id, delta.marked_at)
            self._db.flush()
        return skipped

    def apply_read_upserts(self, user_id: int, items: list[LibraryReadItem]) -> list[int]:
        if not items:
            return []
        news_ids: set[int] = {item.news_id for item in items}
        existing: set[int] = find_existing_news_ids(self._db, news_ids)
        skipped: list[int] = []
        cutoff: int = _now_ms() - READ_RETENTION_MS
        for item in items:
            if item.news_id not in existing:
                skipped.append(item.news_id)
                continue
            if item.read_at < cutoff:
                continue
            self._apply_read_upsert(user_id, item.news_id, item.read_at)
            self._db.flush()
        return skipped

    def commit(self) -> None:
        self._db.commit()

    def _get_saved_row(self, user_id: int, news_id: int) -> UserSavedNews | None:
        return self._db.execute(
            select(UserSavedNews).where(
                UserSavedNews.user_id == user_id,
                UserSavedNews.processed_news_id == news_id,
            )
        ).scalar_one_or_none()

    def _get_read_row(self, user_id: int, news_id: int) -> UserReadNews | None:
        return self._db.execute(
            select(UserReadNews).where(
                UserReadNews.user_id == user_id,
                UserReadNews.processed_news_id == news_id,
            )
        ).scalar_one_or_none()

    def _apply_saved_upsert(self, user_id: int, news_id: int, marked_at: int) -> None:
        row: UserSavedNews | None = self._get_saved_row(user_id, news_id)
        if row is None:
            self._db.add(
                UserSavedNews(
                    user_id=user_id,
                    processed_news_id=news_id,
                    marked_at=marked_at,
                    removed_at=None,
                )
            )
            return
        removed_at: int = row.removed_at if row.removed_at is not None else 0
        if marked_at >= row.marked_at and marked_at >= removed_at:
            row.marked_at = marked_at
            row.removed_at = None
            self._db.add(row)

    def _apply_saved_remove(self, user_id: int, news_id: int, removed_at: int) -> None:
        row: UserSavedNews | None = self._get_saved_row(user_id, news_id)
        if row is None:
            self._db.add(
                UserSavedNews(
                    user_id=user_id,
                    processed_news_id=news_id,
                    marked_at=0,
                    removed_at=removed_at,
                )
            )
            return
        previous_removed: int = row.removed_at if row.removed_at is not None else 0
        if removed_at >= row.marked_at and removed_at >= previous_removed:
            row.removed_at = removed_at
            self._db.add(row)

    def _apply_read_upsert(self, user_id: int, news_id: int, read_at: int) -> None:
        row: UserReadNews | None = self._get_read_row(user_id, news_id)
        if row is None:
            self._db.add(UserReadNews(user_id=user_id, processed_news_id=news_id, read_at=read_at))
            return
        if read_at >= row.read_at:
            row.read_at = read_at
            self._db.add(row)

    def _purge_expired_saved(self, user_id: int, cutoff: int) -> None:
        rows: list[UserSavedNews] = list(
            self._db.scalars(select(UserSavedNews).where(UserSavedNews.user_id == user_id)).all()
        )
        for row in rows:
            last_event: int = row.marked_at
            if row.removed_at is not None and row.removed_at > last_event:
                last_event = row.removed_at
            if last_event < cutoff:
                self._db.delete(row)
        self._db.flush()

    def _purge_expired_read(self, user_id: int, cutoff: int) -> None:
        self._db.execute(
            delete(UserReadNews).where(
                UserReadNews.user_id == user_id,
                UserReadNews.read_at < cutoff,
            )
        )
        self._db.flush()
