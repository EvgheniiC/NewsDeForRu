"""Resolve publication date and the source name shown to readers."""

from datetime import datetime
from urllib.parse import urlparse

from app.models.news import ProcessedNews, RawNewsItem, Source, SourceUrlStatus
from app.schemas.news import ProcessedNewsResponse
from app.services.news_origin_policy import NewsOriginMode, resolve_news_origin_mode

UNKNOWN_SOURCE_NAME: str = "Неизвестный источник"


def public_source_fields(
    *,
    source_key: str | None,
    publisher_name: str,
    publisher_url: str,
    primary_source_url: str | None,
    primary_source_name: str | None,
    rights_verified: bool = False,
    licence: str | None = None,
    licence_url: str | None = None,
) -> tuple[str, str]:
    """Return the source name and URL readers should see.

    A licensed source keeps its own name and URL. An unlicensed publisher item
    points at a primary-source link when the RSS text contains one. Otherwise
    both fields are empty: the card must not cite the publisher.
    """
    primary_url: str = (primary_source_url or "").strip()
    origin_mode: NewsOriginMode | None = resolve_news_origin_mode(
        source_key=source_key,
        rights_verified=rights_verified,
        licence=licence,
        licence_url=licence_url,
        has_primary_source=bool(primary_url),
    )
    cites_publisher: bool = origin_mode not in {
        NewsOriginMode.INDEPENDENT_PRIMARY,
        NewsOriginMode.MISSING_PRIMARY,
    }
    if cites_publisher:
        return publisher_name, publisher_url
    if not primary_url:
        return "", ""
    primary_name: str = (primary_source_name or "").strip()
    if not primary_name:
        primary_name = (urlparse(primary_url).hostname or "").removeprefix("www.") or "Источник"
    return primary_name, primary_url


def attribution_from_processed(processed: ProcessedNews) -> tuple[datetime, str, str]:
    """Return publication time plus the public source name and URL."""
    raw: RawNewsItem | None = processed.raw_item
    if raw is None:
        return processed.created_at, UNKNOWN_SOURCE_NAME, processed.source_url
    source: Source | None = raw.source
    publisher_name: str = source.name if source is not None else UNKNOWN_SOURCE_NAME
    source_key: str | None = source.source_key if source is not None else None
    source_name: str
    source_url: str
    source_name, source_url = public_source_fields(
        source_key=source_key,
        publisher_name=publisher_name,
        publisher_url=processed.source_url,
        primary_source_url=raw.primary_source_url,
        primary_source_name=raw.primary_source_name,
        rights_verified=processed.rights_verified,
        licence=processed.licence,
        licence_url=processed.licence_url,
    )
    return raw.published_at, source_name, source_url


def published_at_and_source_name(processed: ProcessedNews) -> tuple[datetime, str]:
    """Return RSS publication time and the source name shown to readers."""
    published_at, source_name, _source_url = attribution_from_processed(processed)
    return published_at, source_name


def build_processed_news_response(processed: ProcessedNews) -> ProcessedNewsResponse:
    """Build a public news payload including the source readers are allowed to see."""
    pub_at, source_name, source_url = attribution_from_processed(processed)
    raw: RawNewsItem | None = processed.raw_item
    source_key: str | None = (
        raw.source.source_key if raw is not None and raw.source is not None else None
    )
    raw_primary_url: str = ""
    if raw is not None:
        raw_primary_url = (raw.primary_source_url or "").strip()
    origin_mode: NewsOriginMode | None = resolve_news_origin_mode(
        source_key=source_key,
        rights_verified=processed.rights_verified,
        licence=processed.licence,
        licence_url=processed.licence_url,
        has_primary_source=bool(raw_primary_url),
    )
    hide_publisher_original: bool = origin_mode in {
        NewsOriginMode.INDEPENDENT_PRIMARY,
        NewsOriginMode.MISSING_PRIMARY,
    }
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
        source_url=source_url,
        source_url_status=processed.source_url_status or SourceUrlStatus.UNKNOWN,
        image_url=processed.image_url,
        confidence_score=processed.confidence_score,
        publication_status=processed.publication_status,
        read_time_minutes=processed.read_time_minutes,
        topic=processed.topic,
        cover_tag=processed.cover_tag,
        is_urgent=processed.is_urgent,
        is_positive=processed.is_positive,
        importance_ai_score=processed.importance_ai_score,
        published_at=pub_at,
        source_name=source_name,
        original_title=None if hide_publisher_original else processed.original_title,
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
