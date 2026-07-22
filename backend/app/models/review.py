from datetime import UTC, datetime
from enum import StrEnum

from beanie import Document
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.schemas.review import ReviewComment
from app.vcs.models import VCSEnum, WebhookEvent


class ReviewStatus(StrEnum):
    received = "received"
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"


class Review(Document):
    vcs_type: VCSEnum
    provider_host: str
    repository_id: str
    repo_full_name: str
    pr_number: int
    installation_id: int
    delivery_id: str
    base_sha: str
    head_sha: str
    pr_title: str
    pr_body: str | None = None
    status: ReviewStatus = ReviewStatus.received
    task_id: str | None = None
    attempts: int = 0
    summary: str | None = None
    comments: list[ReviewComment] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def from_event(cls, event: WebhookEvent) -> "Review":
        return cls(**event.model_dump())

    class Settings:
        name = "reviews"
        indexes = [
            IndexModel(
                [
                    ("vcs_type", ASCENDING),
                    ("provider_host", ASCENDING),
                    ("repository_id", ASCENDING),
                    ("pr_number", ASCENDING),
                    ("head_sha", ASCENDING),
                ],
                unique=True,
                name="unique_review_commit",
            ),
            IndexModel(
                [
                    ("vcs_type", ASCENDING),
                    ("provider_host", ASCENDING),
                    ("delivery_id", ASCENDING),
                ],
                unique=True,
                name="unique_webhook_delivery",
            ),
        ]
