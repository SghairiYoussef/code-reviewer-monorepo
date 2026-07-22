from typing import Any


class GitLabClient:
    def get_merge_request_diff(self, repo: str, mr_number: int) -> str:
        raise NotImplementedError

    def post_merge_request_comment(
        self, repo: str, mr_number: int, comment: dict[str, Any]
    ) -> None:
        raise NotImplementedError

    def post_mr_note(self, repo: str, mr_number: int, body: str) -> None:
        raise NotImplementedError

    def get_file_contents(self, repo: str, path: str, ref: str) -> str:
        raise NotImplementedError

    def get_project(self, repo: str) -> dict[str, Any]:
        raise NotImplementedError
