from difflib import SequenceMatcher

from pr_review_shared.schemas import AgentResult, Finding, Severity

_SEVERITY_ORDER = {
    Severity.critical: 0,
    Severity.high: 1,
    Severity.medium: 2,
    Severity.low: 3,
    Severity.info: 4,
}

_DUPLICATE_SIMILARITY_THRESHOLD = 0.6


def aggregate_and_dedupe(
    results: list[AgentResult],
) -> tuple[list[Finding], dict[str, int], dict[str, int]]:
    """Pure aggregation/dedup logic - no I/O, safe to run directly inside the workflow."""
    all_findings: list[Finding] = []
    for result in results:
        all_findings.extend(result.findings)

    deduped: list[Finding] = []
    for finding in all_findings:
        dup_index = _find_duplicate_index(deduped, finding)
        if dup_index is None:
            deduped.append(finding)
        elif _rank(finding) < _rank(deduped[dup_index]):
            deduped[dup_index] = finding

    deduped.sort(key=_rank)

    by_category: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for f in deduped:
        by_category[f.category.value] = by_category.get(f.category.value, 0) + 1
        by_severity[f.severity.value] = by_severity.get(f.severity.value, 0) + 1

    return deduped, by_category, by_severity


def _rank(finding: Finding) -> tuple[int, float]:
    return (_SEVERITY_ORDER[finding.severity], -finding.confidence)


def _find_duplicate_index(existing: list[Finding], candidate: Finding) -> int | None:
    for i, e in enumerate(existing):
        if e.file != candidate.file or e.category != candidate.category:
            continue
        if (
            e.line_number is not None
            and candidate.line_number is not None
            and e.line_number != candidate.line_number
        ):
            continue
        similarity = SequenceMatcher(None, e.issue.lower(), candidate.issue.lower()).ratio()
        if similarity > _DUPLICATE_SIMILARITY_THRESHOLD:
            return i
    return None
