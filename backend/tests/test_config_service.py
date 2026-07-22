import pytest

from app.schemas.review import CommentSeverity
from app.services.config_service import (
    meets_minimum_severity,
    merge_review_rules,
    path_is_excluded,
)


def test_repository_config_is_bounded_and_ignores_sensitive_fields() -> None:
    rules = merge_review_rules(
        "review:\n  max_comments: 5\n  excluded_paths: ['generated/**']\n"
        "  model: expensive-model\n",
        None,
    )
    assert rules.max_comments == 5
    assert path_is_excluded("generated/client.py", rules)
    assert not hasattr(rules, "model")


def test_repository_config_rejects_unbounded_values() -> None:
    with pytest.raises(ValueError):
        merge_review_rules("review:\n  max_comments: 10000\n", None)


def test_minimum_severity_is_enforced() -> None:
    assert meets_minimum_severity(CommentSeverity.critical, CommentSeverity.warning)
    assert not meets_minimum_severity(CommentSeverity.info, CommentSeverity.warning)
