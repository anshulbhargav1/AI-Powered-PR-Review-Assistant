import logging
from datetime import datetime, timezone

from temporalio import activity

from pr_review_shared.config import settings
from pr_review_shared.db import get_session
from pr_review_shared.models import FindingRow, Repository, ReviewRun

from .io_models import FetchPreviousInput, FindingSnapshot, PersistResultsInput

logger = logging.getLogger(__name__)


@activity.defn
def persist_results(payload: PersistResultsInput) -> str:
    """Writes the review run + findings to Postgres and returns the dashboard URL."""
    review_input = payload.review_input
    session = get_session()
    try:
        repo_id = f"{review_input.provider.value}:{review_input.repo_external_id}"
        session.merge(
            Repository(
                id=repo_id,
                provider=review_input.provider.value,
                external_id=review_input.repo_external_id,
                full_name=review_input.repo_full_name,
            )
        )

        session.add(
            ReviewRun(
                id=payload.review_run_id,
                repository_id=repo_id,
                pr_number=review_input.pr_number,
                commit_sha=review_input.commit_sha,
                title=review_input.title,
                author=review_input.author,
                html_url=review_input.html_url,
                status="completed",
                workflow_id=payload.workflow_id,
                review_round=review_input.review_round,
                total_findings=len(payload.findings),
                by_category=payload.by_category,
                by_severity=payload.by_severity,
                completed_at=datetime.now(timezone.utc),
            )
        )

        for f in payload.findings:
            session.add(
                FindingRow(
                    review_run_id=payload.review_run_id,
                    category=f.category.value,
                    severity=f.severity.value,
                    file=f.file,
                    line_number=f.line_number,
                    issue=f.issue,
                    explanation=f.explanation,
                    impact=f.impact,
                    recommendation=f.recommendation,
                    confidence=f.confidence,
                    agent=f.agent,
                )
            )

        session.commit()
    finally:
        session.close()

    dashboard_url = f"{settings.dashboard_base_url}/reviews/{payload.review_run_id}"
    logger.info("Persisted review run %s (%d findings)", payload.review_run_id, len(payload.findings))
    return dashboard_url


@activity.defn
def fetch_previous_round_findings(payload: FetchPreviousInput) -> list[FindingSnapshot]:
    """Return the findings from the most recent completed review round for this PR
    that is strictly older than `current_round`. Empty list if this is the first round."""
    session = get_session()
    try:
        repo_id = f"{payload.provider.value}:{payload.repo_external_id}"
        prev = (
            session.query(ReviewRun)
            .filter(
                ReviewRun.repository_id == repo_id,
                ReviewRun.pr_number == payload.pr_number,
                ReviewRun.review_round < payload.current_round,
            )
            .order_by(ReviewRun.review_round.desc())
            .first()
        )
        if prev is None:
            return []
        return [
            FindingSnapshot(
                category=f.category,
                file=f.file,
                line_number=f.line_number,
                issue=f.issue,
                severity=f.severity,
            )
            for f in prev.findings
        ]
    finally:
        session.close()
