from collections.abc import AsyncGenerator

from app.config import Settings, settings


async def get_settings() -> AsyncGenerator[Settings, None]:
    yield settings
