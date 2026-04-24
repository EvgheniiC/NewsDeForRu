from app.core.config import Settings
from app.models.news import PipelineStatus
from app.services.publication_service import (
    PublicationDecisionInput,
    PublicationReviewReason,
    PublicationService,
)


def _inp(
    *,
    confidence: float = 0.99,
    relevance: float = 0.75,
    new_cluster: bool = True,
    title: str = "Titel",
    summary: str = "Kurz",
) -> PublicationDecisionInput:
    return PublicationDecisionInput(
        confidence_score=confidence,
        relevance_score=relevance,
        is_new_cluster=new_cluster,
        title=title,
        summary=summary,
    )


def test_publication_service_auto_publish_when_confident_and_clear() -> None:
    service = PublicationService(
        app_settings=Settings(
            auto_publish_threshold=0.85,
            auto_publish_min_relevance=0.5,
            auto_publish_review_on_duplicate_cluster=True,
        )
    )
    status, reason = service.decide_status(_inp())
    assert status == PipelineStatus.PUBLISHED
    assert reason is None


def test_publication_service_sends_to_review_when_low_confidence() -> None:
    service = PublicationService(app_settings=Settings(auto_publish_threshold=0.85))
    status, reason = service.decide_status(_inp(confidence=0.2))
    assert status == PipelineStatus.NEEDS_REVIEW
    assert reason == PublicationReviewReason.LOW_CONFIDENCE


def test_publication_service_sends_to_review_when_low_relevance() -> None:
    service = PublicationService(
        app_settings=Settings(
            auto_publish_threshold=0.85,
            auto_publish_min_relevance=0.5,
        )
    )
    status, reason = service.decide_status(_inp(confidence=0.99, relevance=0.4))
    assert status == PipelineStatus.NEEDS_REVIEW
    assert reason == PublicationReviewReason.LOW_RELEVANCE


def test_publication_service_sends_to_review_when_joins_existing_cluster() -> None:
    service = PublicationService(
        app_settings=Settings(
            auto_publish_threshold=0.85,
            auto_publish_min_relevance=0.5,
            auto_publish_review_on_duplicate_cluster=True,
        )
    )
    status, reason = service.decide_status(_inp(new_cluster=False))
    assert status == PipelineStatus.NEEDS_REVIEW
    assert reason == PublicationReviewReason.DUPLICATE_CLUSTER


def test_publication_service_auto_publish_when_duplicate_cluster_policy_off() -> None:
    service = PublicationService(
        app_settings=Settings(
            auto_publish_threshold=0.85,
            auto_publish_min_relevance=0.5,
            auto_publish_review_on_duplicate_cluster=False,
        )
    )
    status, reason = service.decide_status(_inp(new_cluster=False))
    assert status == PipelineStatus.PUBLISHED
    assert reason is None


def test_publication_service_keyword_forces_review() -> None:
    service = PublicationService(
        app_settings=Settings(
            auto_publish_threshold=0.85,
            auto_publish_min_relevance=0.5,
            moderation_extra_review_keywords="achtung",
        )
    )
    status, reason = service.decide_status(_inp(title="ACHTUNG im Titel"))
    assert status == PipelineStatus.NEEDS_REVIEW
    assert reason == PublicationReviewReason.KEYWORD
