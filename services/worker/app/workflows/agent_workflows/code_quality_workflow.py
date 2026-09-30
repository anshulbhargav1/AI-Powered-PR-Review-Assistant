from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from pr_review_shared.schemas import AgentResult, CodeContext

    from ...activities.agent_activities import run_code_quality_agent
    from ..retry_policies import AGENT_RETRY


@workflow.defn(name="CodeQualityReviewWorkflow")
class CodeQualityReviewWorkflow:
    @workflow.run
    async def run(self, context: CodeContext) -> AgentResult:
        return await workflow.execute_activity(
            run_code_quality_agent,
            context,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=AGENT_RETRY,
        )
