from collections.abc import Callable

from app.llm.base import LLMProvider

_PROVIDERS: dict[str, Callable[[], LLMProvider]] = {}


def register_provider(name: str, factory: Callable[[], LLMProvider]) -> None:
    if name in _PROVIDERS:
        raise ValueError(f"LLM provider already registered: {name}")
    _PROVIDERS[name] = factory


def get_provider(name: str) -> LLMProvider:
    try:
        return _PROVIDERS[name]()
    except KeyError as exc:
        raise ValueError(f"Unknown LLM provider: {name}") from exc
