from typing import Any

from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.config import settings
from app.models import RepositoryConfig, Review


async def create_database_client() -> AsyncMongoClient[dict[str, Any]]:
    client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(settings.mongo_uri)
    await init_beanie(
        database=client.ai_code_reviewer,
        document_models=[Review, RepositoryConfig],
    )
    return client
