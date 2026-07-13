from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from beanie import init_beanie
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.routers import repos, reviews, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    client = AsyncIOMotorClient(settings.mongo_uri)
    await init_beanie(
        database=client.ai_code_reviewer,
        document_models=[],
    )
    yield
    client.close()


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
app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["reviews"])
app.include_router(repos.router, prefix="/api/v1/repos", tags=["repos"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
