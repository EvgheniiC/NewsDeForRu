from dataclasses import dataclass
from enum import StrEnum

from app.core.config import Settings, settings
from app.models.news import PipelineStatus


@dataclass(frozen=True)
class PublicationDecisionInput:
    """All signals used to choose auto publish vs moderation queue."""

    confidence_score: float
    relevance_score: float
    is_new_cluster: bool
    title: str
    summary: str


class PublicationReviewReason(StrEnum):
    """Why an item was sent to the moderation queue instead of auto publish."""

    LOW_CONFIDENCE = "low_confidence"
    LOW_RELEVANCE = "low_relevance"
    DUPLICATE_CLUSTER = "duplicate_cluster"
    KEYWORD = "keyword"


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
