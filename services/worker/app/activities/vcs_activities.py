import logging

from temporalio import activity

from pr_review_shared.schemas import CodeContext, PRReviewInput, Provider

from ..vcs.factory import get_vcs_client
from .io_models import PostCommentInput, SetCommitStatusInput

logger = logging.getLogger(__name__)


@activity.defn
def fetch_pr_state(review_input: PRReviewInput) -> dict:
    client = get_vcs_client(review_input.provider)
    state = client.refresh_pr_state(review_input)
    logger.info("PR state for %s#%s: %s", review_input.repo_full_name, review_input.pr_number, state)
    return state


@activity.defn
def fetch_diff(review_input: PRReviewInput) -> CodeContext:
    client = get_vcs_client(review_input.provider)
    files = client.get_diff(review_input)
    logger.info("Fetched %d changed file(s) for %s#%s", len(files), review_input.repo_full_name, review_input.pr_number)
    return CodeContext(files=files)


@activity.defn
def post_comment(payload: PostCommentInput) -> str:
    client = get_vcs_client(payload.review_input.provider)
    url = client.upsert_comment(payload.review_input, payload.marker, payload.body)
    logger.info("Posted review comment: %s", url)
    return url


@activity.defn
def set_commit_status(payload: SetCommitStatusInput) -> None:
    client = get_vcs_client(payload.provider)
    state = "success" if payload.passed else "failure"
    if payload.passed:
        description = "All AI Review checks passed"
    else:
        description = f"AI Review found {payload.critical_count} blocking issue(s)"
    # GitLab wants the URL-encoded project path (or the numeric project id); GitHub wants owner/repo.
    repo_identifier = (
        payload.repo_external_id if payload.provider == Provider.gitlab else payload.repo_full_name
    )
    client.set_commit_status(
        repo_identifier,
        payload.commit_sha,
        state,
        description,
        target_url=payload.dashboard_url,
    )
    logger.info(
        "Set commit status on %s @ %s: %s (%s)",
        payload.repo_full_name, payload.commit_sha, state, description,
    )
