from app.schemas.review import (
    CommentCategory,
    CommentSeverity,
    DiffSide,
    ReviewComment,
    SourceLocation,
)
from app.services.diff_service import reviewable_locations, valid_comments
from app.vcs.models import DiffFile, PullRequestDiff


def sample_diff() -> PullRequestDiff:
    return PullRequestDiff(
        base_sha="base",
        head_sha="head",
        files=[
            DiffFile(
                old_path="app.py",
                new_path="app.py",
                status="modified",
                patch="@@ -10,2 +10,2 @@\n-old\n+new\n context",
                additions=1,
                deletions=1,
            )
        ],
    )


def make_comment(line: int) -> ReviewComment:
    return ReviewComment(
        location=SourceLocation(file_path="app.py", line=line, side=DiffSide.right),
        suggestion="Use the validated value.",
        explanation="The current value is not validated.",
        severity=CommentSeverity.warning,
        category=CommentCategory.bug,
    )


def test_changed_line_coordinates_and_validation() -> None:
    diff = sample_diff()
    assert ("app.py", 10, DiffSide.left) in reviewable_locations(diff)
    assert ("app.py", 10, DiffSide.right) in reviewable_locations(diff)
    assert valid_comments([make_comment(10), make_comment(99)], diff) == [make_comment(10)]
