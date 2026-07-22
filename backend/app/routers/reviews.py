from fastapi import APIRouter, HTTPException, Query

from app.models.review import Review

router = APIRouter()


@router.get("")
async def list_reviews(
    limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0)
) -> list[Review]:
    return await Review.find_all().sort("-created_at").skip(offset).limit(limit).to_list()


@router.get("/{review_id}")
async def get_review(review_id: str) -> Review:
    try:
        review = await Review.get(review_id)
    except Exception as exc:
        raise HTTPException(404, "Review not found") from exc
    if review is None:
        raise HTTPException(404, "Review not found")
    return review
