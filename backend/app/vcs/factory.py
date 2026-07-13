from app.vcs.base import VCSProvider
from app.vcs.models import VCSEnum

_PROVIDERS: dict[str, type[VCSProvider]] = {}


def register_provider(vcs_type: str, provider_cls: type[VCSProvider]) -> None:
    _PROVIDERS[vcs_type] = provider_cls


def get_provider(vcs_type: str) -> VCSProvider:
    cls = _PROVIDERS.get(vcs_type)
    if cls is None:
        raise ValueError(f"Unknown VCS provider: {vcs_type}")
    return cls()


def detect_vcs_type(headers: dict[str, str]) -> VCSEnum | None:
    if "x-github-event" in headers:
        return VCSEnum.github
    if "x-gitlab-event" in headers:
        return VCSEnum.gitlab
    return None
