"""Request/response payloads for `/engagement` APIs."""

from __future__ import annotations

import json
from typing import Any, cast

from pydantic import AliasChoices, BaseModel, Field, field_validator

from app.models.engagement import EngagementEventType


class RawEngagementEvent(BaseModel):
    news_id: int = Field(gt=0, description="Processed news PK")
    event_type: EngagementEventType
    client_event_id: str | None = Field(
        None,
        min_length=36,
        max_length=36,
        description="Client UUID for deduplicated retries.",
    )
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    @field_validator("payload", mode="before")
    @classmethod
    def normalize_payload(cls, v: object) -> dict[str, Any]:
        if v is None:
            return {}
        if isinstance(v, dict):
            return cast(dict[str, Any], v)
        raise ValueError("payload must be an object")


def payload_to_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class EngagementBatchRequest(BaseModel):
    anonymous_user_id: str = Field(
        ...,
        validation_alias=AliasChoices("anonymous_user_id", "anonymousUserId"),
        min_length=36,
        max_length=36,
    )
    session_id: str | None = Field(
        None,
        validation_alias=AliasChoices("session_id", "sessionId"),
        max_length=64,
    )
    events: list[RawEngagementEvent]

    model_config = {"extra": "forbid"}


class EngagementBatchResponse(BaseModel):
    inserted: int
    skipped_duplicate: int

