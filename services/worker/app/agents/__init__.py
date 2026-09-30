from .base import BaseReviewAgent
from .code_quality_agent import CodeQualityReviewAgent
from .performance_agent import PerformanceReviewAgent
from .security_agent import SecurityReviewAgent
from .testing_agent import TestingReviewAgent

ALL_AGENTS: list[BaseReviewAgent] = [
    SecurityReviewAgent(),
    PerformanceReviewAgent(),
    CodeQualityReviewAgent(),
    TestingReviewAgent(),
]

__all__ = [
    "BaseReviewAgent",
    "SecurityReviewAgent",
    "PerformanceReviewAgent",
    "CodeQualityReviewAgent",
    "TestingReviewAgent",
    "ALL_AGENTS",
]
