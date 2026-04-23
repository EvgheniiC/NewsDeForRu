from fastapi import APIRouter

from app.api.routes import health, moderation, news, pipeline

api_router: APIRouter = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(moderation.router, prefix="/moderation", tags=["moderation"])
api_router.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
