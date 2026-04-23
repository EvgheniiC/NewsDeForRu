from app.core.config import settings
from app.models.news import PipelineStatus


class PublicationService:
    def decide_status(self, confidence_score: float) -> PipelineStatus:
        if confidence_score >= settings.auto_publish_threshold:
            return PipelineStatus.PUBLISHED
        return PipelineStatus.NEEDS_REVIEW
