import logging

from pr_review_shared.schemas import PRReviewInput, Provider

from .events import EventKind

logger = logging.getLogger(__name__)

_ACTION_KINDS = {
    "open": EventKind.start,
    "reopen": EventKind.start,
    "update": EventKind.update,
    "close": EventKind.close,
    "merge": EventKind.close,
}


def parse_gitlab_event(payload: dict) -> tuple[EventKind, PRReviewInput] | None:
    if payload.get("object_kind") != "merge_request":
        logger.debug("Ignoring GitLab event object_kind=%s", payload.get("object_kind"))
        return None

    attrs = payload.get("object_attributes", {})
    action = attrs.get("action")
    kind = _ACTION_KINDS.get(action)
    if kind is None:
        logger.info("Ignoring GitLab merge_request action=%s", action)
        return None
    if kind != EventKind.close and (attrs.get("work_in_progress") or attrs.get("draft")):
        logger.info("Ignoring draft MR !%s", attrs.get("iid"))
        return None

    project = payload.get("project", {})
    user = payload.get("user", {})
    last_commit = attrs.get("last_commit") or {}
    diff_refs = attrs.get("diff_refs") or {}

    review_input = PRReviewInput(
        provider=Provider.gitlab,
        repo_full_name=project.get("path_with_namespace", ""),
        repo_external_id=str(project.get("id", "")),
        pr_number=attrs.get("iid"),
        commit_sha=last_commit.get("id") or diff_refs.get("head_sha", ""),
        base_sha=diff_refs.get("base_sha", ""),
        author=user.get("username", ""),
        title=attrs.get("title", ""),
        source_branch=attrs.get("source_branch", ""),
        target_branch=attrs.get("target_branch", ""),
        html_url=attrs.get("url", ""),
    )
    return kind, review_input
