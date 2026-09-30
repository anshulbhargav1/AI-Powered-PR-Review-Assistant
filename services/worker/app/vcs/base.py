from abc import ABC, abstractmethod

from pr_review_shared.schemas import CodeFileDiff, PRReviewInput


class VCSClient(ABC):
    """Uniform interface over GitHub / GitLab so the workflow/activities never
    branch on provider directly."""

    @abstractmethod
    def refresh_pr_state(self, review_input: PRReviewInput) -> dict:
        """Re-fetch current PR/MR state from the API (webhooks can be stale).
        Returns a small dict with at least {"open": bool, "changed_files": int}."""

    @abstractmethod
    def get_diff(self, review_input: PRReviewInput) -> list[CodeFileDiff]:
        """Fetch the per-file unified diff for the PR/MR."""

    @abstractmethod
    def upsert_comment(self, review_input: PRReviewInput, marker: str, body: str) -> str:
        """Create or update the single bot comment (identified by `marker`) on the PR/MR.
        Returns a URL to the comment/PR."""

    @abstractmethod
    def set_commit_status(
        self,
        repo_full_name: str,
        commit_sha: str,
        state: str,
        description: str,
        target_url: str | None = None,
    ) -> None:
        """Set the commit status on the head commit. `state` is one of
        "success" | "failure" | "pending" (GitHub semantics); providers map internally."""
