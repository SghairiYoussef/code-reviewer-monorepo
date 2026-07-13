class GitLabClient:
    async def get_merge_request_diff(self, repo: str, mr_number: int) -> str:
        raise NotImplementedError

    async def post_merge_request_comment(self, repo: str, mr_number: int, comment: dict) -> None:
        raise NotImplementedError

    async def post_mr_note(self, repo: str, mr_number: int, body: str) -> None:
        raise NotImplementedError

    async def get_file_contents(self, repo: str, path: str, ref: str) -> str:
        raise NotImplementedError

    async def get_project(self, repo: str) -> dict:
        raise NotImplementedError
