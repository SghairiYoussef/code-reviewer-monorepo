from fnmatch import fnmatch
from typing import Any

import yaml

from app.models.repository import RepositoryConfig, ReviewRules
from app.schemas.review import CommentSeverity

_SAFE_REPO_FIELDS = {"enabled", "max_files", "max_comments", "excluded_paths", "minimum_severity"}
_MAX_CONFIG_BYTES = 64 * 1024


def merge_review_rules(
    repository_file: str | None, database_config: RepositoryConfig | None
) -> ReviewRules:
    values: dict[str, Any] = {}
    if repository_file:
        if len(repository_file.encode()) > _MAX_CONFIG_BYTES:
            raise ValueError(".codereview.yml exceeds 64 KiB")
        parsed = yaml.safe_load(repository_file) or {}
        if not isinstance(parsed, dict):
            raise ValueError(".codereview.yml must contain a mapping")
        review_values = parsed.get("review", parsed)
        if not isinstance(review_values, dict):
            raise ValueError("review configuration must contain a mapping")
        values.update(
            {key: value for key, value in review_values.items() if key in _SAFE_REPO_FIELDS}
        )

    rules = ReviewRules.model_validate(values)
    if database_config and database_config.enforced_rules:
        rules = database_config.enforced_rules
    return rules


def path_is_excluded(path: str, rules: ReviewRules) -> bool:
    return any(fnmatch(path, pattern) for pattern in rules.excluded_paths)


def meets_minimum_severity(severity: CommentSeverity, minimum: CommentSeverity) -> bool:
    rank = {
        CommentSeverity.info: 0,
        CommentSeverity.warning: 1,
        CommentSeverity.critical: 2,
    }
    return rank[severity] >= rank[minimum]
