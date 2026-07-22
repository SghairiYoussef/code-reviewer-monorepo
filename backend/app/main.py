from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from app.config import settings
from app.database import create_database_client
from app.deps import require_api_key
from app.routers import repos, reviews, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    client = await create_database_client()
    redis = Redis.from_url(settings.redis_url)
    app.state.mongo = client
    app.state.redis = redis
    yield
    await redis.aclose()
    await client.close()


app = FastAPI(
    title="AI Code Reviewer",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
protected = [Depends(require_api_key)]
app.include_router(
    reviews.router, prefix="/api/v1/reviews", tags=["reviews"], dependencies=protected
)
app.include_router(repos.router, prefix="/api/v1/repos", tags=["repos"], dependencies=protected)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def readiness_check() -> dict[str, str]:
    try:
        await app.state.mongo.admin.command("ping")
        await app.state.redis.ping()
    except Exception as exc:
        raise HTTPException(503, "A required dependency is unavailable") from exc
    return {"status": "ready"}
