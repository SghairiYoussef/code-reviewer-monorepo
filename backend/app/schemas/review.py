from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class CommentSeverity(StrEnum):
    critical = "critical"
    warning = "warning"
    info = "info"


class CommentCategory(StrEnum):
    security = "security"
    performance = "performance"
    bug = "bug"
    style = "style"
    maintainability = "maintainability"


class DiffSide(StrEnum):
    left = "LEFT"
    right = "RIGHT"


class SourceLocation(BaseModel):
    file_path: str = Field(min_length=1)
    line: int = Field(gt=0)
    side: DiffSide = DiffSide.right
    old_line: int | None = Field(default=None, gt=0)
    new_line: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def set_provider_coordinates(self) -> "SourceLocation":
        if self.side == DiffSide.right and self.new_line is None:
            self.new_line = self.line
        if self.side == DiffSide.left and self.old_line is None:
            self.old_line = self.line
        return self


class ReviewComment(BaseModel):
    location: SourceLocation
    suggestion: str = Field(min_length=1, max_length=4000)
    explanation: str = Field(min_length=1, max_length=4000)
    severity: CommentSeverity
    category: CommentCategory
