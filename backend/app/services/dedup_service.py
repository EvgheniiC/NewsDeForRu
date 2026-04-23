import hashlib
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class DedupResult:
    cluster_key: str


class DedupService:
    @staticmethod
    def _normalize(text: str) -> str:
        normalized: str = re.sub(r"[^a-zA-Z0-9äöüÄÖÜß ]", " ", text)
        normalized = re.sub(r"\s+", " ", normalized).strip().lower()
        return normalized

    def cluster(self, title: str, summary: str) -> DedupResult:
        normalized: str = self._normalize(f"{title} {summary}")
        fingerprint: str = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return DedupResult(cluster_key=fingerprint[:16])
