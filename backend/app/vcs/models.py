from enum import StrEnum

from pydantic import BaseModel, Field


class VCSEnum(StrEnum):
    github = "github"
    gitlab = "gitlab"


class WebhookEvent(BaseModel):
    vcs_type: VCSEnum
    action: str
    delivery_id: str
    provider_host: str
    repository_id: str
    repo_full_name: str
    pr_number: int
    installation_id: int
    base_sha: str
    head_sha: str
    pr_title: str
    pr_body: str | None = None


class RepositoryInfo(BaseModel):
    full_name: str
    default_branch: str
    language: str | None = None
    vcs_type: VCSEnum


class DiffFile(BaseModel):
    old_path: str
    new_path: str
    status: str
    patch: str = ""
    additions: int = Field(default=0, ge=0)
    deletions: int = Field(default=0, ge=0)
    is_binary: bool = False


class PullRequestDiff(BaseModel):
    base_sha: str
    head_sha: str
    files: list[DiffFile]
