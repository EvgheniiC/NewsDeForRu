from dataclasses import dataclass

from app.models.news import PipelineStatus, ProcessedNews, RawNewsItem
from app.repositories.news_repository import NewsRepository
from app.schemas.news import PipelineRunResponse
from app.services.dedup_service import DedupService
from app.services.llm_provider import LLMProvider, StubLLMProvider
from app.services.publication_service import PublicationService
from app.services.relevance_filter_service import RelevanceFilterService
from app.services.rss_ingestion_service import RSSIngestionService


@dataclass(frozen=True)
class PipelineContext:
    ingestion: RSSIngestionService
    relevance_filter: RelevanceFilterService
    dedup: DedupService
    llm_provider: LLMProvider
    publication: PublicationService


class PipelineService:
    def __init__(self, repository: NewsRepository) -> None:
        self.repository: NewsRepository = repository
        self.context: PipelineContext = PipelineContext(
            ingestion=RSSIngestionService(repository),
            relevance_filter=RelevanceFilterService(),
            dedup=DedupService(),
            llm_provider=StubLLMProvider(),
            publication=PublicationService(),
        )

    def run(self) -> PipelineRunResponse:
        ingestion_stats = self.context.ingestion.run()
        filtered_out: int = 0
        clustered: int = 0
        processed_count: int = 0
        published: int = 0
        needs_review: int = 0

        raw_items: list[RawNewsItem] = self.repository.list_raw_items_for_processing()
        for raw_item in raw_items:
            relevance = self.context.relevance_filter.evaluate(raw_item.title, raw_item.summary)
            if not relevance.is_relevant:
                filtered_out += 1
                self.repository.update_raw_status(
                    raw_item=raw_item,
                    status=PipelineStatus.FILTERED_OUT,
                    relevance_score=relevance.score,
                    relevance_reason=relevance.reason,
                )
                continue

            dedup_result = self.context.dedup.cluster(raw_item.title, raw_item.summary)
            clustered += 1
            self.repository.update_raw_status(
                raw_item=raw_item,
                status=PipelineStatus.CLUSTERED,
                relevance_score=relevance.score,
                relevance_reason=relevance.reason,
                cluster_key=dedup_result.cluster_key,
            )

            llm_output = self.context.llm_provider.process_news(raw_item.title, raw_item.summary)
            publication_status = self.context.publication.decide_status(llm_output.confidence_score)
            if publication_status == PipelineStatus.PUBLISHED:
                published += 1
            else:
                needs_review += 1

            processed_item = ProcessedNews(
                raw_item_id=raw_item.id,
                title=llm_output.title,
                one_sentence_summary=llm_output.one_sentence_summary,
                plain_language=llm_output.plain_language,
                impact_owner=llm_output.impact_owner,
                impact_tenant=llm_output.impact_tenant,
                impact_buyer=llm_output.impact_buyer,
                action_items=llm_output.action_items,
                bonus_block=llm_output.bonus_block,
                spoiler=llm_output.spoiler,
                source_url=raw_item.url,
                confidence_score=llm_output.confidence_score,
                publication_status=publication_status,
                read_time_minutes=2,
            )
            self.repository.create_processed_news(processed_item)
            self.repository.update_raw_status(
                raw_item=raw_item,
                status=PipelineStatus.PROCESSED,
                relevance_score=relevance.score,
                relevance_reason=relevance.reason,
                cluster_key=dedup_result.cluster_key,
            )
            processed_count += 1

        return PipelineRunResponse(
            fetched=ingestion_stats.fetched,
            filtered_out=filtered_out,
            clustered=clustered,
            processed=processed_count,
            published=published,
            needs_review=needs_review,
        )
