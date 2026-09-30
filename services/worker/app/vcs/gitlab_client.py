import logging

import httpx

from pr_review_shared.schemas import CodeFileDiff, PRReviewInput

from .base import VCSClient

logger = logging.getLogger(__name__)

TOTAL_PATCH_BUDGET_CHARS = 12000


class GitLabClient(VCSClient):
    def __init__(self, token: str, base_url: str = "https://gitlab.com"):
        self._client = httpx.Client(
            base_url=f"{base_url.rstrip('/')}/api/v4",
            headers={"PRIVATE-TOKEN": token},
            timeout=30.0,
        )

    def refresh_pr_state(self, review_input: PRReviewInput) -> dict:
        project_id = review_input.repo_external_id
        resp = self._client.get(f"/projects/{project_id}/merge_requests/{review_input.pr_number}")
        resp.raise_for_status()
        data = resp.json()
        return {"open": data.get("state") == "opened", "changed_files": len(data.get("changes", []) or [])}

    def get_diff(self, review_input: PRReviewInput) -> list[CodeFileDiff]:
        project_id = review_input.repo_external_id
        resp = self._client.get(f"/projects/{project_id}/merge_requests/{review_input.pr_number}/changes")
        resp.raise_for_status()
        data = resp.json()
        files: list[CodeFileDiff] = []
        budget = TOTAL_PATCH_BUDGET_CHARS
        for c in data.get("changes", []):
            patch = c.get("diff", "") or ""
            if budget <= 0:
                patch = "... (skipped - diff budget exhausted)"
            elif len(patch) > budget:
                patch = patch[:budget] + "\n... (truncated)"
            budget -= len(patch)
            status = "modified"
            if c.get("new_file"):
                status = "added"
            elif c.get("deleted_file"):
                status = "removed"
            elif c.get("renamed_file"):
                status = "renamed"
            files.append(
                CodeFileDiff(
                    path=c.get("new_path") or c.get("old_path"),
                    status=status,
                    patch=patch,
                )
            )
        return files

    def upsert_comment(self, review_input: PRReviewInput, marker: str, body: str) -> str:
        project_id = review_input.repo_external_id
        full_body = f"{marker}\n{body}"
        existing_id = self._find_existing_note(review_input, marker)
        base = f"/projects/{project_id}/merge_requests/{review_input.pr_number}/notes"
        if existing_id is not None:
            resp = self._client.put(f"{base}/{existing_id}", json={"body": full_body})
        else:
            resp = self._client.post(base, json={"body": full_body})
        resp.raise_for_status()
        return review_input.html_url

    def set_commit_status(
        self,
        repo_full_name: str,
        commit_sha: str,
        state: str,
        description: str,
        target_url: str | None = None,
    ) -> None:
        gl_state = {"success": "success", "failure": "failed", "pending": "pending"}.get(state, state)
        # GitLab project statuses require a URL-encoded project path or numeric ID.
        # For webhook-driven flows we always have the numeric project id in repo_external_id;
        # here we accept whichever caller-supplied identifier the workflow uses.
        project_id = repo_full_name.replace("/", "%2F")
        payload: dict = {
            "state": gl_state,
            "description": (description or "")[:255],
            "name": "ai-review-bot/review",
        }
        if target_url:
            payload["target_url"] = target_url
        resp = self._client.post(
            f"/projects/{project_id}/statuses/{commit_sha}",
            json=payload,
        )
        resp.raise_for_status()

    def _find_existing_note(self, review_input: PRReviewInput, marker: str) -> int | None:
        project_id = review_input.repo_external_id
        resp = self._client.get(
            f"/projects/{project_id}/merge_requests/{review_input.pr_number}/notes",
            params={"per_page": 100},
        )
        resp.raise_for_status()
        for note in resp.json():
            if marker in (note.get("body") or ""):
                return note["id"]
        return None
