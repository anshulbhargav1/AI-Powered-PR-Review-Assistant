from pr_review_shared.config import settings
from pr_review_shared.schemas import Provider

from .base import VCSClient
from .github_client import GitHubClient
from .gitlab_client import GitLabClient
from .mock_client import MockVCSClient


def get_vcs_client(provider: Provider) -> VCSClient:
    if settings.vcs_mode == "mock":
        return MockVCSClient()
    if provider == Provider.github:
        return GitHubClient(token=settings.github_token)
    if provider == Provider.gitlab:
        return GitLabClient(token=settings.gitlab_token, base_url=settings.gitlab_base_url)
    raise ValueError(f"Unknown provider: {provider}")
