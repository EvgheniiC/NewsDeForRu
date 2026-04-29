"""Prototype cluster-quality metrics using sklearn (dev/tests). Gold labels required for real evaluation."""

from __future__ import annotations

import numpy as np


def silhouette_cosine(embeddings: np.ndarray, labels: np.ndarray) -> float | None:
    """Mean silhouette coefficient (cosine) if sklearn is installed; ``None`` if degenerate."""

    if embeddings.ndim != 2 or labels.ndim != 1:
        return None
    n_rows: int = int(embeddings.shape[0])
    if n_rows < 2 or int(labels.shape[0]) != n_rows:
        return None
    unique_labels: np.ndarray = np.unique(labels)
    if unique_labels.size < 2:
        return None
    try:
        from sklearn.metrics import silhouette_score  # type: ignore[import-untyped]
    except ImportError:
        return None
    return float(silhouette_score(embeddings, labels, metric="cosine"))
