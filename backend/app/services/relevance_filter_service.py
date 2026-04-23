from dataclasses import dataclass


ALLOW_KEYWORDS: tuple[str, ...] = (
    "gesetz",
    "miete",
    "steuer",
    "versicherung",
    "rente",
    "wohnung",
    "krankenkasse",
    "gesundheit",
    "heizung",
)

DENY_KEYWORDS: tuple[str, ...] = ("sport", "bundesliga", "transfer", "promi", "unfall")


@dataclass(frozen=True)
class RelevanceResult:
    is_relevant: bool
    score: float
    reason: str


class RelevanceFilterService:
    def evaluate(self, title: str, summary: str) -> RelevanceResult:
        text: str = f"{title} {summary}".lower()

        if any(keyword in text for keyword in DENY_KEYWORDS):
            return RelevanceResult(is_relevant=False, score=0.1, reason="Denied by topic keyword.")

        hit_count: int = sum(1 for keyword in ALLOW_KEYWORDS if keyword in text)
        if hit_count == 0:
            return RelevanceResult(is_relevant=False, score=0.2, reason="No useful life-impact signals.")

        score: float = min(0.3 + (hit_count * 0.15), 1.0)
        return RelevanceResult(is_relevant=True, score=score, reason="Matched life-impact keywords.")
