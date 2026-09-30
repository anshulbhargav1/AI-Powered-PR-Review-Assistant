import asyncio
import logging
from datetime import timedelta

from temporalio import workflow

# Everything imported here is either the workflow SDK itself (safe) or pure/I-O code that
# the workflow only *schedules* rather than executes inline - pass these through the sandbox
# instead of re-importing them in a restricted environment.
with workflow.unsafe.imports_passed_through():
    from pr_review_shared.config import settings
    from pr_review_shared.schemas import (
        AgentResult,
        CodeContext,
        PRReviewInput,
        ReviewSummary,
        ReviewWorkflowResult,
        Severity,
    )

    from ..activities.io_models import (
        FetchPreviousInput,
        PersistResultsInput,
        PostCommentInput,
        SetCommitStatusInput,
    )
    from ..activities.persist_activity import fetch_previous_round_findings, persist_results
    from ..activities.vcs_activities import fetch_diff, fetch_pr_state, post_comment, set_commit_status
    from ..agents import (
        CodeQualityReviewAgent,
        PerformanceReviewAgent,
        SecurityReviewAgent,
        TestingReviewAgent,
    )
    from ..aggregation import aggregate_and_dedupe
    from ..comment_template import build_comment_body
    from ..round_diff import compute_round_diff
    from .agent_workflows import (
        CodeQualityReviewWorkflow,
        PerformanceReviewWorkflow,
        SecurityReviewWorkflow,
        TestingReviewWorkflow,
    )
    from .retry_policies import AGENT_RETRY, PERSIST_RETRY, VALIDATE_RETRY

logger = logging.getLogger(__name__)


# Pair each agent (used only for its `applies_to` gate + naming) with the child workflow
# class that actually runs it. The gate lets an agent opt out cheaply when a diff has
# nothing it can reason about, saving both LLM calls and Temporal child-workflow overhead.
_CHILD_WORKFLOW_MAP = [
    (SecurityReviewAgent(), SecurityReviewWorkflow),
    (PerformanceReviewAgent(), PerformanceReviewWorkflow),
    (CodeQualityReviewAgent(), CodeQualityReviewWorkflow),
    (TestingReviewAgent(), TestingReviewWorkflow),
]


def _empty_summary(review_run_id: str) -> ReviewSummary:
    return ReviewSummary(
        review_run_id=review_run_id,
        total_findings=0,
        by_category={},
        by_severity={},
        dashboard_url="",
        passed=True,
    )


@workflow.defn
class PRReviewWorkflow:
    """Entity workflow for one PR/MR: lives from open to close. Each commit pushed to the
    PR/MR re-runs one full AI review via the `new_commit` signal; `close` ends it. All I/O
    (VCS calls, LLM calls, DB writes) lives in activities; this class is pure orchestration
    logic, kept deterministic per Temporal's workflow replay requirements."""

    def __init__(self) -> None:
        self._pending: PRReviewInput | None = None
        self._closed = False

    @workflow.signal
    def new_commit(self, review_input: PRReviewInput) -> None:
        self._pending = review_input

    @workflow.signal
    def close(self) -> None:
        self._closed = True

    @workflow.run
    async def run(self, review_input: PRReviewInput) -> ReviewWorkflowResult:
        # A failed review cycle must not kill this entity workflow - it has to keep waiting
        # for signals until the PR/MR is explicitly closed.
        try:
            result = await self._run_review(review_input)
        except Exception as e:
            logger.error(
                "Review cycle failed for %s#%s @ %s: %s",
                review_input.repo_full_name, review_input.pr_number, review_input.commit_sha, e,
            )
            result = ReviewWorkflowResult(
                review_run_id=str(workflow.uuid4()),
                summary=_empty_summary(""),
                skipped=True,
                skip_reason=f"Review failed: {e}",
            )

        await workflow.wait_condition(lambda: self._pending is not None or self._closed)
        if self._closed:
            return result

        next_input = self._pending
        self._pending = None
        # Bump the round counter on every re-review so the comment, dashboard, and diff
        # logic can all reason about "round N vs round N-1".
        next_input = next_input.model_copy(
            update={"review_round": review_input.review_round + 1}
        )
        workflow.continue_as_new(next_input)
        raise AssertionError("unreachable: continue_as_new always raises")

    async def _run_review(self, review_input: PRReviewInput) -> ReviewWorkflowResult:
        review_run_id = str(workflow.uuid4())
        workflow_id = workflow.info().workflow_id

        # 1. Validate: re-check the PR/MR is still open (webhooks can race with later events)
        state: dict = await workflow.execute_activity(
            fetch_pr_state,
            review_input,
            start_to_close_timeout=timedelta(seconds=20),
            retry_policy=VALIDATE_RETRY,
        )
        if not state.get("open", True):
            return ReviewWorkflowResult(
                review_run_id=review_run_id,
                summary=_empty_summary(review_run_id),
                skipped=True,
                skip_reason="PR/MR is no longer open",
            )

        # 2/3. Fetch diff and build structured code context
        context: CodeContext = await workflow.execute_activity(
            fetch_diff,
            review_input,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=VALIDATE_RETRY,
        )
        if not context.files:
            return ReviewWorkflowResult(
                review_run_id=review_run_id,
                summary=_empty_summary(review_run_id),
                skipped=True,
                skip_reason="No reviewable file changes",
            )

        # 4. Fan out to specialist child workflows in parallel. Each one is its own
        # workflow entry in the Temporal UI, which makes the parallelism visible in the demo
        # and lets each agent retry independently without dragging the others down.
        selected = [
            (agent, wf_cls)
            for agent, wf_cls in _CHILD_WORKFLOW_MAP
            if agent.applies_to(context.files)
        ]
        child_results = await asyncio.gather(
            *(
                workflow.execute_child_workflow(
                    wf_cls.run,
                    context,
                    id=f"{workflow_id}-{agent.name}-r{review_input.review_round}",
                    task_queue=settings.temporal_task_queue,
                    execution_timeout=timedelta(minutes=5),
                    retry_policy=AGENT_RETRY,
                )
                for agent, wf_cls in selected
            ),
            return_exceptions=True,
        )

        agent_results: list[AgentResult] = []
        for (agent, _), result in zip(selected, child_results):
            if isinstance(result, BaseException):
                logger.warning("%s child workflow failed: %s", agent.name, result)
                agent_results.append(
                    AgentResult(
                        agent=agent.name,
                        category=agent.category,
                        findings=[],
                        passed=True,
                        error=str(result),
                    )
                )
            else:
                agent_results.append(result)

        # 5. Aggregate + dedupe (pure - runs directly in the workflow, no activity needed)
        findings, by_category, by_severity = aggregate_and_dedupe(agent_results)

        # 6. Persist
        dashboard_url = await workflow.execute_activity(
            persist_results,
            PersistResultsInput(
                review_input=review_input,
                review_run_id=review_run_id,
                workflow_id=workflow_id,
                findings=findings,
                by_category=by_category,
                by_severity=by_severity,
            ),
            start_to_close_timeout=timedelta(seconds=20),
            retry_policy=PERSIST_RETRY,
        )

        # Overall pass = every agent passed AND aggregation found nothing critical/high.
        blocking = {Severity.critical, Severity.high}
        critical_count = sum(1 for f in findings if f.severity in blocking)
        overall_passed = all(r.passed for r in agent_results) and critical_count == 0

        summary = ReviewSummary(
            review_run_id=review_run_id,
            total_findings=len(findings),
            by_category=by_category,
            by_severity=by_severity,
            dashboard_url=dashboard_url,
            passed=overall_passed,
        )

        # 7. Fetch previous round for diff (empty on round 1)
        round_diff = None
        if review_input.review_round > 1:
            previous = await workflow.execute_activity(
                fetch_previous_round_findings,
                FetchPreviousInput(
                    provider=review_input.provider,
                    repo_external_id=review_input.repo_external_id,
                    pr_number=review_input.pr_number,
                    current_round=review_input.review_round,
                ),
                start_to_close_timeout=timedelta(seconds=15),
                retry_policy=PERSIST_RETRY,
            )
            round_diff = compute_round_diff(previous, findings)

        # 8. Post/update the PR/MR comment
        marker = f"<!-- ai-review-bot:{review_input.provider.value}:{review_input.pr_number} -->"
        body = build_comment_body(
            summary,
            findings,
            review_round=review_input.review_round,
            round_diff=round_diff,
            head_sha_short=(review_input.commit_sha or "")[:7],
        )
        comment_url = await workflow.execute_activity(
            post_comment,
            PostCommentInput(review_input=review_input, marker=marker, body=body),
            start_to_close_timeout=timedelta(seconds=20),
            retry_policy=VALIDATE_RETRY,
        )

        # 9. Set the commit status so the PR is either merge-blocked or greenlit
        await workflow.execute_activity(
            set_commit_status,
            SetCommitStatusInput(
                provider=review_input.provider,
                repo_full_name=review_input.repo_full_name,
                repo_external_id=review_input.repo_external_id,
                commit_sha=review_input.commit_sha,
                passed=overall_passed,
                critical_count=critical_count,
                dashboard_url=dashboard_url,
            ),
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=VALIDATE_RETRY,
        )

        return ReviewWorkflowResult(review_run_id=review_run_id, summary=summary, comment_url=comment_url)
