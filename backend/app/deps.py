import secrets

from fastapi import Header, HTTPException, status

from app.config import Settings, settings


def get_settings() -> Settings:
    return settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    configured = settings.api_key.get_secret_value()
    if not configured:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Management API is disabled")
    if x_api_key is None or not secrets.compare_digest(x_api_key, configured):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
