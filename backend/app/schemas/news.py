from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models.news import PipelineStatus, UserRole


class ProcessedNewsResponse(BaseModel):
    id: int
    title: str
    one_sentence_summary: str
    plain_language: str
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
    created_at: datetime

    model_config = {"from_attributes": True}


class NewsFeedItem(BaseModel):
    id: int
    title: str
    subtitle: str
    read_time_minutes: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ModerationActionRequest(BaseModel):
    action: Literal["approve", "reject"]


class RoleImpactResponse(BaseModel):
    role: UserRole
    text: str


class PipelineRunResponse(BaseModel):
    fetched: int
    feeds_failed: int
    filtered_out: int
    clustered: int
    processed: int
    published: int
    needs_review: int
