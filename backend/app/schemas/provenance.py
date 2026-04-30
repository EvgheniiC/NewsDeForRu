"""Read-only API payloads for raw → cluster → processed chain (internal use)."""

from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from app.models.news import PipelineStatus, NewsTopic
from app.utils.berlin_time import to_berlin_iso


class ProvenanceRawOut(BaseModel):
    id: int
    source_key: str = Field(description="Configured source identifier (not a secret).")
    title: str
    summary_preview: str = Field(description="First part of raw summary for inspection.")
    pipeline_status: PipelineStatus
    cluster_key: str | None
    url_fingerprint: str
    published_at: datetime
    created_at: datetime

    @field_serializer("published_at", "created_at")
    def _serialize_raw_datetimes(self, value: datetime) -> str:
        return to_berlin_iso(value)


class ProvenanceClusterOut(BaseModel):
    id: int
    cluster_key: str
    canonical_title: str
    size: int
    updated_at: datetime

    @field_serializer("updated_at")
    def _serialize_updated_at(self, value: datetime) -> str:
        return to_berlin_iso(value)


class ProvenanceProcessedOut(BaseModel):
    id: int
    title: str
    one_sentence_summary: str = Field(description="Short reader-facing summary.")
    publication_status: PipelineStatus
    topic: NewsTopic
    raw_item_id: int
    cluster_id: int | None


class NewsProvenanceResponse(BaseModel):
    """Full chain for one story; not a public end-user surface."""

    raw: ProvenanceRawOut
    cluster: ProvenanceClusterOut | None = None
    processed: ProvenanceProcessedOut | None = None
