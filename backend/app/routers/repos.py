from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError

from app.models.repository import RepositoryConfig, ReviewRules
from app.vcs.models import VCSEnum

router = APIRouter()


@router.get("")
class RepositoryConfigInput(BaseModel):
    vcs_type: VCSEnum
    provider_host: str
    repository_id: str
    repo_full_name: str
    enabled: bool = True
    enforced_rules: ReviewRules | None = None


async def list_repos(limit: int = Query(default=50, ge=1, le=100)) -> list[RepositoryConfig]:
    return await RepositoryConfig.find_all().limit(limit).to_list()


@router.post("")
async def create_repo(data: RepositoryConfigInput) -> RepositoryConfig:
    repository = RepositoryConfig(**data.model_dump())
    try:
        await repository.insert()
    except DuplicateKeyError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Repository already exists") from exc
    return repository


@router.get("/{repo_id}")
async def get_repo(repo_id: str) -> RepositoryConfig:
    try:
        repository = await RepositoryConfig.get(repo_id)
    except Exception as exc:
        raise HTTPException(404, "Repository not found") from exc
    if repository is None:
        raise HTTPException(404, "Repository not found")
    return repository


@router.put("/{repo_id}")
async def update_repo(repo_id: str, data: RepositoryConfigInput) -> RepositoryConfig:
    repository = await get_repo(repo_id)
    for key, value in data.model_dump().items():
        setattr(repository, key, value)
    repository.updated_at = datetime.now(UTC)
    await repository.save()
    return repository


@router.delete("/{repo_id}")
async def delete_repo(repo_id: str) -> dict[str, str]:
    repository = await get_repo(repo_id)
    await repository.delete()
    return {"status": "deleted"}
