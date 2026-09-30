import hashlib
import hmac
import logging

from fastapi import FastAPI, HTTPException, Request
from temporalio.common import WorkflowIDConflictPolicy
from temporalio.service import RPCError, RPCStatusCode

from pr_review_shared.config import settings
from pr_review_shared.logging import configure_logging
from pr_review_shared.schemas import PRReviewInput

from .events import EventKind
from .github_webhook import parse_github_event
from .gitlab_webhook import parse_gitlab_event
from .temporal_client import get_temporal_client

configure_logging("webhook-gateway", settings.log_level)
logger = logging.getLogger(__name__)

if settings.env == "production" and not settings.github_webhook_secret:
    raise RuntimeError(
        "GITHUB_WEBHOOK_SECRET is required in production. "
        "Set ENV=development to skip signature verification for local runs."
    )

app = FastAPI(title="AI-Powered PR Review Assistant - Webhook Gateway")


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/webhooks/github")
async def github_webhook(request: Request) -> dict:
    body = await request.body()
    if settings.github_webhook_secret:
        _verify_github_signature(body, request.headers.get("x-hub-signature-256", ""))

    event_type = request.headers.get("x-github-event", "")
    payload = await request.json()
    parsed = parse_github_event(event_type, payload)
    if parsed is None:
        return {"status": "ignored"}

    kind, review_input = parsed
    workflow_id = await _dispatch(kind, review_input)
    return {"status": kind.value, "workflow_id": workflow_id}


@app.post("/webhooks/gitlab")
async def gitlab_webhook(request: Request) -> dict:
    if settings.gitlab_webhook_secret:
        token = request.headers.get("x-gitlab-token", "")
        if not hmac.compare_digest(token, settings.gitlab_webhook_secret):
            raise HTTPException(status_code=401, detail="invalid webhook token")

    payload = await request.json()
    parsed = parse_gitlab_event(payload)
    if parsed is None:
        return {"status": "ignored"}

    kind, review_input = parsed
    workflow_id = await _dispatch(kind, review_input)
    return {"status": kind.value, "workflow_id": workflow_id}


def _verify_github_signature(body: bytes, signature_header: str) -> None:
    if not signature_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="missing signature")
    expected = "sha256=" + hmac.new(settings.github_webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=401, detail="invalid signature")


def _workflow_id(review_input: PRReviewInput) -> str:
    return f"pr-review-{review_input.provider.value}-{review_input.repo_external_id}-{review_input.pr_number}"


async def _dispatch(kind: EventKind, review_input: PRReviewInput) -> str:
    client = await get_temporal_client()
    workflow_id = _workflow_id(review_input)

    if kind == EventKind.start:
        handle = await client.start_workflow(
            "PRReviewWorkflow",
            review_input,
            id=workflow_id,
            task_queue=settings.temporal_task_queue,
            id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
        )
        logger.info(
            "Started review workflow %s for %s#%s", handle.id, review_input.repo_full_name, review_input.pr_number
        )
        return handle.id

    # UPDATE/CLOSE: signal the existing per-PR workflow. If it isn't running (a synchronize
    # raced ahead of the opened event, or the workflow already finished), there's nothing to
    # signal - log and move on rather than starting a fresh review out of band.
    signal_name = "new_commit" if kind == EventKind.update else "close"
    handle = client.get_workflow_handle(workflow_id)
    try:
        if kind == EventKind.update:
            await handle.signal("new_commit", review_input)
        else:
            await handle.signal("close")
        logger.info("Signaled %s on workflow %s for %s#%s", signal_name, workflow_id, review_input.repo_full_name, review_input.pr_number)
    except RPCError as e:
        if e.status != RPCStatusCode.NOT_FOUND:
            raise
        logger.info(
            "No active workflow %s to signal %s for %s#%s", workflow_id, signal_name,
            review_input.repo_full_name, review_input.pr_number,
        )
    return workflow_id
