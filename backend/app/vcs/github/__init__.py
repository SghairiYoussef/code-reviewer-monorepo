from app.vcs.factory import register_provider
from app.vcs.github.provider import GitHubProvider

register_provider("github", GitHubProvider)
