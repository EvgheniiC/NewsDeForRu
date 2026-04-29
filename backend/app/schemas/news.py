from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

from app.models.news import ImpactPresentation, NewsTopic, PipelineStatus, UserRole

# Existing rows can contain a literal "None" from bad model JSON; never expose to clients as text.
_OCCASIONAL_PLACEHOLDERS: frozenset[str] = frozenset({"None", "null", "NULL", ""})


def normalize_one_sentence_for_api(value: str) -> str:
    t: str = value.strip()
    if t in _OCCASIONAL_PLACEHOLDERS:
        return (
            "Сводка не сформирована; смотрите оригинал по ссылке ниже."
        )
    return t


class ProcessedNewsResponse(BaseModel):
    id: int
    title: str
    one_sentence_summary: str
    plain_language: str
    impact_presentation: ImpactPresentation
    impact_unified: str
    impact_owner: str
    impact_tenant: str
    impact_buyer: str
    action_items: str
    bonus_block: str
    spoiler: str
    source_url: str
    confidence_score: float
    publication_status: PipelineStatus
    read_time_minutes: int
    topic: NewsTopic
    is_urgent: bool
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def _fix_legacy_placeholder_summary(self) -> Self:
        fixed: str = normalize_one_sentence_for_api(self.one_sentence_summary)
        if fixed != self.one_sentence_summary:
            return self.model_copy(update={"one_sentence_summary": fixed})
        return self


class NewsFeedItem(BaseModel):
    id: int
    title: str
    subtitle: str
    read_time_minutes: int
    topic: NewsTopic
    is_urgent: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NewsFeedPageResponse(BaseModel):
    """Paginated feed: pass ``next_cursor`` as ``cursor`` on the next request."""

    items: list[NewsFeedItem]
    next_cursor: int | None = None


class ModerationActionRequest(BaseModel):
    action: Literal["approve", "reject"]


class RoleImpactResponse(BaseModel):
    role: UserRole
    text: str


class PipelineItemErrorDetail(BaseModel):
    """Safe diagnostic context for a failed pipeline item (no PII, no secrets)."""

    raw_item_id: int
    source_key: str
    pipeline_step: Literal["llm"] = "llm"
    error_type: str
    url_fingerprint: str
    cluster_id: int | None = None


class PipelineRunResponse(BaseModel):
    fetched: int
    feeds_failed: int
    filtered_out: int
    clustered: int
    processed: int
    published: int
    needs_review: int
    item_errors: int = 0
    run_id: str
    item_error_details: list[PipelineItemErrorDetail] = Field(default_factory=list)
    ok: bool = True
    error: str | None = None
