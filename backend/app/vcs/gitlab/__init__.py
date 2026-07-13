from app.vcs.factory import register_provider
from app.vcs.gitlab.provider import GitLabProvider

register_provider("gitlab", GitLabProvider)
