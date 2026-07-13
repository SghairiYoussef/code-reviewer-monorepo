from app.schemas.review import ReviewComment
from app.vcs.base import VCSProvider
from app.vcs.github.client import GitHubClient
from app.vcs.github.webhook import GitHubWebhookValidator
from app.vcs.models import RepositoryInfo, WebhookEvent


class GitHubProvider(VCSProvider):
    def __init__(self) -> None:
        self._webhook = GitHubWebhookValidator()
        self._client = GitHubClient()

    @property
    def vcs_type(self) -> str:
        return "github"

    def validate_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        raise NotImplementedError

    def parse_webhook_event(self, headers: dict[str, str], body: dict) -> WebhookEvent:
        raise NotImplementedError

    async def get_diff(self, repo: str, pr_number: int, head_sha: str) -> str:
        raise NotImplementedError

    async def post_review(
        self,
        repo: str,
        pr_number: int,
        comments: list[ReviewComment],
        summary: str,
        head_sha: str,
    ) -> None:
        raise NotImplementedError

    async def get_file_contents(self, repo: str, path: str, ref: str) -> str:
        raise NotImplementedError

    async def get_repo_info(self, repo: str) -> RepositoryInfo:
        raise NotImplementedError
