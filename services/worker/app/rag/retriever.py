"""Lightweight RAG retriever over the project's coding-standards corpus.

Design notes
------------
This is deliberately embedding-free: the corpus is small (a handful of markdown files
under ``docs/standards/``), the queries are short (a category name plus a few tokens
from the diff), and adding a vector store would introduce infrastructure the demo
otherwise doesn't need. Instead we do classic TF-style keyword overlap scoring over
markdown *sections* (split on ``##`` headings) and return the top-k snippets.

The retrieval interface is intentionally the same shape a vector-backed retriever
would expose (``retrieve(query, k) -> list[Snippet]``) so it can be swapped for
``chromadb``, ``pgvector``, or a hosted store later without touching the agents.

Retrieved snippets are injected into each agent's *user* prompt (not the system
prompt) so the LLM treats them as authoritative in-context reference material rather
than persona instructions - this matches how tools like Cursor's ``@Docs`` behave.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

# Category → standards file mapping. Missing files are silently skipped so the pipeline
# still works even if a standards doc is deleted.
_CATEGORY_TO_DOC = {
    "security": "security.md",
    "performance": "performance.md",
    "code_quality": "code_quality.md",
    "testing": "testing.md",
}

_TOKEN_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]{2,}")
_STOPWORDS = frozenset(
    """the a an and or of to in on for with is are was were be been being that this these
    those it its as at by from into if then else than not no do does did done have has had
    but so up out about over under most many much any all some more less other same such
    also which who whom whose when where why how what""".split()
)


@dataclass(frozen=True)
class Snippet:
    """A retrieved passage from the standards corpus."""

    source: str  # e.g. "security.md#injection"
    heading: str
    text: str
    score: float


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text) if t.lower() not in _STOPWORDS]


class StandardsRetriever:
    """Keyword-overlap retriever over section-level splits of the standards corpus."""

    def __init__(self, standards_dir: Path) -> None:
        self._standards_dir = standards_dir
        self._sections_by_category: dict[str, list[tuple[str, str, str, set[str]]]] = {}
        self._load()

    def _load(self) -> None:
        for category, filename in _CATEGORY_TO_DOC.items():
            path = self._standards_dir / filename
            if not path.exists():
                logger.info("standards file missing, skipping: %s", path)
                continue
            self._sections_by_category[category] = self._split_sections(path)

    @staticmethod
    def _split_sections(path: Path) -> list[tuple[str, str, str, set[str]]]:
        """Split a markdown file into (source, heading, body, token_set) sections at ``##`` boundaries."""
        raw = path.read_text(encoding="utf-8")
        sections: list[tuple[str, str, str, set[str]]] = []
        # Group by ## headings; treat everything before the first ## as an implicit intro.
        parts = re.split(r"(?m)^##\s+(.+)$", raw)
        # parts = [intro, h1, body1, h2, body2, ...]
        intro = parts[0].strip()
        if intro:
            sections.append((f"{path.name}#intro", "intro", intro, set(_tokenize(intro))))
        for heading, body in zip(parts[1::2], parts[2::2]):
            body = body.strip()
            if not body:
                continue
            slug = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
            sections.append((f"{path.name}#{slug}", heading.strip(), body, set(_tokenize(f"{heading} {body}"))))
        return sections

    def retrieve(self, category: str, query: str, k: int = 3) -> list[Snippet]:
        """Return top-k standards snippets for ``category`` most relevant to ``query``.

        Scoring is Jaccard-ish: |query_tokens ∩ section_tokens| / (1 + log(section_size)).
        Ties broken by original document order. Sections with zero overlap are dropped
        unless nothing else scored - in that case we return the first ``k`` sections as
        a "always give the agent *something*" fallback, which mirrors the safe default of
        a vector store returning nearest-neighbors regardless of absolute similarity.
        """
        sections = self._sections_by_category.get(category, [])
        if not sections:
            return []
        q_tokens = set(_tokenize(query))
        scored: list[tuple[float, str, str, str]] = []
        for source, heading, body, section_tokens in sections:
            overlap = len(q_tokens & section_tokens)
            if overlap == 0:
                continue
            # length normalization keeps huge sections from dominating
            norm = 1.0 + (len(section_tokens) ** 0.5) / 10.0
            scored.append((overlap / norm, source, heading, body))
        scored.sort(key=lambda t: t[0], reverse=True)
        if not scored:
            # fallback: hand back the first k sections so the agent still gets context
            return [Snippet(source=s, heading=h, text=b, score=0.0) for s, h, b, _ in sections[:k]]
        return [Snippet(source=s, heading=h, text=b, score=score) for score, s, h, b in scored[:k]]


@lru_cache(maxsize=1)
def get_retriever() -> StandardsRetriever:
    """Process-wide singleton. The corpus is small and immutable at runtime."""
    # /app is the docker WORKDIR of the worker; standards are baked into the image at
    # /app/docs/standards. In local dev (running from repo root) the same relative path
    # resolves correctly because we're rooted at the project root.
    for candidate in (Path("/app/docs/standards"), Path("docs/standards"), Path(__file__).resolve().parents[4] / "docs" / "standards"):
        if candidate.exists():
            logger.info("RAG standards corpus loaded from %s", candidate)
            return StandardsRetriever(candidate)
    logger.warning("No standards corpus found; RAG retriever will return no snippets")
    return StandardsRetriever(Path("docs/standards"))  # empty retriever
