from app.models.news import PipelineStatus
from app.services.publication_service import PublicationService


def test_publication_service_auto_publish_when_confident() -> None:
    service = PublicationService()
    assert service.decide_status(0.99) == PipelineStatus.PUBLISHED


def test_publication_service_sends_to_review_when_low_confidence() -> None:
    service = PublicationService()
    assert service.decide_status(0.2) == PipelineStatus.NEEDS_REVIEW
