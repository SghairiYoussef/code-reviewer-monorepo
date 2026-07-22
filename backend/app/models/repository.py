from datetime import UTC, datetime

from beanie import Document
from pydantic import BaseModel, Field
from pymongo import ASCENDING, IndexModel

from app.schemas.review import CommentSeverity
from app.vcs.models import VCSEnum


class ReviewRules(BaseModel):
    enabled: bool = True
    max_files: int = Field(default=50, ge=1, le=200)
    max_comments: int = Field(default=20, ge=1, le=100)
    excluded_paths: list[str] = Field(default_factory=lambda: ["*.lock", "vendor/**", "dist/**"])
    minimum_severity: CommentSeverity = CommentSeverity.info


class RepositoryConfig(Document):
    vcs_type: VCSEnum
    provider_host: str
    repository_id: str
    repo_full_name: str
    enabled: bool = True
    # These trusted server-side values override repository-file values.
    enforced_rules: ReviewRules | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "repository_configs"
        indexes = [
            IndexModel(
                [
                    ("vcs_type", ASCENDING),
                    ("provider_host", ASCENDING),
                    ("repository_id", ASCENDING),
                ],
                unique=True,
            )
        ]
