from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import uuid

from app.core.config import settings
from app.models.news import NewsCluster
from app.repositories.news_repository import NewsRepository
from app.services.embedding_service import EmbeddingEncoder, create_embedding_encoder, cosine_similarity


@dataclass(frozen=True)
class DedupResult:
    cluster_key: str
    similarity: float
    is_new_cluster: bool
    embedding: tuple[float, ...]


class DedupService:
    def __init__(self, encoder: EmbeddingEncoder | None = None) -> None:
        self._encoder: EmbeddingEncoder = encoder or create_embedding_encoder()

    def assign_cluster(self, repository: NewsRepository, title: str, summary: str) -> DedupResult:
        text: str = f"{title}\n{summary}".strip()
        embedding: list[float] = self._encoder.encode_normalized(text)
        embedding_tuple: tuple[float, ...] = tuple(embedding)

        since: datetime = datetime.utcnow() - timedelta(days=settings.semantic_dedup_lookback_days)
        candidates: list[NewsCluster] = repository.list_clusters_with_centroid_since(since=since)
        threshold: float = settings.semantic_dedup_min_similarity

        best_key: str | None = None
        best_similarity: float = -1.0
        for cluster in candidates:
            if not cluster.centroid_embedding_json:
                continue
            centroid: list[float] = json.loads(cluster.centroid_embedding_json)
            similarity: float = cosine_similarity(embedding, centroid)
            if similarity > best_similarity:
                best_similarity = similarity
                best_key = cluster.cluster_key

        if best_key is not None and best_similarity >= threshold:
            return DedupResult(
                cluster_key=best_key,
                similarity=float(best_similarity),
                is_new_cluster=False,
                embedding=embedding_tuple,
            )

        new_key: str = uuid.uuid4().hex
        return DedupResult(
            cluster_key=new_key,
            similarity=1.0,
            is_new_cluster=True,
            embedding=embedding_tuple,
        )
