from __future__ import annotations

from datetime import datetime

import pytest

from app.core.database import Base, SessionLocal, engine, init_database
from app.models.news import ImpactPresentation, ModerationEvent, NewsTopic, PipelineStatus, ProcessedNews
from app.repositories.news_repository import NewsRepository


@pytest.fixture(autouse=True)
def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    init_database()


def test_list_telegram_digest_candidates_excludes_moderation_approve() -> None:
    init_database()
    with SessionLocal() as db:
        repo: NewsRepository = NewsRepository(db)
        src = repo.upsert_source("s1", "S", "http://x/rss")
        raw = repo.create_raw_item(
            source_id=src.id,
            guid="g1",
            title="t",
            summary="s",
            url="http://u",
            published_at=datetime.utcnow(),
        )
        auto_hi: ProcessedNews = ProcessedNews(
            raw_item_id=raw.id,
            title="A",
            one_sentence_summary="x",
            plain_language="p",
            impact_presentation=ImpactPresentation.MULTI,
            impact_owner="",
            impact_tenant="",
            impact_buyer="",
            action_items="",
            spoiler="",
            source_url="http://u",
            publication_status=PipelineStatus.PUBLISHED,
            topic=NewsTopic.LIFE,
            importance_ai_score=8,
            is_urgent=False,
        )
        repo.create_processed_news(auto_hi)

        raw2 = repo.create_raw_item(
            source_id=src.id,
            guid="g2",
            title="t2",
            summary="s2",
            url="http://u2",
            published_at=datetime.utcnow(),
        )
        moderated: ProcessedNews = ProcessedNews(
            raw_item_id=raw2.id,
            title="B",
            one_sentence_summary="y",
            plain_language="p",
            impact_presentation=ImpactPresentation.MULTI,
            impact_owner="",
            impact_tenant="",
            impact_buyer="",
            action_items="",
            spoiler="",
            source_url="http://u2",
            publication_status=PipelineStatus.PUBLISHED,
            topic=NewsTopic.LIFE,
            importance_ai_score=9,
            is_urgent=False,
        )
        saved_m: ProcessedNews = repo.create_processed_news(moderated)
        db.add(
            ModerationEvent(
                processed_news_id=saved_m.id,
                action="approve",
            )
        )
        db.commit()

        picked: list[ProcessedNews] = repo.list_telegram_digest_candidates(
            min_importance=6, limit=10, max_scan=100
        )
        assert len(picked) == 1
        assert picked[0].title == "A"


def test_list_telegram_digest_candidates_skips_urgent_and_low_score() -> None:
    init_database()
    with SessionLocal() as db:
        repo: NewsRepository = NewsRepository(db)
        src = repo.upsert_source("s2", "S2", "http://x2/rss")

        def _row(guid: str, title: str, imp: int, urgent: bool) -> None:
            raw = repo.create_raw_item(
                source_id=src.id,
                guid=guid,
                title=title,
                summary="s",
                url=f"http://{guid}",
                published_at=datetime.utcnow(),
            )
            p = ProcessedNews(
                raw_item_id=raw.id,
                title=title,
                one_sentence_summary="x",
                plain_language="p",
                impact_presentation=ImpactPresentation.MULTI,
                impact_owner="",
                impact_tenant="",
                impact_buyer="",
                action_items="",
                spoiler="",
                source_url="http://u",
                publication_status=PipelineStatus.PUBLISHED,
                topic=NewsTopic.LIFE,
                importance_ai_score=imp,
                is_urgent=urgent,
            )
            repo.create_processed_news(p)

        _row("u1", "low", 5, False)
        _row("u2", "urgent_ok", 8, True)
        _row("u3", "ok", 7, False)

        picked: list[ProcessedNews] = repo.list_telegram_digest_candidates(
            min_importance=6, limit=10, max_scan=100
        )
        titles: set[str] = {x.title for x in picked}
        assert titles == {"ok"}


def test_list_telegram_digest_candidates_one_per_cluster() -> None:
    with SessionLocal() as db:
        repo: NewsRepository = NewsRepository(db)
        src = repo.upsert_source("s3", "S3", "http://x3/rss")
        cluster = repo.upsert_cluster("ck", "ct", "cs")
        for i, (guid, score) in enumerate([("ga", 9), ("gb", 8)]):
            raw = repo.create_raw_item(
                source_id=src.id,
                guid=guid,
                title=guid,
                summary="s",
                url=f"http://{guid}",
                published_at=datetime.utcnow(),
            )
            p = ProcessedNews(
                raw_item_id=raw.id,
                title=f"row{i}",
                one_sentence_summary="x",
                plain_language="p",
                impact_presentation=ImpactPresentation.MULTI,
                impact_owner="",
                impact_tenant="",
                impact_buyer="",
                action_items="",
                spoiler="",
                source_url="http://u",
                publication_status=PipelineStatus.PUBLISHED,
                topic=NewsTopic.LIFE,
                importance_ai_score=score,
                is_urgent=False,
                cluster_id=cluster.id,
            )
            repo.create_processed_news(p)
        raw_other = repo.create_raw_item(
            source_id=src.id,
            guid="gc",
            title="other",
            summary="s",
            url="http://gc",
            published_at=datetime.utcnow(),
        )
        p_other = ProcessedNews(
            raw_item_id=raw_other.id,
            title="solo",
            one_sentence_summary="x",
            plain_language="p",
            impact_presentation=ImpactPresentation.MULTI,
            impact_owner="",
            impact_tenant="",
            impact_buyer="",
            action_items="",
            spoiler="",
            source_url="http://u",
            publication_status=PipelineStatus.PUBLISHED,
            topic=NewsTopic.LIFE,
            importance_ai_score=7,
            is_urgent=False,
            cluster_id=None,
        )
        repo.create_processed_news(p_other)

        picked: list[ProcessedNews] = repo.list_telegram_digest_candidates(
            min_importance=6, limit=3, max_scan=50
        )
        titles = {x.title for x in picked}
        assert titles == {"row0", "solo"}
        assert len(picked) == 2
