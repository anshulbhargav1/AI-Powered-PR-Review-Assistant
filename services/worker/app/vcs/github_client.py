import logging

import httpx

from pr_review_shared.schemas import CodeFileDiff, PRReviewInput

from .base import VCSClient

logger = logging.getLogger(__name__)

TOTAL_PATCH_BUDGET_CHARS = 12000


class GitHubClient(VCSClient):
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )

    def refresh_pr_state(self, review_input: PRReviewInput) -> dict:
        resp = self._client.get(f"/repos/{review_input.repo_full_name}/pulls/{review_input.pr_number}")
        resp.raise_for_status()
        data = resp.json()
        return {"open": data.get("state") == "open", "changed_files": data.get("changed_files", 0)}

    def get_diff(self, review_input: PRReviewInput) -> list[CodeFileDiff]:
        raw_files: list[dict] = []
        page = 1
        while True:
            resp = self._client.get(
                f"/repos/{review_input.repo_full_name}/pulls/{review_input.pr_number}/files",
                params={"per_page": 100, "page": page},
            )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            raw_files.extend(batch)
            if len(batch) < 100:
                break
            page += 1

        files: list[CodeFileDiff] = []
        budget = TOTAL_PATCH_BUDGET_CHARS
        for f in raw_files:
            patch = f.get("patch", "") or ""
            if budget <= 0:
                patch = "... (skipped - diff budget exhausted)"
            elif len(patch) > budget:
                patch = patch[:budget] + "\n... (truncated)"
            budget -= len(patch)
            files.append(
                CodeFileDiff(
                    path=f["filename"],
                    status=f.get("status", "modified"),
                    additions=f.get("additions", 0),
                    deletions=f.get("deletions", 0),
                    patch=patch,
                )
            )
        return files

    def upsert_comment(self, review_input: PRReviewInput, marker: str, body: str) -> str:
        full_body = f"{marker}\n{body}"
        existing_id = self._find_existing_comment(review_input, marker)
        if existing_id is not None:
            resp = self._client.patch(
                f"/repos/{review_input.repo_full_name}/issues/comments/{existing_id}",
                json={"body": full_body},
            )
        else:
            resp = self._client.post(
                f"/repos/{review_input.repo_full_name}/issues/{review_input.pr_number}/comments",
                json={"body": full_body},
            )
        resp.raise_for_status()
        return resp.json().get("html_url", review_input.html_url)

    def set_commit_status(
        self,
        repo_full_name: str,
        commit_sha: str,
        state: str,
        description: str,
        target_url: str | None = None,
    ) -> None:
        payload: dict = {
            "state": state,
            "description": (description or "")[:140],
            "context": "ai-review-bot/review",
        }
        if target_url:
            payload["target_url"] = target_url
        resp = self._client.post(
            f"/repos/{repo_full_name}/statuses/{commit_sha}",
            json=payload,
        )
        resp.raise_for_status()

    def _find_existing_comment(self, review_input: PRReviewInput, marker: str) -> int | None:
        resp = self._client.get(
            f"/repos/{review_input.repo_full_name}/issues/{review_input.pr_number}/comments",
            params={"per_page": 100},
        )
        resp.raise_for_status()
        for comment in resp.json():
            if marker in (comment.get("body") or ""):
                return comment["id"]
        return None
