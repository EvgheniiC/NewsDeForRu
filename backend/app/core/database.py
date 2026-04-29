from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from sqlalchemy.engine import Engine

from app.core.config import settings


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
    return create_engine(url, future=True)


engine = _make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db_session() -> Generator[Session, None, None]:
    db_session: Session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def init_database() -> None:
    from app.models import news  # noqa: F401
    from app.models import engagement  # noqa: F401

    Base.metadata.create_all(bind=engine)
