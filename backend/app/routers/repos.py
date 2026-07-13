from fastapi import APIRouter, Response

router = APIRouter()


@router.get("")
async def list_repos() -> Response:
    return Response(status_code=501, content='{"status": "not_implemented"}', media_type="application/json")


@router.post("")
async def create_repo() -> Response:
    return Response(status_code=501, content='{"status": "not_implemented"}', media_type="application/json")


@router.get("/{repo_id}")
async def get_repo(repo_id: str) -> Response:
    return Response(status_code=501, content='{"status": "not_implemented"}', media_type="application/json")


@router.put("/{repo_id}")
async def update_repo(repo_id: str) -> Response:
    return Response(status_code=501, content='{"status": "not_implemented"}', media_type="application/json")


@router.delete("/{repo_id}")
async def delete_repo(repo_id: str) -> Response:
    return Response(status_code=501, content='{"status": "not_implemented"}', media_type="application/json")
