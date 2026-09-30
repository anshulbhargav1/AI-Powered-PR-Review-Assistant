"""Per-agent LangGraph pipeline: retrieve → analyze → validate.

Why LangGraph *inside* a Temporal activity, rather than replacing Temporal?
--------------------------------------------------------------------------
The two tools solve non-overlapping problems:

* **Temporal** owns durable, cross-agent orchestration: it fans out the four review
  agents as parallel child workflows, retries them independently on transient failure,
  survives worker restarts, and gives you a replayable audit trail of the whole review.
* **LangGraph** owns the *stateful, in-process* pipeline each individual agent runs
  through: fetch relevant coding-standards snippets (RAG), call the LLM, then run a
  cheap validator/repair pass over the structured output before returning findings.

Keeping LangGraph inside the Temporal activity means the graph runs on a single worker
and can share mutable Python state freely, while Temporal still gets a clean
"activity succeeded/failed" boundary to retry against. Effectively: LangGraph for the
agent's reasoning loop, Temporal for durability and orchestration between agents.
"""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, TypedDict

from langgraph.graph import END, StateGraph

from pr_review_shared.schemas import CodeFileDiff, Finding, Severity

from ..llm.groq_client import complete_json
from ..rag import get_retriever

if TYPE_CHECKING:
    from .base import BaseReviewAgent

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    """State threaded through the per-agent LangGraph."""

    agent_name: str
    category: str
    files: list[CodeFileDiff]
    system_prompt: str
    retrieved_snippets: list[dict]  # [{source, heading, text, score}]
    raw_llm_output: str
    parsed_findings: list[Finding]
    validation_errors: list[str]


def _diff_summary_for_query(files: list[CodeFileDiff]) -> str:
    """Build a short query string from the diff for the RAG retriever - just the
    file paths and the added lines, capped so we don't pathologically dominate the
    tokenizer."""
    parts: list[str] = []
    for f in files:
        parts.append(f.path)
        for line in f.patch.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                parts.append(line[1:])
    return "\n".join(parts)[:4000]


def _retrieve_node(state: AgentState) -> AgentState:
    """Node 1: fetch relevant standards snippets for this agent's category."""
    retriever = get_retriever()
    query = _diff_summary_for_query(state["files"])
    snippets = retriever.retrieve(state["category"], query, k=3)
    logger.info(
        "%s: retrieved %d standards snippet(s) from RAG (sources=%s)",
        state["agent_name"],
        len(snippets),
        [s.source for s in snippets],
    )
    return {
        "retrieved_snippets": [
            {"source": s.source, "heading": s.heading, "text": s.text, "score": s.score}
            for s in snippets
        ]
    }


def _build_user_prompt(state: AgentState) -> str:
    """Compose the user prompt: retrieved standards first (as authoritative reference),
    then the JSON output contract, then the diff itself."""
    parts: list[str] = []
    snippets = state.get("retrieved_snippets") or []
    if snippets:
        parts.append(
            "## Project standards (authoritative reference - cite by source when relevant)\n"
        )
        for s in snippets:
            parts.append(f"### From {s['source']} — {s['heading']}\n{s['text']}\n")
        parts.append("---\n")
    parts.append(
        "Review the following changed files from a pull request diff. Only flag issues "
        "actually introduced or visible in the diff below - do not invent files or lines "
        "that are not shown. Respond ONLY with a JSON object of this exact shape:\n"
        '{"findings": [{"severity": "critical|high|medium|low|info", "file": "<path>", '
        '"line_number": <int-or-null>, "issue": "<short title>", '
        '"explanation": "<why it matters>", "impact": "<concrete impact>", '
        '"recommendation": "<how to fix>", "confidence": <float 0-1>}]}\n'
        'If you find nothing in this category, return {"findings": []}.\n\n'
    )
    for f in state["files"]:
        parts.append(
            f"### File: {f.path} ({f.status}, +{f.additions}/-{f.deletions})\n"
            f"```diff\n{f.patch}\n```\n"
        )
    return "\n".join(parts)


def _analyze_node(state: AgentState) -> AgentState:
    """Node 2: call the LLM with the retrieval-augmented prompt."""
    user_prompt = _build_user_prompt(state)
    raw = complete_json(state["system_prompt"], user_prompt)
    return {"raw_llm_output": raw}


def _safe_load(raw: str) -> dict | None:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None


def _validate_node(state: AgentState) -> AgentState:
    """Node 3: parse the LLM output into ``Finding`` objects, dropping malformed ones
    and recording validation errors. This is the "structured LLM responses and
    validation" guarantee the platform makes to downstream consumers - anything that
    escapes this node is safe to persist and render."""
    from pr_review_shared.schemas import Category

    raw = state.get("raw_llm_output", "") or ""
    data = _safe_load(raw)
    if data is None:
        logger.warning(
            "%s: could not parse model output as JSON, returning no findings",
            state["agent_name"],
        )
        return {"parsed_findings": [], "validation_errors": ["unparseable-json"]}

    findings: list[Finding] = []
    errors: list[str] = []
    for item in data.get("findings", []):
        try:
            findings.append(
                Finding(
                    category=Category(state["category"]),
                    severity=Severity(str(item.get("severity", "low")).lower()),
                    file=item.get("file") or "unknown",
                    line_number=item.get("line_number"),
                    issue=item.get("issue") or "Unspecified issue",
                    explanation=item.get("explanation"),
                    impact=item.get("impact"),
                    recommendation=item.get("recommendation") or "",
                    confidence=float(item.get("confidence", 0.6)),
                    agent=state["agent_name"],
                )
            )
        except (ValueError, TypeError) as e:
            logger.warning(
                "%s: dropping malformed finding %r (%s)", state["agent_name"], item, e
            )
            errors.append(f"malformed-finding: {e}")
    return {"parsed_findings": findings, "validation_errors": errors}


def build_agent_graph():
    """Compile the retrieve → analyze → validate graph once; it's reused per agent call."""
    graph = StateGraph(AgentState)
    graph.add_node("retrieve", _retrieve_node)
    graph.add_node("analyze", _analyze_node)
    graph.add_node("validate", _validate_node)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "analyze")
    graph.add_edge("analyze", "validate")
    graph.add_edge("validate", END)
    return graph.compile()


_COMPILED_GRAPH = None


def run_agent_graph(agent: "BaseReviewAgent", files: list[CodeFileDiff]) -> list[Finding]:
    """Entry point called from ``BaseReviewAgent.analyze``. Lazily compiles the graph
    on first use (LangGraph compilation isn't free but does not need to happen at
    import time)."""
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_agent_graph()
    initial: AgentState = {
        "agent_name": agent.name,
        "category": agent.category.value,
        "files": files,
        "system_prompt": agent.system_prompt,
    }
    final_state: AgentState = _COMPILED_GRAPH.invoke(initial)
    return final_state.get("parsed_findings", []) or []
