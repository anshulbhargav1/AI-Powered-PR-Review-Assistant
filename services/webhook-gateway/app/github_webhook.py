import logging

from pr_review_shared.schemas import PRReviewInput, Provider

from .events import EventKind

logger = logging.getLogger(__name__)

_ACTION_KINDS = {
    "opened": EventKind.start,
    "reopened": EventKind.start,
    "synchronize": EventKind.update,
    "closed": EventKind.close,
}


def parse_github_event(event_type: str, payload: dict) -> tuple[EventKind, PRReviewInput] | None:
    if event_type != "pull_request":
        logger.debug("Ignoring GitHub event type=%s", event_type)
        return None

    action = payload.get("action")
    kind = _ACTION_KINDS.get(action)
    if kind is None:
        logger.info("Ignoring GitHub pull_request action=%s", action)
        return None

    pr = payload.get("pull_request", {})
    if kind != EventKind.close and pr.get("draft"):
        logger.info("Ignoring draft PR #%s", pr.get("number"))
        return None

    repo = payload.get("repository", {})
    review_input = PRReviewInput(
        provider=Provider.github,
        repo_full_name=repo.get("full_name", ""),
        repo_external_id=str(repo.get("id", "")),
        pr_number=pr.get("number"),
        commit_sha=pr.get("head", {}).get("sha", ""),
        base_sha=pr.get("base", {}).get("sha", ""),
        author=pr.get("user", {}).get("login", ""),
        title=pr.get("title", ""),
        source_branch=pr.get("head", {}).get("ref", ""),
        target_branch=pr.get("base", {}).get("ref", ""),
        html_url=pr.get("html_url", ""),
    )
    return kind, review_input
