from datetime import UTC, datetime

from pymongo.errors import DuplicateKeyError

from app.models.review import Review, ReviewStatus
from app.vcs.models import WebhookEvent


async def accept_review(event: WebhookEvent) -> tuple[Review, bool]:
    review = Review.from_event(event)
    try:
        await review.insert()
    except DuplicateKeyError:
        existing = await Review.find_one(
            {
                "$or": [
                    {"vcs_type": event.vcs_type, "delivery_id": event.delivery_id},
                    {
                        "vcs_type": event.vcs_type,
                        "provider_host": event.provider_host,
                        "repository_id": event.repository_id,
                        "pr_number": event.pr_number,
                        "head_sha": event.head_sha,
                    },
                ]
            }
        )
        if existing is None:
            raise
        return existing, False

    from app.workers.tasks import process_review

    try:
        task = process_review.delay(str(review.id))
        review.task_id = task.id
        review.status = ReviewStatus.queued
    except Exception as exc:
        review.status = ReviewStatus.failed
        review.error = f"Failed to enqueue review: {exc}"[:2000]
        await review.save()
        raise
    review.updated_at = datetime.now(UTC)
    await review.save()
    return review, True
