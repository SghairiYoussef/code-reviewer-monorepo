import re

from app.schemas.review import DiffSide, ReviewComment
from app.vcs.models import PullRequestDiff

_HUNK = re.compile(r"^@@ -(?P<old>\d+)(?:,\d+)? \+(?P<new>\d+)(?:,\d+)? @@")


def reviewable_locations(diff: PullRequestDiff) -> set[tuple[str, int, DiffSide]]:
    locations: set[tuple[str, int, DiffSide]] = set()
    for file in diff.files:
        old_line = new_line = 0
        for line in file.patch.splitlines():
            match = _HUNK.match(line)
            if match:
                old_line, new_line = int(match["old"]), int(match["new"])
            elif line.startswith("+") and not line.startswith("+++"):
                locations.add((file.new_path, new_line, DiffSide.right))
                new_line += 1
            elif line.startswith("-") and not line.startswith("---"):
                locations.add((file.old_path, old_line, DiffSide.left))
                old_line += 1
            elif not line.startswith("\\"):
                old_line += 1
                new_line += 1
    return locations


def valid_comments(comments: list[ReviewComment], diff: PullRequestDiff) -> list[ReviewComment]:
    allowed = reviewable_locations(diff)
    return [
        comment
        for comment in comments
        if (comment.location.file_path, comment.location.line, comment.location.side) in allowed
    ]
