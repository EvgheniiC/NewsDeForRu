from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.database import init_database

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_database()
    yield


app: FastAPI = FastAPI(title="newsForGermanyRU Backend", version="0.2.0", lifespan=lifespan)
app.include_router(api_router)