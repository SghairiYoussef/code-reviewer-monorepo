from fastapi import APIRouter, Response

router = APIRouter()


@router.get("")
async def list_reviews() -> Response:
    return Response(status_code=501, content='{"status": "not_implemented"}', media_type="application/json")


@router.get("/{review_id}")
async def get_review(review_id: str) -> Response:
    return Response(status_code=501, content='{"status": "not_implemented"}', media_type="application/json")
