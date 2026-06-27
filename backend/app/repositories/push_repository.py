from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.push_subscription import PushSubscription


class PushRepository:
    def __init__(self, db_session: Session) -> None:
        self.db_session: Session = db_session

    def get_by_token(self, device_token: str) -> PushSubscription | None:
        query = select(PushSubscription).where(PushSubscription.device_token == device_token)
        return self.db_session.execute(query).scalar_one_or_none()

    def upsert_enabled(self, *, device_token: str, platform: str) -> PushSubscription:
        row: PushSubscription | None = self.get_by_token(device_token)
        now: datetime = datetime.utcnow()
        if row is None:
            row = PushSubscription(
                device_token=device_token,
                platform=platform,
                enabled=True,
                created_at=now,
                updated_at=now,
            )
            self.db_session.add(row)
        else:
            row.platform = platform
            row.enabled = True
            row.updated_at = now
            self.db_session.add(row)
        self.db_session.commit()
        self.db_session.refresh(row)
        return row

    def disable(self, device_token: str) -> bool:
        row: PushSubscription | None = self.get_by_token(device_token)
        if row is None:
            return False
        row.enabled = False
        row.updated_at = datetime.utcnow()
        self.db_session.add(row)
        self.db_session.commit()
        return True
