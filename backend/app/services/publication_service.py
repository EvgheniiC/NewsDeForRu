from dataclasses import dataclass
from enum import StrEnum

from app.core.config import Settings, settings
from app.models.news import PipelineStatus
from app.services.news_origin_policy import NewsOriginMode, resolve_news_origin_mode


@dataclass(frozen=True)
class PublicationDecisionInput:
    """All signals used to choose auto publish vs moderation queue."""

    confidence_score: float
    relevance_score: float
    is_new_cluster: bool
    title: str
    summary: str
    licence: str | None
    licence_url: str | None
    rights_verified: bool
    source_key: str | None = None
    has_primary_source: bool = True


class PublicationReviewReason(StrEnum):
    """Why an item was sent to the moderation queue instead of auto publish."""

    LOW_CONFIDENCE = "low_confidence"
    LOW_RELEVANCE = "low_relevance"
    DUPLICATE_CLUSTER = "duplicate_cluster"
    KEYWORD = "keyword"
    LICENCE = "licence"
    INDEPENDENT_DRAFT = "independent_draft"
    NO_PRIMARY_SOURCE = "no_primary_source"


def _parse_review_keywords(raw: str) -> tuple[str, ...]:
    parts: list[str] = [p.strip() for p in raw.split(",")]
    return tuple(p for p in parts if p)


class PublicationService:
    def __init__(self, app_settings: Settings | None = None) -> None:
        self._s: Settings = app_settings if app_settings is not None else settings

    def decide_status(self, inp: PublicationDecisionInput) -> tuple[PipelineStatus, PublicationReviewReason | None]:
        """
        Return publication status and, when not auto-published, the primary reason for review.
        """
        origin_mode: NewsOriginMode | None = resolve_news_origin_mode(
            source_key=inp.source_key,
            rights_verified=inp.rights_verified,
            licence=inp.licence,
            licence_url=inp.licence_url,
            has_primary_source=inp.has_primary_source,
        )
        # Rule 3: no primary source, so a person must decide.
        if origin_mode is NewsOriginMode.MISSING_PRIMARY:
            return PipelineStatus.NEEDS_REVIEW, PublicationReviewReason.NO_PRIMARY_SOURCE
        # Rule 2: original draft from a primary source, still a moderation item.
        if origin_mode is NewsOriginMode.INDEPENDENT_PRIMARY:
            return PipelineStatus.NEEDS_REVIEW, PublicationReviewReason.INDEPENDENT_DRAFT
        # Unlicensed non-publisher items stay out of the public feed.
        if origin_mode is None:
            return PipelineStatus.NEEDS_REVIEW, PublicationReviewReason.LICENCE
        # Rule 1: a licensed source may pass the quality gates below.

        text_lower: str = f"{inp.title}\n{inp.summary}".lower()
        for kw in _parse_review_keywords(self._s.moderation_extra_review_keywords):
            if kw.lower() in text_lower:
                return PipelineStatus.NEEDS_REVIEW, PublicationReviewReason.KEYWORD

        if inp.relevance_score < self._s.auto_publish_min_relevance:
            return PipelineStatus.NEEDS_REVIEW, PublicationReviewReason.LOW_RELEVANCE

        if self._s.auto_publish_review_on_duplicate_cluster and not inp.is_new_cluster:
            return PipelineStatus.NEEDS_REVIEW, PublicationReviewReason.DUPLICATE_CLUSTER

        if inp.confidence_score >= self._s.auto_publish_threshold:
            return PipelineStatus.PUBLISHED, None

        return PipelineStatus.NEEDS_REVIEW, PublicationReviewReason.LOW_CONFIDENCE
