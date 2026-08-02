from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.models.news import ProcessedNews, RawNewsItem
from app.services.publisher_text_guard import (
    PublisherTextOverlap,
    detect_publisher_text_overlap,
)


@dataclass(frozen=True)
class PublishedTextFinding:
    processed_news_id: int
    raw_item_id: int
    overlap: PublisherTextOverlap


def _processed_text_segments(item: ProcessedNews) -> tuple[str, ...]:
    return (
        item.title,
        item.one_sentence_summary,
        item.plain_language,
        item.impact_unified,
        item.impact_owner,
        item.impact_tenant,
        item.impact_buyer,
        item.action_items,
        item.bonus_block,
        item.spoiler,
    )


def audit_published_texts(
    items: list[ProcessedNews],
    *,
    app_settings: Settings | None = None,
) -> list[PublishedTextFinding]:
    """Return suspicious published rows without exposing matched publisher text."""
    findings: list[PublishedTextFinding] = []
    for item in items:
        raw_item: RawNewsItem | None = item.raw_item
        if raw_item is None:
            continue
        overlap: PublisherTextOverlap = detect_publisher_text_overlap(
            source_title=raw_item.title,
            source_summary=raw_item.summary,
            output_segments=_processed_text_segments(item),
            app_settings=app_settings,
        )
        if overlap.is_suspicious:
            findings.append(
                PublishedTextFinding(
                    processed_news_id=item.id,
                    raw_item_id=raw_item.id,
                    overlap=overlap,
                )
            )
    return findings
