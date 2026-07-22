import pytest

from app.llm import get_provider
from app.llm.openai_provider import OpenAIReviewProvider


def test_openai_provider_is_registered() -> None:
    assert isinstance(get_provider("openai"), OpenAIReviewProvider)


def test_unknown_provider_fails_closed() -> None:
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_provider("unknown")
