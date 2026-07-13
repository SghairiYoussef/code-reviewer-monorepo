from abc import ABC, abstractmethod

from app.schemas.review import ReviewComment
from app.vcs.models import RepositoryInfo, WebhookEvent


class VCSProvider(ABC):
    @property
    @abstractmethod
    def vcs_type(self) -> str: ...

    @abstractmethod
    def validate_webhook(self, headers: dict[str, str], body: bytes) -> bool: ...

    @abstractmethod
    def parse_webhook_event(self, headers: dict[str, str], body: dict) -> WebhookEvent: ...

    @abstractmethod
    async def get_diff(self, repo: str, pr_number: int, head_sha: str) -> str: ...

    @abstractmethod
    async def post_review(
        self,
        repo: str,
        pr_number: int,
        comments: list[ReviewComment],
        summary: str,
        head_sha: str,
    ) -> None: ...

    @abstractmethod
    async def get_file_contents(self, repo: str, path: str, ref: str) -> str: ...

    @abstractmethod
    async def get_repo_info(self, repo: str) -> RepositoryInfo: ...
