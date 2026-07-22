import asyncio
from datetime import UTC, datetime
from typing import Any

from celery.utils.log import get_task_logger

from app.config import settings
from app.database import create_database_client
from app.llm import get_provider as get_llm_provider
from app.models.repository import RepositoryConfig
from app.models.review import Review, ReviewStatus
from app.services.config_service import (
    meets_minimum_severity,
    merge_review_rules,
    path_is_excluded,
)
from app.services.diff_service import valid_comments
from app.vcs.factory import get_provider
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


async def _process_review(review_id: str) -> None:
    client = await create_database_client()
    try:
        review = await Review.get(review_id)
        if review is None or review.status in {ReviewStatus.completed, ReviewStatus.skipped}:
            return

        review.status = ReviewStatus.running
        review.attempts += 1
        review.updated_at = datetime.now(UTC)
        await review.save()

        provider = get_provider(review.vcs_type.value)
        diff = provider.get_diff(review.repo_full_name, review.pr_number, review.installation_id)
        if diff.head_sha != review.head_sha:
            review.status = ReviewStatus.skipped
            review.error = "Pull request head changed before review started"
            review.updated_at = datetime.now(UTC)
            await review.save()
            return

        repository_config = await RepositoryConfig.find_one(
            RepositoryConfig.vcs_type == review.vcs_type,
            RepositoryConfig.provider_host == review.provider_host,
            RepositoryConfig.repository_id == review.repository_id,
        )
        repo_file: str | None = None
        try:
            repo_file = provider.get_file_contents(
                review.repo_full_name,
                ".codereview.yml",
                review.base_sha,
                review.installation_id,
            )
        except FileNotFoundError:
            logger.info("No trusted repository config for review %s", review_id)

        rules = merge_review_rules(repo_file, repository_config)
        if not rules.enabled or (repository_config and not repository_config.enabled):
            review.status = ReviewStatus.skipped
            review.updated_at = datetime.now(UTC)
            await review.save()
            return

        diff.files = [
            file
            for file in diff.files
            if not file.is_binary and not path_is_excluded(file.new_path, rules)
        ][: rules.max_files]
        if not diff.files:
            review.status = ReviewStatus.skipped
            review.error = "No reviewable changed files"
            review.updated_at = datetime.now(UTC)
            await review.save()
            return
        result = get_llm_provider(settings.llm_provider).review(
            diff, review.pr_title, review.pr_body
        )
        comments = [
            comment
            for comment in valid_comments(result.comments, diff)
            if meets_minimum_severity(comment.severity, rules.minimum_severity)
        ][: rules.max_comments]
        provider.post_review(
            review.repo_full_name,
            review.pr_number,
            comments,
            result.summary,
            review.head_sha,
            review.installation_id,
            review_id,
        )
        review.summary = result.summary
        review.comments = comments
        review.status = ReviewStatus.completed
        review.error = None
        review.updated_at = datetime.now(UTC)
        await review.save()
    except Exception as exc:
        review = await Review.get(review_id)
        if review is not None:
            review.status = ReviewStatus.failed
            review.error = str(exc)[:2000]
            review.updated_at = datetime.now(UTC)
            await review.save()
        raise
    finally:
        await client.close()


@celery_app.task(bind=True, max_retries=3, name="reviews.process")  # type: ignore[untyped-decorator]
def process_review(self: Any, review_id: str) -> None:
    try:
        asyncio.run(_process_review(review_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=min(300, 2 ** (self.request.retries + 1))) from exc
