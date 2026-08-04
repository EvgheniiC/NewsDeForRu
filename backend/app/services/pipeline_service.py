import logging
import threading
from dataclasses import dataclass
from datetime import timedelta

from app.core.config import settings as app_settings
from app.core.database import SessionLocal
from app.models.news import ImpactPresentation, NewsTopic, PipelineStatus, ProcessedNews, RawNewsItem
from app.repositories.news_repository import NewsRepository
from app.schemas.llm_output import fallback_after_validation_failure
from app.schemas.news import PipelineItemErrorDetail, PipelineRunResponse
from app.services.dedup_service import DedupService
from app.services.embedding_service import create_embedding_encoder
from app.services.llm_provider import LLMProvider, create_llm_provider
from app.services.govdata_ingestion import GovDataIngestionService
from app.services.official_data_ingestion import (
    EurostatIngestionService,
    GenesisIngestionService,
    IngestionProvider,
)
from app.services.publication_service import PublicationDecisionInput, PublicationService
from app.services.publisher_text_guard import guard_llm_output
from app.services.telegram_notifier import send_auto_published_notice
from app.services.push_notifier import send_urgent_push_notice
from app.services.relevance_filter_service import RelevanceFilterService
from app.services.rss_ingestion_service import IngestionStats, RSSIngestionService
from app.services.urgent_news import ev_is_urgent_news
from app.utils.url_fingerprint import url_fingerprint

logger: logging.Logger = logging.getLogger(__name__)

_MAX_ITEM_ERROR_DETAILS: int = 100


@dataclass(frozen=True)
class PipelineContext:
    ingestion_providers: tuple[IngestionProvider, ...]
    relevance_filter: RelevanceFilterService
    dedup: DedupService
    llm_provider: LLMProvider
    publication: PublicationService


class PipelineService:
    def __init__(self, repository: NewsRepository) -> None:
        self.repository: NewsRepository = repository
        encoder = create_embedding_encoder()
        self.context: PipelineContext = PipelineContext(
            ingestion_providers=(
                RSSIngestionService(repository),
                GenesisIngestionService(repository),
                EurostatIngestionService(repository),
                GovDataIngestionService(repository),
            ),
            relevance_filter=RelevanceFilterService(encoder),
            dedup=DedupService(encoder),
            llm_provider=create_llm_provider(),
            publication=PublicationService(),
        )

    def run(self, run_id: str) -> PipelineRunResponse:
        provider_stats: tuple[IngestionStats, ...] = tuple(
            provider.run() for provider in self.context.ingestion_providers
        )
        ingestion_stats: IngestionStats = IngestionStats(
            fetched=sum(item.fetched for item in provider_stats),
            feeds_failed=sum(item.feeds_failed for item in provider_stats),
        )
        requeued_breaking: int = self.repository.requeue_filtered_breaking_news(
            lookback=timedelta(hours=48),
        )
        if requeued_breaking:
            logger.info(
                "requeued filtered breaking news count=%s run_id=%s",
                requeued_breaking,
                run_id,
            )
        requeued_official: int = self.repository.requeue_filtered_official_data(
            lookback=timedelta(hours=48),
        )
        if requeued_official:
            logger.info(
                "requeued filtered official data count=%s run_id=%s",
                requeued_official,
                run_id,
            )
        filtered_out: int = 0
        clustered: int = 0
        processed_count: int = 0
        published: int = 0
        needs_review: int = 0
        item_errors: int = 0
        item_error_details: list[PipelineItemErrorDetail] = []
        details_truncated_logged: bool = False

        raw_items: list[RawNewsItem] = self.repository.list_raw_items_for_processing()
        for raw_item in raw_items:
            source_key: str | None = (
                raw_item.source.source_key if raw_item.source is not None else None
            )
            relevance = self.context.relevance_filter.evaluate(
                raw_item.title,
                raw_item.summary,
                source_key=source_key,
            )
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
                source_key: str = raw_item.source.source_key if raw_item.source is not None else ""
                fp: str = url_fingerprint(raw_item.url)
                err_name: str = type(e).__name__
                logger.exception(
                    "LLM step failed raw_item_id=%s source_key=%s pipeline_step=llm "
                    "error_type=%s url_fingerprint=%s",
                    raw_item.id,
                    source_key,
                    err_name,
                    fp,
                )
                llm_output = fallback_after_validation_failure()
                item_errors += 1
                if len(item_error_details) < _MAX_ITEM_ERROR_DETAILS:
                    item_error_details.append(
                        PipelineItemErrorDetail(
                            raw_item_id=raw_item.id,
                            source_key=source_key,
                            pipeline_step="llm",
                            error_type=err_name,
                            url_fingerprint=fp,
                            cluster_id=cluster.id,
                        )
                    )
                elif not details_truncated_logged:
                    logger.warning(
                        "pipeline item_error_details capped at %s for run_id=%s",
                        _MAX_ITEM_ERROR_DETAILS,
                        run_id,
                    )
                    details_truncated_logged = True
            llm_output, overlap = guard_llm_output(
                source_title=raw_item.title,
                source_summary=raw_item.summary,
                output=llm_output,
            )
            if overlap.is_suspicious:
                logger.warning(
                    "Publisher text overlap blocked raw_item_id=%s max_ratio=%.3f "
                    "longest_match_words=%s longest_match_chars=%s",
                    raw_item.id,
                    overlap.max_similarity_ratio,
                    overlap.longest_match_words,
                    overlap.longest_match_chars,
                )
            decision_inp = PublicationDecisionInput(
                confidence_score=llm_output.confidence_score,
                relevance_score=relevance.score,
                is_new_cluster=dedup_result.is_new_cluster,
                title=raw_item.title,
                summary=raw_item.summary,
                licence=raw_item.licence,
                licence_url=raw_item.licence_url,
                rights_verified=raw_item.rights_verified,
            )
            publication_status, _ = self.context.publication.decide_status(decision_inp)
            if publication_status == PipelineStatus.PUBLISHED:
                published += 1
            else:
                needs_review += 1

            topic: NewsTopic = NewsTopic(llm_output.topic)
            is_urgent: bool = ev_is_urgent_news(
                raw_item.title,
                raw_item.summary,
                llm_output,
                published_at=raw_item.published_at,
            )
            # Do not store publisher preview URLs (Urheberrecht); app uses topic stock covers.
            processed_item = ProcessedNews(
                raw_item_id=raw_item.id,
                title=llm_output.title,
                one_sentence_summary=llm_output.one_sentence_summary,
                plain_language=llm_output.plain_language,
                impact_presentation=ImpactPresentation(llm_output.impact_presentation),
                impact_unified=llm_output.impact_unified,
                impact_owner=llm_output.impact_owner,
                impact_tenant=llm_output.impact_tenant,
                impact_buyer=llm_output.impact_buyer,
                action_items=llm_output.action_items,
                bonus_block=llm_output.bonus_block,
                spoiler=llm_output.spoiler,
                source_url=raw_item.url,
                original_title=raw_item.title,
                original_language=raw_item.original_language,
                retrieved_at=raw_item.retrieved_at,
                licence=raw_item.licence,
                licence_url=raw_item.licence_url,
                copyright_holder=raw_item.copyright_holder,
                is_translated=raw_item.is_translated,
                is_ai_summarised=raw_item.is_ai_summarised,
                changes_notice=raw_item.changes_notice,
                third_party_material_excluded=raw_item.third_party_material_excluded,
                source_revision=raw_item.source_revision,
                rights_verified=raw_item.rights_verified,
                image_url=None,
                confidence_score=llm_output.confidence_score,
                importance_ai_score=llm_output.importance_score,
                cluster_id=cluster.id,
                publication_status=publication_status,
                read_time_minutes=2,
                topic=topic,
                is_urgent=is_urgent,
                is_positive=llm_output.is_positive,
            )
            saved: ProcessedNews = self.repository.create_processed_news(processed_item)
            if publication_status == PipelineStatus.PUBLISHED:
                if is_urgent:
                    if app_settings.telegram_urgent_background_enabled:
                        urgent_id: int = saved.id
                        urgent_title: str = saved.title
                        urgent_topic: NewsTopic = saved.topic
                        urgent_summary: str = saved.one_sentence_summary
                        urgent_source_url: str = saved.source_url
                        urgent_source_name: str = raw_item.source.name
                        urgent_changes_notice: str = saved.changes_notice or ""

                        def _urgent_telegram_worker() -> None:
                            try:
                                sent_bg: bool = send_auto_published_notice(
                                    title_ru=urgent_title,
                                    topic=urgent_topic,
                                    one_sentence_summary=urgent_summary,
                                    source_url=urgent_source_url,
                                    source_name=urgent_source_name,
                                    changes_notice=urgent_changes_notice,
                                    processed_id=urgent_id,
                                    use_urgent_retries=True,
                                )
                                if not sent_bg:
                                    return
                                with SessionLocal() as bg_session:
                                    NewsRepository(bg_session).mark_telegram_notified(urgent_id)
                            except Exception:
                                logger.exception(
                                    "Background urgent Telegram failed processed_news_id=%s",
                                    urgent_id,
                                )

                        threading.Thread(
                            target=_urgent_telegram_worker,
                            daemon=True,
                            name=f"telegram-urgent-{urgent_id}",
                        ).start()
                    else:
                        sent_breaking: bool = send_auto_published_notice(
                            title_ru=saved.title,
                            topic=saved.topic,
                            one_sentence_summary=saved.one_sentence_summary,
                            source_url=saved.source_url,
                            source_name=raw_item.source.name,
                            changes_notice=saved.changes_notice or "",
                            processed_id=saved.id,
                            use_urgent_retries=True,
                        )
                        if sent_breaking:
                            self.repository.mark_telegram_notified(saved.id)
                    if app_settings.push_urgent_background_enabled:
                        push_id: int = saved.id
                        push_title: str = saved.title
                        push_summary: str = saved.one_sentence_summary
                        push_source_name: str = raw_item.source.name
                        push_source_url: str = saved.source_url

                        def _urgent_push_worker() -> None:
                            try:
                                sent_push_bg: bool = send_urgent_push_notice(
                                    title_ru=push_title,
                                    one_sentence_summary=push_summary,
                                    processed_id=push_id,
                                    source_name=push_source_name,
                                    source_url=push_source_url,
                                    use_urgent_retries=True,
                                )
                                if not sent_push_bg:
                                    return
                                with SessionLocal() as bg_session:
                                    NewsRepository(bg_session).mark_push_notified(push_id)
                            except Exception:
                                logger.exception(
                                    "Background urgent push failed processed_news_id=%s",
                                    push_id,
                                )

                        threading.Thread(
                            target=_urgent_push_worker,
                            daemon=True,
                            name=f"push-urgent-{push_id}",
                        ).start()
                    else:
                        sent_push: bool = send_urgent_push_notice(
                            title_ru=saved.title,
                            one_sentence_summary=saved.one_sentence_summary,
                            processed_id=saved.id,
                            source_name=raw_item.source.name,
                            source_url=saved.source_url,
                            use_urgent_retries=True,
                        )
                        if sent_push:
                            self.repository.mark_push_notified(saved.id)
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
            run_id=run_id,
            item_error_details=item_error_details,
        )
        logger.info(
            "Pipeline finished run_id=%s fetched=%s feeds_failed=%s filtered=%s "
            "clustered=%s processed=%s published=%s needs_review=%s item_errors=%s",
            run_id,
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
