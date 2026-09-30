import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from pr_review_shared.config import settings
from pr_review_shared.db import init_db
from pr_review_shared.logging import configure_logging

from .activities.agent_activities import (
    run_code_quality_agent,
    run_performance_agent,
    run_security_agent,
    run_testing_agent,
)
from .activities.persist_activity import fetch_previous_round_findings, persist_results
from .activities.vcs_activities import fetch_diff, fetch_pr_state, post_comment, set_commit_status
from .workflows.agent_workflows import (
    CodeQualityReviewWorkflow,
    PerformanceReviewWorkflow,
    SecurityReviewWorkflow,
    TestingReviewWorkflow,
)
from .workflows.pr_review_workflow import PRReviewWorkflow

logger = logging.getLogger(__name__)


async def main() -> None:
    configure_logging("worker", settings.log_level)
    init_db()

    client = await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
        data_converter=pydantic_data_converter,
    )

    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[
            PRReviewWorkflow,
            SecurityReviewWorkflow,
            PerformanceReviewWorkflow,
            CodeQualityReviewWorkflow,
            TestingReviewWorkflow,
        ],
        activities=[
            fetch_pr_state,
            fetch_diff,
            post_comment,
            set_commit_status,
            run_security_agent,
            run_performance_agent,
            run_code_quality_agent,
            run_testing_agent,
            persist_results,
            fetch_previous_round_findings,
        ],
        activity_executor=ThreadPoolExecutor(max_workers=20),
    )
    logger.info("Worker starting on task queue '%s' (%s)", settings.temporal_task_queue, settings.temporal_address)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
