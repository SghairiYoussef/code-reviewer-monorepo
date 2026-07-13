from enum import Enum

from pydantic import BaseModel


class VCSEnum(str, Enum):
    github = "github"
    gitlab = "gitlab"


class WebhookEvent(BaseModel):
    vcs_type: VCSEnum
    action: str
    repo_full_name: str
    pr_number: int
    head_sha: str
    pr_title: str
    pr_body: str | None = None


class RepositoryInfo(BaseModel):
    full_name: str
    default_branch: str
    language: str | None = None
    vcs_type: VCSEnum
