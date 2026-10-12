"""Request/response payloads for ``/users/me/listening``."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ListeningItem(BaseModel):
    news_id: int = Field(gt=0)
    chunk_index: int = Field(ge=0, le=500)
    finished: bool = False


class ListeningStateBody(BaseModel):
    items: list[ListeningItem] = Field(default_factory=list, max_length=50)
    current_news_id: int | None = Field(default=None, gt=0)
    auto_next: bool = False
    updated_at: int = Field(ge=0, description="Unix time in milliseconds")

    model_config = {"extra": "forbid"}


class ListeningPutResponse(BaseModel):
    state: ListeningStateBody
    applied: bool
    skipped_news_ids: list[int]
