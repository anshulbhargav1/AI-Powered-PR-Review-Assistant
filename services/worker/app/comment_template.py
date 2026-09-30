from pr_review_shared.schemas import Finding, ReviewSummary

_SEVERITY_EMOJI = {"critical": "\U0001F534", "high": "\U0001F7E0", "medium": "\U0001F7E1", "low": "\U0001F535", "info": "⚪"}
_CATEGORY_LABEL = {"security": "Security", "performance": "Performance", "code_quality": "Code Quality", "testing": "Testing"}
_CATEGORY_ORDER = ("security", "performance", "code_quality", "testing")


def build_comment_body(
    summary: ReviewSummary,
    findings: list[Finding],
    review_round: int = 1,
    round_diff: dict | None = None,
    head_sha_short: str = "",
) -> str:
    """Deterministic templating - no LLM call needed for the summary comment, which keeps
    it cheap, fast, and immune to the model hallucinating counts that don't match the data."""
    header = f"## AI Code Review \u2014 Round {review_round}"
    if head_sha_short:
        header += f" (`{head_sha_short}`)"
    lines = [header, "", f"**Summary:** Found {summary.total_findings} issue(s)", ""]

    if round_diff and review_round > 1:
        resolved = len(round_diff.get("resolved", []))
        new_ = len(round_diff.get("new", []))
        still = len(round_diff.get("still_present", []))
        if resolved or new_ or still:
            lines.append("### Changes since last round")
            if resolved:
                lines.append(f"- Resolved: {resolved} issue(s)")
            if new_:
                lines.append(f"- New: {new_} issue(s)")
            if still:
                lines.append(f"- Still present: {still} issue(s)")
            lines.append("")

    for category in _CATEGORY_ORDER:
        count = summary.by_category.get(category, 0)
        if count == 0:
            continue
        sev_counts = _category_severity_counts(findings, category)
        breakdown = " ".join(f"{n} {sev}" for sev, n in sev_counts.items())
        lines.append(f"- **{_CATEGORY_LABEL[category]}:** {count} ({breakdown})")
    lines.append("")

    if findings:
        lines.append("<details>")
        lines.append("<summary><strong>Detailed Report</strong></summary>")
        lines.append("")
        for category in _CATEGORY_ORDER:
            cat_findings = [f for f in findings if f.category.value == category]
            if not cat_findings:
                continue
            lines.append(f"#### {_CATEGORY_LABEL[category]}")
            for f in cat_findings:
                loc = f.file + (f":{f.line_number}" if f.line_number else "")
                emoji = _SEVERITY_EMOJI.get(f.severity.value, "")
                lines.append(f"- {emoji} **[{f.severity.value.upper()}]** `{loc}` — {f.issue}")
                if f.explanation:
                    lines.append(f"  - Why it matters: {f.explanation}")
                if f.impact:
                    lines.append(f"  - Impact: {f.impact}")
                if f.recommendation:
                    lines.append(f"  - Recommendation: {f.recommendation}")
                lines.append(f"  - Confidence: {f.confidence:.0%}")
            lines.append("")
        lines.append("</details>")
    else:
        lines.append("No issues found.")

    lines.append("")
    lines.append(f"[View full analysis on the dashboard]({summary.dashboard_url})")
    lines.append("")
    lines.append("---")
    if summary.passed:
        lines.append("**Status: All checks passed. Ready to merge.**")
    else:
        lines.append("**Status: Blocked \u2014 critical issues must be fixed before merge.**")
    return "\n".join(lines)


def _category_severity_counts(findings: list[Finding], category: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for f in findings:
        if f.category.value != category:
            continue
        counts[f.severity.value] = counts.get(f.severity.value, 0) + 1
    return counts
