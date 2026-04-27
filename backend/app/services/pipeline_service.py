import logging
from dataclasses import dataclass

from app.models.news import NewsTopic, PipelineStatus, ProcessedNews, RawNewsItem
from app.repositories.news_repository import NewsRepository
from app.schemas.llm_output import fallback_after_validation_failure
from app.schemas.news import PipelineRunResponse
from app.services.dedup_service import DedupService
from app.services.embedding_service import create_embedding_encoder
from app.services.llm_provider import LLMProvider, create_llm_provider
from app.services.publication_service import PublicationDecisionInput, PublicationService
from app.services.relevance_filter_service import RelevanceFilterService
from app.services.rss_ingestion_service import RSSIngestionService
from app.services.urgent_news import ev_is_urgent_news

logger: logging.Logger = logging.getLogger(__name__)


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
        encoder = create_embedding_encoder()
        self.context: PipelineContext = PipelineContext(
            ingestion=RSSIngestionService(repository),
            relevance_filter=RelevanceFilterService(encoder),
            dedup=DedupService(encoder),
            llm_provider=create_llm_provider(),
            publication=PublicationService(),
        )

    def run(self) -> PipelineRunResponse:
        ingestion_stats = self.context.ingestion.run()
        filtered_out: int = 0
        clustered: int = 0
        processed_count: int = 0
        published: int = 0
        needs_review: int = 0
        item_errors: int = 0

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

            dedup_result = self.context.dedup.assign_cluster(
                self.repository,
                raw_item.title,
                raw_item.summary,
            )
            clustered += 1
            self.repository.update_raw_status(
                raw_item=raw_item,
                status=PipelineStatus.CLUSTERED,
                relevance_score=relevance.score,
                relevance_reason=relevance.reason,
                cluster_key=dedup_result.cluster_key,
            )
            cluster = self.repository.upsert_cluster(
                cluster_key=dedup_result.cluster_key,
                canonical_title=raw_item.title,
                summary=raw_item.summary,
            )
            previous_cluster_size: int = cluster.size
            self.repository.attach_raw_to_cluster(
                raw_item=raw_item,
                cluster=cluster,
                similarity_score=dedup_result.similarity,
            )
            embedding_list: list[float] = list(dedup_result.embedding)
            if dedup_result.is_new_cluster:
                self.repository.set_cluster_centroid_embedding(cluster.id, embedding_list)
            else:
                self.repository.merge_cluster_centroid_embedding(
                    cluster.id,
                    embedding_list,
                    previous_cluster_size,
                )

            try:
                llm_output = self.context.llm_provider.process_news(raw_item.title, raw_item.summary)
            except Exception as e:
                logger.exception("LLM step failed for raw_item_id=%s", raw_item.id)
                llm_output = fallback_after_validation_failure(
                    raw_item.title, raw_item.summary, str(e)[:200]
                )
                item_errors += 1
            decision_inp = PublicationDecisionInput(
                confidence_score=llm_output.confidence_score,
                relevance_score=relevance.score,
                is_new_cluster=dedup_result.is_new_cluster,
                title=raw_item.title,
                summary=raw_item.summary,
            )
            publication_status, _ = self.context.publication.decide_status(decision_inp)
            if publication_status == PipelineStatus.PUBLISHED:
                published += 1
            else:
                needs_review += 1

            topic: NewsTopic = NewsTopic(llm_output.topic)
            is_urgent: bool = ev_is_urgent_news(raw_item.title, raw_item.summary, llm_output)
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
                cluster_id=cluster.id,
                publication_status=publication_status,
                read_time_minutes=2,
                topic=topic,
                is_urgent=is_urgent,
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

        out: PipelineRunResponse = PipelineRunResponse(
            fetched=ingestion_stats.fetched,
            feeds_failed=ingestion_stats.feeds_failed,
            filtered_out=filtered_out,
            clustered=clustered,
            processed=processed_count,
            published=published,
            needs_review=needs_review,
            item_errors=item_errors,
        )
        logger.info(
            "Pipeline finished: fetched=%s feeds_failed=%s filtered=%s "
            "clustered=%s processed=%s published=%s needs_review=%s item_errors=%s",
            out.fetched,
            out.feeds_failed,
            out.filtered_out,
            out.clustered,
            out.processed,
            out.published,
            out.needs_review,
            out.item_errors,
        )
        return out
