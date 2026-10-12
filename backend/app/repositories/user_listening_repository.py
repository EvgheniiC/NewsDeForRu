"""Persist one listen-queue document per user with last-write-wins timestamps."""

from __future__ import annotations

from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.user_listening import UserListeningState
from app.repositories.engagement_repository import find_existing_news_ids
from app.schemas.user_listening import ListeningItem, ListeningPutResponse, ListeningStateBody


def empty_listening_state() -> ListeningStateBody:
    return ListeningStateBody(items=[], current_news_id=None, auto_next=False, updated_at=0)


class UserListeningRepository:
    def __init__(self, db_session: Session) -> None:
        self._db: Session = db_session

    def commit(self) -> None:
        self._db.commit()

    def delete_for_user(self, user_id: int) -> None:
        self._db.execute(delete(UserListeningState).where(UserListeningState.user_id == user_id))

    def get_state(self, user_id: int) -> ListeningStateBody:
        row: UserListeningState | None = self._row(user_id)
        if row is None:
            return empty_listening_state()
        return self._parse(row.state_json)

    def save_state(self, user_id: int, incoming: ListeningStateBody) -> ListeningPutResponse:
        row: UserListeningState | None = self._row(user_id)
        if row is not None and row.updated_at > incoming.updated_at:
            return ListeningPutResponse(state=self._parse(row.state_json), applied=False, skipped_news_ids=[])

        cleaned: ListeningStateBody
        skipped: list[int]
        cleaned, skipped = self._drop_unknown_news(incoming)
        payload: str = cleaned.model_dump_json()
        if row is None:
            self._db.add(
                UserListeningState(user_id=user_id, state_json=payload, updated_at=cleaned.updated_at)
            )
        else:
            row.state_json = payload
            row.updated_at = cleaned.updated_at
            self._db.add(row)
        return ListeningPutResponse(state=cleaned, applied=True, skipped_news_ids=skipped)

    def _row(self, user_id: int) -> UserListeningState | None:
        return self._db.scalar(select(UserListeningState).where(UserListeningState.user_id == user_id))

    def _parse(self, raw: str) -> ListeningStateBody:
        try:
            return ListeningStateBody.model_validate_json(raw)
        except ValidationError:
            return empty_listening_state()

    def _drop_unknown_news(self, incoming: ListeningStateBody) -> tuple[ListeningStateBody, list[int]]:
        news_ids: set[int] = {item.news_id for item in incoming.items}
        if incoming.current_news_id is not None:
            news_ids.add(incoming.current_news_id)
        existing: set[int] = find_existing_news_ids(self._db, news_ids)
        skipped: list[int] = sorted(news_id for news_id in news_ids if news_id not in existing)
        items: list[ListeningItem] = [item for item in incoming.items if item.news_id in existing]
        kept_ids: set[int] = {item.news_id for item in items}
        current_news_id: int | None = (
            incoming.current_news_id if incoming.current_news_id in kept_ids else None
        )
        cleaned: ListeningStateBody = ListeningStateBody(
            items=items,
            current_news_id=current_news_id,
            auto_next=incoming.auto_next,
            updated_at=incoming.updated_at,
        )
        return cleaned, skipped
