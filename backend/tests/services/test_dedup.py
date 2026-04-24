from __future__ import annotations

import json
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
import app.models.news  # noqa: F401
from app.models.news import NewsCluster
from app.repositories.news_repository import NewsRepository
from app.services.dedup_service import DedupService
from app.services.embedding_service import HashEmbeddingEncoder


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_dedup_reuses_cluster_when_centroid_matches(db_session) -> None:
    encoder: HashEmbeddingEncoder = HashEmbeddingEncoder()
    title: str = "Steuerreform 2026"
    summary: str = "Neue Regeln fuer Mieter und Eigentuemer."
    text: str = f"{title}\n{summary}".strip()
    embedding: list[float] = encoder.encode_normalized(text)

    cluster: NewsCluster = NewsCluster(
        cluster_key="a" * 32,
        canonical_title=title,
        summary=summary,
        size=1,
        centroid_embedding_json=json.dumps(embedding),
        updated_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db_session.add(cluster)
    db_session.commit()

    repo: NewsRepository = NewsRepository(db_session)
    dedup: DedupService = DedupService(encoder)
    result = dedup.assign_cluster(repo, title, summary)
    assert result.is_new_cluster is False
    assert result.cluster_key == cluster.cluster_key
    assert result.similarity >= 0.99


def test_dedup_creates_new_cluster_when_no_neighbors(db_session) -> None:
    repo: NewsRepository = NewsRepository(db_session)
    dedup: DedupService = DedupService(HashEmbeddingEncoder())
    result = dedup.assign_cluster(repo, "Other topic", "Unrelated summary body.")
    assert result.is_new_cluster is True
    assert len(result.cluster_key) == 32
