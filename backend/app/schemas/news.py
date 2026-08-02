from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, field_serializer, model_validator

from app.models.news import ImpactPresentation, NewsTopic, PipelineStatus, SourceUrlStatus, UserRole
from app.utils.berlin_time import to_berlin_iso

# Existing rows can contain a literal "None" from bad model JSON; never expose to clients as text.
_OCCASIONAL_PLACEHOLDERS: frozenset[str] = frozenset({"None", "null", "NULL", ""})


def normalize_one_sentence_for_api(value: str) -> str:
    t: str = value.strip()
    if t in _OCCASIONAL_PLACEHOLDERS:
        return (
            "Сводка не сформирована; смотрите оригинал по ссылке ниже."
        )
    return t


_LEGACY_ACTION_ITEMS_PLACEHOLDER_NO_INFO: str = (
    "- Уточните детали по официальным источникам и актуальным объявлениям."
)


def normalize_action_items_for_api(value: str) -> str:
    """Older pipeline rows used a generic filler line; omit it when exposing JSON to clients."""
    t: str = value.strip()
    if t == _LEGACY_ACTION_ITEMS_PLACEHOLDER_NO_INFO:
        return ""
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
    source_url_status: SourceUrlStatus = SourceUrlStatus.UNKNOWN
    image_url: str | None = None
    confidence_score: float
    publication_status: PipelineStatus
    read_time_minutes: int
    topic: NewsTopic
    is_urgent: bool
    is_positive: bool
    importance_ai_score: int
    published_at: datetime
    source_name: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("published_at", "created_at")
    def _serialize_datetimes(self, value: datetime) -> str:
        return to_berlin_iso(value)

    @model_validator(mode="after")
    def _fix_legacy_placeholder_summary(self) -> Self:
        fixed: str = normalize_one_sentence_for_api(self.one_sentence_summary)
        if fixed != self.one_sentence_summary:
            return self.model_copy(update={"one_sentence_summary": fixed})
        return self

    @model_validator(mode="after")
    def _strip_legacy_action_items_placeholder(self) -> Self:
        fixed: str = normalize_action_items_for_api(self.action_items)
        if fixed != self.action_items:
            return self.model_copy(update={"action_items": fixed})
        return self


class NewsFeedItem(BaseModel):
    id: int
    title: str
    subtitle: str
    image_url: str | None = None
    read_time_minutes: int
    topic: NewsTopic
    is_urgent: bool
    is_positive: bool
    published_at: datetime
    source_name: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("published_at", "created_at")
    def _serialize_datetimes(self, value: datetime) -> str:
        return to_berlin_iso(value)


class NewsFeedPageResponse(BaseModel):
    """Paginated feed: pass ``next_cursor`` as ``cursor`` on the next request."""

    items: list[NewsFeedItem]
    next_cursor: int | None = None


class TopNewsRankMeta(BaseModel):
    total_score: int
    source_count: int
    mentions_points: int
    freshness_points: int
    ai_importance: int


class TopNewsFeedItem(NewsFeedItem):
    rank: TopNewsRankMeta


class TopNewsTodayResponse(BaseModel):
    items: list[TopNewsFeedItem]


class ModerationActionRequest(BaseModel):
    action: Literal["approve", "reject"]


class NewsMetadataPatchRequest(BaseModel):
    """Partial metadata edit for items in the moderation queue."""

    topic: NewsTopic | None = None
    is_urgent: bool | None = None
    is_positive: bool | None = None

    @model_validator(mode="after")
    def _require_at_least_one_field(self) -> Self:
        if self.topic is None and self.is_urgent is None and self.is_positive is None:
            raise ValueError("At least one metadata field must be provided.")
        return self


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
