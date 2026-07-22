from app.llm.factory import get_provider, register_provider
from app.llm.openai_provider import OpenAIReviewProvider

register_provider("openai", OpenAIReviewProvider)

__all__ = ["get_provider"]
