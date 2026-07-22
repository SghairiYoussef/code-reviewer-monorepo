from github import Auth, Github
from github.GithubException import GithubException
from github.PullRequest import ReviewComment as GitHubReviewComment

from app.config import settings
from app.schemas.review import DiffSide, ReviewComment
from app.vcs.models import DiffFile, PullRequestDiff, RepositoryInfo, VCSEnum


class GitHubClient:
    def _client(self, installation_id: int) -> Github:
        app_id = settings.github_app_id
        private_key = settings.github_private_key.get_secret_value()
        if not app_id or not private_key:
            raise RuntimeError("GitHub App credentials are not configured")
        app_auth = Auth.AppAuth(int(app_id), private_key)
        return Github(
            auth=app_auth.get_installation_auth(installation_id),
            base_url=settings.github_api_url,
        )

    def get_pull_request_diff(
        self, repo: str, pr_number: int, installation_id: int
    ) -> PullRequestDiff:
        repository = self._client(installation_id).get_repo(repo)
        pull = repository.get_pull(pr_number)
        files = [
            DiffFile(
                old_path=getattr(item, "previous_filename", None) or item.filename,
                new_path=item.filename,
                status=item.status,
                patch=item.patch or "",
                additions=item.additions,
                deletions=item.deletions,
                is_binary=item.patch is None,
            )
            for item in pull.get_files()
        ]
        return PullRequestDiff(base_sha=pull.base.sha, head_sha=pull.head.sha, files=files)

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
        repository = self._client(installation_id).get_repo(repo)
        pull = repository.get_pull(pr_number)
        marker = f"<!-- ai-code-review:{review_key} -->"
        if any(marker in (review.body or "") for review in pull.get_reviews()):
            return
        api_comments: list[GitHubReviewComment] = []
        for comment in comments:
            api_comments.append(
                {
                    "path": comment.location.file_path,
                    "line": comment.location.line,
                    "side": "RIGHT" if comment.location.side == DiffSide.right else "LEFT",
                    "body": (
                        f"**{comment.severity.value} · {comment.category.value}**\n\n"
                        f"{comment.explanation}\n\nSuggestion: {comment.suggestion}"
                    ),
                }
            )
        pull.create_review(
            body=f"{summary}\n\n{marker}",
            commit=repository.get_commit(head_sha),
            event="COMMENT",
            comments=api_comments,
        )

    def get_file_contents(self, repo: str, path: str, ref: str, installation_id: int) -> str:
        try:
            contents = self._client(installation_id).get_repo(repo).get_contents(path, ref=ref)
        except GithubException as exc:
            if exc.status == 404:
                raise FileNotFoundError(path) from exc
            raise
        if isinstance(contents, list):
            raise ValueError(f"Expected file but found directory: {path}")
        return contents.decoded_content.decode("utf-8")

    def get_repository(self, repo: str, installation_id: int) -> RepositoryInfo:
        repository = self._client(installation_id).get_repo(repo)
        return RepositoryInfo(
            full_name=repository.full_name,
            default_branch=repository.default_branch,
            language=repository.language,
            vcs_type=VCSEnum.github,
        )
