from abc import ABC, abstractmethod
from typing import Any

from app.schemas.review import ReviewComment
from app.vcs.models import PullRequestDiff, RepositoryInfo, WebhookEvent


class VCSProvider(ABC):
    @property
    @abstractmethod
    def vcs_type(self) -> str: ...

    @abstractmethod
    def validate_webhook(self, headers: dict[str, str], body: bytes) -> bool: ...

    @abstractmethod
    def parse_webhook_event(
        self, headers: dict[str, str], body: dict[str, Any]
    ) -> WebhookEvent | None: ...

    @abstractmethod
    def get_diff(self, repo: str, pr_number: int, installation_id: int) -> PullRequestDiff: ...

    @abstractmethod
    def post_review(
        self,
        repo: str,
        pr_number: int,
        comments: list[ReviewComment],
        summary: str,
        head_sha: str,
        installation_id: int,
        review_key: str,
    ) -> None: ...

    @abstractmethod
    def get_file_contents(self, repo: str, path: str, ref: str, installation_id: int) -> str: ...

    @abstractmethod
    def get_repo_info(self, repo: str, installation_id: int) -> RepositoryInfo: ...
