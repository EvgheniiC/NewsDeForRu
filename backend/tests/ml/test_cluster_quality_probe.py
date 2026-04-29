from __future__ import annotations

import numpy as np

from app.ml.cluster_quality_probe import silhouette_cosine


def test_silhouette_returns_float_for_two_clusters() -> None:
    emb: np.ndarray = np.array([[1.0, 0.0], [0.9, 0.1], [0.0, 1.0], [0.1, 0.9]], dtype=np.float64)
    labels: np.ndarray = np.array([0, 0, 1, 1], dtype=np.int64)
    score: float | None = silhouette_cosine(emb, labels)
    assert score is not None
    assert -1.0 <= score <= 1.0


def test_silhouette_none_when_single_cluster() -> None:
    emb: np.ndarray = np.ones((3, 2), dtype=np.float64)
    labels: np.ndarray = np.zeros(3, dtype=np.int64)
    assert silhouette_cosine(emb, labels) is None
