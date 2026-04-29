from fastapi import APIRouter

from app.api.routes import engagement, health, moderation, news, pipeline, provenance

api_router: APIRouter = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(engagement.router, prefix="/engagement", tags=["engagement"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(moderation.router, prefix="/moderation", tags=["moderation"])
api_router.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
api_router.include_router(provenance.router)
