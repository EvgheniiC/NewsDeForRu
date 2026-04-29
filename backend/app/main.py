from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.router import api_router
from app.core.config import settings
from app.core.database import init_database
from app.core.logging_config import configure_logging
from app.workers.scheduler import create_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    if settings.sentry_dsn.strip():
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.sentry_dsn.strip(),
            traces_sample_rate=0.1,
            environment=settings.app_env,
        )
    init_database()
    sched: BackgroundScheduler | None = None
    if settings.pipeline_scheduler_enabled:
        sched = create_scheduler()
        sched.start()
    try:
        yield
    finally:
        if sched is not None:
            sched.shutdown(wait=False)


app: FastAPI = FastAPI(title="newsForGermanyRU Backend", version="0.2.0", lifespan=lifespan)

_cors_origins: list[str] = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router)


@app.get("/metrics", include_in_schema=False)
def prometheus_metrics_endpoint() -> Response:
    """Prometheus exposition (enable with ``PROMETHEUS_METRICS_ENABLED=true`` only)."""
    if not settings.prometheus_metrics_enabled:
        raise HTTPException(status_code=404, detail="Not found")
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)