from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from pr_review_shared.schemas import AgentResult, CodeContext

    from ...activities.agent_activities import run_performance_agent
    from ..retry_policies import AGENT_RETRY


@workflow.defn(name="PerformanceReviewWorkflow")
class PerformanceReviewWorkflow:
    @workflow.run
    async def run(self, context: CodeContext) -> AgentResult:
        return await workflow.execute_activity(
            run_performance_agent,
            context,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=AGENT_RETRY,
        )
