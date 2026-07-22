from pydantic import BaseModel, Field

from app.schemas.review import ReviewComment


class ReviewResult(BaseModel):
    summary: str = Field(min_length=1, max_length=8000)
    comments: list[ReviewComment] = Field(default_factory=list)
