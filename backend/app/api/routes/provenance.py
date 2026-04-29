"""Internal read-only tracing: raw ingestion → clustering → processed card."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db_session
from app.models.news import RawNewsItem
from app.repositories.news_repository import NewsRepository
from app.schemas.provenance import (
    NewsProvenanceResponse,
    ProvenanceClusterOut,
    ProvenanceProcessedOut,
    ProvenanceRawOut,
)
from app.utils.url_fingerprint import url_fingerprint

router: APIRouter = APIRouter(prefix="/internal/provenance", tags=["internal"])

_provenance_header: APIKeyHeader = APIKeyHeader(name="X-Internal-Api-Key", auto_error=False)


def verify_provenance_key(
    x_internal_api_key: str | None = Depends(_provenance_header),
) -> None:
    expected: str = (settings.provenance_api_key or "").strip()
    if not expected:
        raise HTTPException(status_code=404, detail="Not found")
    if not x_internal_api_key or x_internal_api_key != expected:
        raise HTTPException(status_code=403, detail="Forbidden")


_PREVIEW_LEN: int = 400


def _raw_out_from_item(raw_item: RawNewsItem, source_key: str) -> ProvenanceRawOut:
    summary: str = raw_item.summary or ""
    preview: str = summary if len(summary) <= _PREVIEW_LEN else summary[: _PREVIEW_LEN] + "…"
    return ProvenanceRawOut(
        id=raw_item.id,
        source_key=source_key,
        title=raw_item.title,
        summary_preview=preview,
        pipeline_status=raw_item.pipeline_status,
        cluster_key=raw_item.cluster_key,
        url_fingerprint=url_fingerprint(raw_item.url),
        published_at=raw_item.published_at,
        created_at=raw_item.created_at,
    )


def _build_response(repo: NewsRepository, raw_item: RawNewsItem) -> NewsProvenanceResponse:
    src = raw_item.source
    source_key: str = src.source_key if src is not None else ""
    raw_out: ProvenanceRawOut = _raw_out_from_item(raw_item, source_key)

    cluster_out: ProvenanceClusterOut | None = None
    if raw_item.cluster_key:
        ck = repo.get_cluster_by_key(raw_item.cluster_key)
        if ck is not None:
            cluster_out = ProvenanceClusterOut(
                id=ck.id,
                cluster_key=ck.cluster_key,
                canonical_title=ck.canonical_title,
                size=ck.size,
                updated_at=ck.updated_at,
            )

    proc_row = repo.get_processed_by_raw_item_id(raw_item.id)
    processed_out: ProvenanceProcessedOut | None = None
    if proc_row is not None:
        processed_out = ProvenanceProcessedOut(
            id=proc_row.id,
            title=proc_row.title,
            one_sentence_summary=proc_row.one_sentence_summary,
            publication_status=proc_row.publication_status,
            topic=proc_row.topic,
            raw_item_id=proc_row.raw_item_id,
            cluster_id=proc_row.cluster_id,
        )

    return NewsProvenanceResponse(raw=raw_out, cluster=cluster_out, processed=processed_out)


@router.get(
    "/by-raw/{raw_item_id}",
    response_model=NewsProvenanceResponse,
    dependencies=[Depends(verify_provenance_key)],
)
def get_by_raw(raw_item_id: int, db: Session = Depends(get_db_session)) -> NewsProvenanceResponse:
    repo: NewsRepository = NewsRepository(db)
    raw_item = repo.get_raw_item_by_id(raw_item_id)
    if raw_item is None:
        raise HTTPException(status_code=404, detail="Raw item not found")
    return _build_response(repo, raw_item)


@router.get(
    "/by-processed/{processed_news_id}",
    response_model=NewsProvenanceResponse,
    dependencies=[Depends(verify_provenance_key)],
)
def get_by_processed(processed_news_id: int, db: Session = Depends(get_db_session)) -> NewsProvenanceResponse:
    repo: NewsRepository = NewsRepository(db)
    proc = repo.get_processed_by_id(processed_news_id)
    if proc is None:
        raise HTTPException(status_code=404, detail="Processed item not found")
    raw_item = repo.get_raw_item_by_id(proc.raw_item_id)
    if raw_item is None:
        raise HTTPException(status_code=500, detail="Processed row refers to missing raw item")
    return _build_response(repo, raw_item)
