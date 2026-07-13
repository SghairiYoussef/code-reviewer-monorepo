from enum import Enum

from pydantic import BaseModel


class CommentSeverity(str, Enum):
    critical = "critical"
    warning = "warning"
    info = "info"


class CommentCategory(str, Enum):
    security = "security"
    performance = "performance"
    bug = "bug"
    style = "style"
    maintainability = "maintainability"


class ReviewComment(BaseModel):
    file_path: str
    line: int
    suggestion: str
    explanation: str
    severity: CommentSeverity
    category: CommentCategory
