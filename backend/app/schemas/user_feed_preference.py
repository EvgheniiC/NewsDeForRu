"""Request and response payloads for ``/users/me/feed-preferences``."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.models.news import CoverTag


class FeedPreferencesBody(BaseModel):
    interests: list[CoverTag] = Field(default_factory=list, max_length=16)

    model_config = {"extra": "forbid"}

    @field_validator("interests")
    @classmethod
    def unique_interests(cls, value: list[CoverTag]) -> list[CoverTag]:
        seen: list[CoverTag] = []
        for tag in value:
            if tag not in seen:
                seen.append(tag)
        return seen
