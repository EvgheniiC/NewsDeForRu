"""Request/response payloads for ``/users/me/library``."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LibrarySavedItem(BaseModel):
    news_id: int = Field(gt=0)
    marked_at: int = Field(gt=0, description="Unix time in milliseconds")


class LibraryReadItem(BaseModel):
    news_id: int = Field(gt=0)
    read_at: int = Field(gt=0, description="Unix time in milliseconds")


class LibrarySavedDelta(BaseModel):
    news_id: int = Field(gt=0)
    marked_at: int = Field(
        gt=0,
        description="Event time in milliseconds: mark time, or unmark time when removed is true",
    )
    removed: bool = False


class LibraryGetResponse(BaseModel):
    saved: list[LibrarySavedItem]
    read: list[LibraryReadItem]


class LibraryPutRequest(BaseModel):
    saved: list[LibrarySavedDelta] = Field(default_factory=list, max_length=2000)
    read: list[LibraryReadItem] = Field(default_factory=list, max_length=2000)

    model_config = {"extra": "forbid"}


class LibraryPutResponse(BaseModel):
    saved_count: int
    read_count: int
    skipped_news_ids: list[int]
