"""Text embedding backends for semantic relevance and deduplication."""

from __future__ import annotations

import hashlib
from typing import Any, Protocol, cast, runtime_checkable

import numpy as np

from app.core.config import settings


@runtime_checkable
class EmbeddingEncoder(Protocol):
    def encode_normalized(self, text: str) -> list[float]:
        """Return L2-normalized embedding as a list of floats."""


class HashEmbeddingEncoder:
    """Deterministic embedding for tests and environments without ML models."""

    dim: int = 384

    def encode_normalized(self, text: str) -> list[float]:
        vector: np.ndarray = np.zeros(self.dim, dtype=np.float32)
        tokens: list[str] = text.lower().split()
        if not tokens:
            tokens = ["<empty>"]
        for token in tokens:
            digest: bytes = hashlib.sha256(token.encode("utf-8")).digest()
            for byte_index in range(len(digest)):
                component_index: int = (byte_index * 7 + len(token)) % self.dim
                vector[component_index] += float(digest[byte_index]) / 255.0
        norm: float = float(np.linalg.norm(vector))
        if norm > 1e-9:
            vector = vector / norm
        return cast(list[float], vector.astype(np.float32).tolist())


class SentenceTransformerEmbeddingEncoder:
    def __init__(self, model_name: str) -> None:
        self._model_name: str = model_name
        self._model: Any = None

    def _ensure_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
        return self._model

    def encode_normalized(self, text: str) -> list[float]:
        model: Any = self._ensure_model()
        vector: np.ndarray = model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        if vector.ndim > 1:
            vector = vector[0]
        return cast(list[float], vector.astype(np.float32).tolist())


def create_embedding_encoder() -> EmbeddingEncoder:
    backend: str = settings.semantic_embedding_backend.strip().lower()
    if backend == "hash":
        return HashEmbeddingEncoder()
    if backend in ("sentence_transformers", "sentence-transformers", "st"):
        return SentenceTransformerEmbeddingEncoder(settings.semantic_embedding_model)
    raise ValueError(f"Unknown semantic_embedding_backend: {settings.semantic_embedding_backend!r}")


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity for L2-normalized vectors (dot product)."""
    if len(a) != len(b):
        raise ValueError("Embedding dimensions must match.")
    return float(np.dot(np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)))
