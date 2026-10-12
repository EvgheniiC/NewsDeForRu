"""Per-account listen queue and playback progress, synced across devices."""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserListeningState(Base):
    """One JSON document per user: queue order, chunk index, auto-next."""

    __tablename__ = "user_listening_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    state_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
