import logging
from collections.abc import Generator
from datetime import datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool, StaticPool

from app.core.config import settings

logger: logging.Logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def _make_engine(url: str) -> Engine:
    if ":memory:" in url:
        return create_engine(
            url,
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    # File-based SQLite: avoid pooled connections sticking across threads (scheduler + API),
    # and cap wait on DB busy lock so /health does not hang indefinitely.
    if url.strip().lower().startswith("sqlite"):
        return create_engine(
            url,
            future=True,
            connect_args={"check_same_thread": False, "timeout": 20.0},
            poolclass=NullPool,
        )
    return create_engine(url, future=True)


engine = _make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db_session() -> Generator[Session, None, None]:
    db_session: Session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def repair_implausible_published_dates(session: Session) -> int:
    """Rewrite stored publication times whose year cannot be real. Returns the row count."""
    from app.models.news import RawNewsItem
    from app.services.rss_entry_normalization import (
        correct_published_at,
        earliest_implausible_published_at,
    )

    rows: list[RawNewsItem] = list(
        session.scalars(
            select(RawNewsItem).where(
                RawNewsItem.published_at >= earliest_implausible_published_at()
            )
        )
    )
    fixed: int = 0
    for row in rows:
        corrected: datetime = correct_published_at(row.published_at)
        if corrected == row.published_at:
            continue
        row.published_at = corrected
        fixed += 1
    if fixed:
        session.commit()
    return fixed


def init_database() -> None:
    from app.models import engagement  # noqa: F401
    from app.models import job_lock  # noqa: F401
    from app.models import news  # noqa: F401
    from app.models import app_user  # noqa: F401
    from app.models import password_reset_token  # noqa: F401
    from app.models import email_verification_token  # noqa: F401
    from app.models import push_subscription  # noqa: F401
    from app.models import user_library  # noqa: F401
    from app.models import user_feed_preference  # noqa: F401
    from app.models import user_listening  # noqa: F401

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        fixed: int = repair_implausible_published_dates(session)
    if fixed:
        logger.info("corrected published_at rows with an impossible year count=%s", fixed)
