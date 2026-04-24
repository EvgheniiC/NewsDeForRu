from dataclasses import dataclass

from app.core.config import settings
from app.services.embedding_service import EmbeddingEncoder, create_embedding_encoder, cosine_similarity

DENY_KEYWORDS: tuple[str, ...] = ("sport", "bundesliga", "transfer", "promi", "unfall")

POSITIVE_ANCHORS: tuple[str, ...] = (
    "Mietrecht und Nebenkostenabrechnung für Mieter in Deutschland.",
    "Steuererklärung und Steuerklassen für Arbeitnehmer und Selbstständige in Deutschland.",
    "Krankenversicherung und Zusatzbeiträge der gesetzlichen Krankenkasse.",
    "Rente und gesetzliche Rentenversicherung sowie Rentenberechnung.",
    "Wohnungseigentum, Eigentümergemeinschaft und Beschlüsse der WEG.",
    "Heizkosten, Heizungsgesetz und energetische Sanierung mit Förderung.",
    "Arbeitsrecht, Kündigungsschutz, Urlaubsanspruch und Arbeitszeit.",
)

NEGATIVE_ANCHORS: tuple[str, ...] = (
    "Bundesliga Fußball Spielbericht Tabelle und Transfergerüchte.",
    "Promi Klatsch und Unterhaltungsshows ohne Bezug zum Alltag in Deutschland.",
    "Sport Wettkampf Olympische Spiele Medaillen und Spielergebnisse.",
)


@dataclass(frozen=True)
class RelevanceResult:
    is_relevant: bool
    score: float
    reason: str


class RelevanceFilterService:
    def __init__(self, encoder: EmbeddingEncoder | None = None) -> None:
        self._encoder: EmbeddingEncoder = encoder or create_embedding_encoder()
        self._positive_embeddings: list[list[float]] | None = None
        self._negative_embeddings: list[list[float]] | None = None

    def _ensure_anchor_embeddings(self) -> tuple[list[list[float]], list[list[float]]]:
        if self._positive_embeddings is None:
            self._positive_embeddings = [self._encoder.encode_normalized(t) for t in POSITIVE_ANCHORS]
            self._negative_embeddings = [self._encoder.encode_normalized(t) for t in NEGATIVE_ANCHORS]
        return self._positive_embeddings, self._negative_embeddings

    def evaluate(self, title: str, summary: str) -> RelevanceResult:
        text_lower: str = f"{title} {summary}".lower()
        if any(keyword in text_lower for keyword in DENY_KEYWORDS):
            return RelevanceResult(is_relevant=False, score=0.1, reason="Denied by topic keyword.")

        combined: str = f"{title}\n{summary}".strip()
        embedding: list[float] = self._encoder.encode_normalized(combined)
        positive_vectors, negative_vectors = self._ensure_anchor_embeddings()

        max_positive: float = max(cosine_similarity(embedding, p) for p in positive_vectors)
        max_negative: float = max(cosine_similarity(embedding, n) for n in negative_vectors)

        if max_negative > max_positive:
            return RelevanceResult(
                is_relevant=False,
                score=float(max_positive),
                reason="Closer to off-topic anchors than life-impact topics.",
            )

        min_score: float = settings.semantic_relevance_min_score
        if max_positive < min_score:
            return RelevanceResult(
                is_relevant=False,
                score=float(max_positive),
                reason="Below semantic relevance threshold.",
            )

        return RelevanceResult(
            is_relevant=True,
            score=float(max_positive),
            reason="Semantic match to life-impact topics.",
        )
