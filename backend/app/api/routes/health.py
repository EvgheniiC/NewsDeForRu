from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.monitoring import last_pipeline_run

router: APIRouter = APIRouter()


@router.get("/health")
def healthcheck() -> dict[str, Any]:
    db_ok: bool
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    st = last_pipeline_run.get_state()
    last_at: str | None = st.at_utc.isoformat() if st.at_utc is not None else None
    last_ok: bool | None = None if st.at_utc is None else st.ok
    status: str = "ok" if db_ok else "degraded"
    return {
        "status": status,
        "database": "ok" if db_ok else "unavailable",
        "last_pipeline_run_at": last_at,
        "last_pipeline_ok": last_ok,
        "last_pipeline_run_id": st.run_id,
        "pipeline_scheduler": "enabled" if settings.pipeline_scheduler_enabled else "disabled",
    }
