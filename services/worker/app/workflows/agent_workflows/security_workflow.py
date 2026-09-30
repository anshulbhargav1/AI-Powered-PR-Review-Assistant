from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from pr_review_shared.schemas import AgentResult, CodeContext

    from ...activities.agent_activities import run_security_agent
    from ..retry_policies import AGENT_RETRY


@workflow.defn(name="SecurityReviewWorkflow")
class SecurityReviewWorkflow:
    """Thin child workflow around the security review activity. Being a workflow
    (not just an activity) means it shows up as its own entry in the Temporal UI,
    which is the visual demo win: four parallel specialist workflows fanning out."""

    @workflow.run
    async def run(self, context: CodeContext) -> AgentResult:
        return await workflow.execute_activity(
            run_security_agent,
            context,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=AGENT_RETRY,
        )
