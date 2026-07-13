class GitHubClient:
    async def get_pull_request_diff(self, repo: str, pr_number: int) -> str:
        raise NotImplementedError

    async def post_review_comment(self, repo: str, pr_number: int, comment: dict) -> None:
        raise NotImplementedError

    async def post_pr_comment(self, repo: str, pr_number: int, body: str) -> None:
        raise NotImplementedError

    async def get_file_contents(self, repo: str, path: str, ref: str) -> str:
        raise NotImplementedError

    async def get_repository(self, repo: str) -> dict:
        raise NotImplementedError
