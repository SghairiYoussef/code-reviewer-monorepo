from abc import ABC, abstractmethod

from app.llm.models import ReviewResult
from app.vcs.models import PullRequestDiff


class LLMProvider(ABC):
    @abstractmethod
    def review(self, diff: PullRequestDiff, title: str, body: str | None) -> ReviewResult: ...
