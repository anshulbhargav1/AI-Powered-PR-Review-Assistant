"""Pure helpers for comparing the current review round against the previous one.

Runs directly inside the workflow (no I/O, deterministic), so it's kept as a
tiny standalone module rather than a Temporal activity."""

from typing import Iterable

from pr_review_shared.schemas import Finding

from .activities.io_models import FindingSnapshot


def _key(f) -> tuple:
    # Match on the semantic identity of a finding, not object identity - so re-runs
    # of the same LLM prompt still line up round-over-round even if wording drifts
    # slightly. Truncating `issue` keeps minor rephrasings from splitting a finding.
    return (
        getattr(f.category, "value", f.category),
        f.file,
        f.line_number,
        (f.issue or "")[:80],
    )


def compute_round_diff(
    previous: Iterable[FindingSnapshot],
    current: Iterable[Finding],
) -> dict:
    prev_list = list(previous)
    curr_list = list(current)
    prev_keys = {_key(f) for f in prev_list}
    curr_keys = {_key(f) for f in curr_list}

    resolved = [f for f in prev_list if _key(f) not in curr_keys]
    still_present = [f for f in curr_list if _key(f) in prev_keys]
    new_findings = [f for f in curr_list if _key(f) not in prev_keys]

    return {
        "resolved": resolved,
        "still_present": still_present,
        "new": new_findings,
    }
