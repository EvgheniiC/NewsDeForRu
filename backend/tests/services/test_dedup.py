from app.services.dedup_service import DedupService


def test_dedup_returns_deterministic_cluster() -> None:
    service = DedupService()
    first = service.cluster("Steuerreform 2026", "Neue Regeln fuer Mieter und Eigentuemer.")
    second = service.cluster("Steuerreform 2026", "Neue Regeln fuer Mieter und Eigentuemer.")
    assert first.cluster_key == second.cluster_key
