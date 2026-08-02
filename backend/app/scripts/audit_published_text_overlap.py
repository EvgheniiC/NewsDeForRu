from __future__ import annotations

import argparse
import logging

from sqlalchemy import Select, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.database import SessionLocal
from app.models.news import ImpactPresentation, PipelineStatus, ProcessedNews
from app.schemas.llm_output import LLMNewsOutput, fallback_after_validation_failure
from app.services.published_text_audit import PublishedTextFinding, audit_published_texts

logger: logging.Logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Audit published rows for suspicious overlap with stored RSS text."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Quarantine findings and replace public editorial text with the safe fallback.",
    )
    parser.add_argument("--limit", type=int, default=10_000)
    return parser.parse_args()


def _published_items(db_session: Session, limit: int) -> list[ProcessedNews]:
    query: Select[tuple[ProcessedNews]] = (
        select(ProcessedNews)
        .where(ProcessedNews.publication_status == PipelineStatus.PUBLISHED)
        .options(selectinload(ProcessedNews.raw_item))
        .order_by(ProcessedNews.id)
        .limit(max(1, limit))
    )
    return list(db_session.execute(query).scalars().all())


def _quarantine(item: ProcessedNews, fallback: LLMNewsOutput) -> None:
    item.title = fallback.title
    item.one_sentence_summary = fallback.one_sentence_summary
    item.plain_language = fallback.plain_language
    item.impact_presentation = ImpactPresentation(fallback.impact_presentation)
    item.impact_unified = fallback.impact_unified
    item.impact_owner = fallback.impact_owner
    item.impact_tenant = fallback.impact_tenant
    item.impact_buyer = fallback.impact_buyer
    item.action_items = fallback.action_items
    item.bonus_block = fallback.bonus_block
    item.spoiler = fallback.spoiler
    item.confidence_score = fallback.confidence_score
    item.importance_ai_score = fallback.importance_score
    item.publication_status = PipelineStatus.NEEDS_REVIEW


def _run_audit(args: argparse.Namespace) -> int:
    with SessionLocal() as db_session:
        items: list[ProcessedNews] = _published_items(db_session, args.limit)
        findings: list[PublishedTextFinding] = audit_published_texts(items)
        logger.info("Audited %s published rows; suspicious=%s", len(items), len(findings))
        for finding in findings:
            logger.warning(
                "Suspicious processed_news_id=%s raw_item_id=%s ratio=%.3f "
                "match_words=%s match_chars=%s",
                finding.processed_news_id,
                finding.raw_item_id,
                finding.overlap.max_similarity_ratio,
                finding.overlap.longest_match_words,
                finding.overlap.longest_match_chars,
            )

        if not args.apply or not findings:
            if findings:
                logger.info("Dry run only. Re-run with --apply to quarantine findings.")
            return 1 if findings else 0

        findings_by_id: frozenset[int] = frozenset(
            finding.processed_news_id for finding in findings
        )
        fallback: LLMNewsOutput = fallback_after_validation_failure()
        for item in items:
            if item.id in findings_by_id:
                _quarantine(item, fallback)
                db_session.add(item)
        db_session.commit()
        logger.info("Quarantined %s published rows", len(findings))
    return 0


def main() -> int:
    args: argparse.Namespace = _parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        return _run_audit(args)
    except SQLAlchemyError as error:
        logger.error("Published text audit could not access the database: %s", error)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
