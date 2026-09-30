import logging

from temporalio import activity

from pr_review_shared.schemas import AgentResult, CodeContext

from ..agents.base import BaseReviewAgent
from ..agents.code_quality_agent import CodeQualityReviewAgent
from ..agents.performance_agent import PerformanceReviewAgent
from ..agents.security_agent import SecurityReviewAgent
from ..agents.testing_agent import TestingReviewAgent

logger = logging.getLogger(__name__)


def _run(agent: BaseReviewAgent, context: CodeContext) -> AgentResult:
    findings = agent.analyze(context.files)
    logger.info("%s produced %d finding(s)", agent.name, len(findings))
    return AgentResult(agent=agent.name, category=agent.category, findings=findings)


@activity.defn
def run_security_agent(context: CodeContext) -> AgentResult:
    return _run(SecurityReviewAgent(), context)


@activity.defn
def run_performance_agent(context: CodeContext) -> AgentResult:
    return _run(PerformanceReviewAgent(), context)


@activity.defn
def run_code_quality_agent(context: CodeContext) -> AgentResult:
    return _run(CodeQualityReviewAgent(), context)


@activity.defn
def run_testing_agent(context: CodeContext) -> AgentResult:
    return _run(TestingReviewAgent(), context)
