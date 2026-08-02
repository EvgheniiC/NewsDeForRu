"""Resolve publication date and publisher name for public news API responses."""

from datetime import datetime

from app.models.news import ProcessedNews, RawNewsItem, Source, SourceUrlStatus
from app.schemas.news import ProcessedNewsResponse

UNKNOWN_SOURCE_NAME: str = "Неизвестный источник"


def published_at_and_source_name(processed: ProcessedNews) -> tuple[datetime, str]:
    """Return RSS publication time and human-readable publisher name."""
    raw: RawNewsItem | None = processed.raw_item
    if raw is None:
        return processed.created_at, UNKNOWN_SOURCE_NAME
    source: Source | None = raw.source
    source_name: str = source.name if source is not None else UNKNOWN_SOURCE_NAME
    return raw.published_at, source_name


def build_processed_news_response(processed: ProcessedNews) -> ProcessedNewsResponse:
    """Build a public news payload including publisher attribution."""
    pub_at, source_name = published_at_and_source_name(processed)
    return ProcessedNewsResponse(
        id=processed.id,
        title=processed.title,
        one_sentence_summary=processed.one_sentence_summary,
        plain_language=processed.plain_language,
        impact_presentation=processed.impact_presentation,
        impact_unified=processed.impact_unified,
        impact_owner=processed.impact_owner,
        impact_tenant=processed.impact_tenant,
        impact_buyer=processed.impact_buyer,
        action_items=processed.action_items,
        bonus_block=processed.bonus_block,
        spoiler=processed.spoiler,
        source_url=processed.source_url,
        source_url_status=processed.source_url_status or SourceUrlStatus.UNKNOWN,
        image_url=processed.image_url,
        confidence_score=processed.confidence_score,
        publication_status=processed.publication_status,
        read_time_minutes=processed.read_time_minutes,
        topic=processed.topic,
        is_urgent=processed.is_urgent,
        is_positive=processed.is_positive,
        importance_ai_score=processed.importance_ai_score,
        published_at=pub_at,
        source_name=source_name,
        original_title=processed.original_title,
        original_language=processed.original_language,
        retrieved_at=processed.retrieved_at,
        licence=processed.licence,
        licence_url=processed.licence_url,
        copyright_holder=processed.copyright_holder,
        is_translated=processed.is_translated,
        is_ai_summarised=processed.is_ai_summarised,
        changes_notice=processed.changes_notice,
        third_party_material_excluded=processed.third_party_material_excluded,
        source_revision=processed.source_revision,
        created_at=processed.created_at,
    )
