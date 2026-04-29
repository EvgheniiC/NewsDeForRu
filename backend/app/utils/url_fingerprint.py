"""Non-reversible short fingerprint for correlating URLs in logs without storing full URLs."""

from __future__ import annotations

import hashlib


def url_fingerprint(url: str, *, hex_prefix_len: int = 16) -> str:
    digest: str = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return digest[:hex_prefix_len]
