from __future__ import annotations

import argparse
import logging

from sqlalchemy import Select, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.news import PipelineStatus, ProcessedNews, RawNewsItem, Source
from app.services.rss_sources import is_source_allowed_for_publication

logger: logging.Logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=(
            "Unpublish feed/Telegram items from disabled or unverified sources "
            "(e.g. Welt, Zeit) and drop their INGESTED backlog."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes. Without this flag the script only reports matches.",
    )
    parser.add_argument("--limit", type=int, default=50_000)
    return parser.parse_args()


def _disabled_published_items(db_session: Session, limit: int) -> list[ProcessedNews]:
    query: Select[tuple[ProcessedNews]] = (
        select(ProcessedNews)
        .join(RawNewsItem, ProcessedNews.raw_item_id == RawNewsItem.id)
        .join(Source, Source.id == RawNewsItem.source_id)
        .where(ProcessedNews.publication_status == PipelineStatus.PUBLISHED)
        .options(selectinload(ProcessedNews.raw_item).selectinload(RawNewsItem.source))
        .order_by(ProcessedNews.id)
        .limit(max(1, limit))
    )
    rows: list[ProcessedNews] = list(db_session.execute(query).scalars().all())
    disabled: list[ProcessedNews] = []
    for item in rows:
        raw_item: RawNewsItem | None = item.raw_item
        source_key: str | None = None
        if raw_item is not None and raw_item.source is not None:
            source_key = raw_item.source.source_key
        if is_source_allowed_for_publication(
            source_key,
            rights_verified=item.rights_verified,
            enabled_source_keys=settings.rss_enabled_source_keys,
            allow_unverified=settings.rss_allow_unverified_catalog_sources,
        ):
            continue
        disabled.append(item)
    return disabled


def _disabled_ingested_raw_items(db_session: Session, limit: int) -> list[RawNewsItem]:
    query: Select[tuple[RawNewsItem]] = (
        select(RawNewsItem)
        .where(RawNewsItem.pipeline_status == PipelineStatus.INGESTED)
        .options(selectinload(RawNewsItem.source))
        .order_by(RawNewsItem.id)
        .limit(max(1, limit))
    )
    rows: list[RawNewsItem] = list(db_session.execute(query).scalars().all())
    disabled: list[RawNewsItem] = []
    for raw_item in rows:
        source_key: str | None = (
            raw_item.source.source_key if raw_item.source is not None else None
        )
        if is_source_allowed_for_publication(
            source_key,
            rights_verified=raw_item.rights_verified,
            enabled_source_keys=settings.rss_enabled_source_keys,
            allow_unverified=settings.rss_allow_unverified_catalog_sources,
        ):
            continue
        disabled.append(raw_item)
    return disabled


def _run(args: argparse.Namespace) -> int:
    with SessionLocal() as db_session:
        published: list[ProcessedNews] = _disabled_published_items(db_session, args.limit)
        ingested: list[RawNewsItem] = _disabled_ingested_raw_items(db_session, args.limit)
        logger.info(
            "Disabled-source cleanup candidates: published=%s ingested_backlog=%s "
            "rss_enabled_source_keys=%r",
            len(published),
            len(ingested),
            settings.rss_enabled_source_keys,
        )
        for item in published:
            published_source_key: str = (
                item.raw_item.source.source_key
                if item.raw_item is not None and item.raw_item.source is not None
                else "?"
            )
            logger.warning(
                "Would unpublish processed_news_id=%s source_key=%s rights_verified=%s",
                item.id,
                published_source_key,
                item.rights_verified,
            )
        for raw_item in ingested:
            ingested_source_key: str = (
                raw_item.source.source_key if raw_item.source is not None else "?"
            )
            logger.warning(
                "Would drop ingested raw_item_id=%s source_key=%s rights_verified=%s",
                raw_item.id,
                ingested_source_key,
                raw_item.rights_verified,
            )

        if not args.apply:
            if published or ingested:
                logger.info("Dry run only. Re-run with --apply to write changes.")
            return 0

        for item in published:
            item.publication_status = PipelineStatus.FILTERED_OUT
            db_session.add(item)
        for raw_item in ingested:
            raw_item.pipeline_status = PipelineStatus.FILTERED_OUT
            raw_item.relevance_reason = "source_not_enabled"
            db_session.add(raw_item)
        db_session.commit()
        logger.info(
            "Unpublished %s processed rows; filtered %s ingested raw rows",
            len(published),
            len(ingested),
        )
    return 0


def main() -> int:
    args: argparse.Namespace = _parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        return _run(args)
    except SQLAlchemyError as error:
        logger.error("Disabled-source cleanup could not access the database: %s", error)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
