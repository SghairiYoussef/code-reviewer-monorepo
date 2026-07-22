from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # MongoDB
    mongo_uri: str = "mongodb://localhost:27017"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # GitHub App
    github_app_id: str = ""
    github_web_url: str = "https://github.com"
    github_api_url: str = "https://api.github.com"
    github_private_key: SecretStr = SecretStr("")
    github_webhook_secret: SecretStr = SecretStr("")

    # GitLab
    gitlab_url: str = "https://gitlab.com"
    gitlab_token: SecretStr = SecretStr("")
    gitlab_webhook_secret: SecretStr = SecretStr("")

    # OpenAI
    llm_provider: str = "openai"
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-4o"

    # Celery
    celery_concurrency: int = 4

    # Protects management/read APIs. Webhooks use provider signatures instead.
    api_key: SecretStr = SecretStr("")

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
