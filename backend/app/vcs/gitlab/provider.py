from typing import Any

from app.schemas.review import ReviewComment
from app.vcs.base import VCSProvider
from app.vcs.gitlab.client import GitLabClient
from app.vcs.gitlab.webhook import GitLabWebhookValidator
from app.vcs.models import PullRequestDiff, RepositoryInfo, WebhookEvent


class GitLabProvider(VCSProvider):
    def __init__(self) -> None:
        self._webhook = GitLabWebhookValidator()
        self._client = GitLabClient()

    @property
    def vcs_type(self) -> str:
        return "gitlab"

    def validate_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        raise NotImplementedError

    def parse_webhook_event(
        self, headers: dict[str, str], body: dict[str, Any]
    ) -> WebhookEvent | None:
        raise NotImplementedError

    def get_diff(self, repo: str, pr_number: int, installation_id: int) -> PullRequestDiff:
        raise NotImplementedError

    def post_review(
        self,
        repo: str,
        pr_number: int,
        comments: list[ReviewComment],
        summary: str,
        head_sha: str,
        installation_id: int,
        review_key: str,
    ) -> None:
        raise NotImplementedError

    def get_file_contents(self, repo: str, path: str, ref: str, installation_id: int) -> str:
        raise NotImplementedError

    def get_repo_info(self, repo: str, installation_id: int) -> RepositoryInfo:
        raise NotImplementedError
