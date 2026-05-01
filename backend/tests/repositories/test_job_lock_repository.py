from __future__ import annotations

import pytest

from app.core.database import Base, SessionLocal, engine, init_database
from app.repositories.job_lock_repository import JobLockRepository


@pytest.fixture(autouse=True)
def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    init_database()


def test_job_lock_acquire_release_cycle() -> None:
    with SessionLocal() as db:
        repo: JobLockRepository = JobLockRepository(db)
        assert repo.try_acquire("telegram_digest", "holder-a", ttl_seconds=300) is True
        assert repo.try_acquire("telegram_digest", "holder-b", ttl_seconds=300) is False
        repo.release("telegram_digest")
        assert repo.try_acquire("telegram_digest", "holder-b", ttl_seconds=300) is True
