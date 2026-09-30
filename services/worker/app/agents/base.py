"""Base class for review agents.

Each concrete agent (security, performance, code-quality, testing) supplies only its
category and system prompt; the actual review pipeline - RAG retrieval over the
project's coding standards, the LLM call, and structured-output validation - is a
LangGraph pipeline defined in :mod:`.graph` and shared across all agents.
"""
from abc import ABC, abstractmethod

from pr_review_shared.schemas import Category, CodeFileDiff, Finding


class BaseReviewAgent(ABC):
    category: Category
    name: str

    def applies_to(self, files: list[CodeFileDiff]) -> bool:
        """Workflow-level routing gate: should this agent's activity even be scheduled?
        Default: yes, as long as there is any changed file. Subclasses can override to
        skip themselves when the diff has nothing they can reason about (e.g. a
        docs-only PR)."""
        return bool(files)

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    def analyze(self, files: list[CodeFileDiff]) -> list[Finding]:
        """Run the RAG + LLM + validation pipeline for this agent over the given diff.

        Delayed import to avoid a hard dependency on ``langgraph`` at module-import
        time (keeps unit tests that only import agent classes lightweight).
        """
        from .graph import run_agent_graph

        return run_agent_graph(self, files)
