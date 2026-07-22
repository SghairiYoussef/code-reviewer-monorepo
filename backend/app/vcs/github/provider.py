from typing import Any
from urllib.parse import urlparse

from app.config import settings
from app.schemas.review import ReviewComment
from app.vcs.base import VCSProvider
from app.vcs.github.client import GitHubClient
from app.vcs.github.webhook import GitHubWebhookValidator
from app.vcs.models import PullRequestDiff, RepositoryInfo, VCSEnum, WebhookEvent


class GitHubProvider(VCSProvider):
    def __init__(self) -> None:
        self._webhook = GitHubWebhookValidator(settings.github_webhook_secret.get_secret_value())
        self._client = GitHubClient()

    @property
    def vcs_type(self) -> str:
        return "github"

    def validate_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        return self._webhook.validate(headers, body)

    def parse_webhook_event(
        self, headers: dict[str, str], body: dict[str, Any]
    ) -> WebhookEvent | None:
        if self._webhook.extract_event_type(headers) != "pull_request":
            return None
        action = body.get("action", "")
        if action not in {"opened", "reopened", "synchronize", "ready_for_review"}:
            return None
        try:
            pull = body["pull_request"]
            repository = body["repository"]
            installation = body["installation"]
            host = urlparse(repository["html_url"]).hostname or "github.com"
            expected_host = urlparse(settings.github_web_url).hostname
            if expected_host is None or host.casefold() != expected_host.casefold():
                raise ValueError("Webhook repository host is not configured")
            return WebhookEvent(
                vcs_type=VCSEnum.github,
                action=action,
                delivery_id=headers["x-github-delivery"],
                provider_host=host,
                repository_id=str(repository["id"]),
                repo_full_name=repository["full_name"],
                pr_number=int(body["number"]),
                installation_id=int(installation["id"]),
                base_sha=pull["base"]["sha"],
                head_sha=pull["head"]["sha"],
                pr_title=pull["title"],
                pr_body=pull.get("body"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Malformed GitHub pull_request webhook") from exc

    def get_diff(self, repo: str, pr_number: int, installation_id: int) -> PullRequestDiff:
        return self._client.get_pull_request_diff(repo, pr_number, installation_id)

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
        self._client.post_review(
            repo, pr_number, comments, summary, head_sha, installation_id, review_key
        )

    def get_file_contents(self, repo: str, path: str, ref: str, installation_id: int) -> str:
        return self._client.get_file_contents(repo, path, ref, installation_id)

    def get_repo_info(self, repo: str, installation_id: int) -> RepositoryInfo:
        return self._client.get_repository(repo, installation_id)
