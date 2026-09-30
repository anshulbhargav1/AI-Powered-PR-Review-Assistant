from pydantic import BaseModel

from pr_review_shared.schemas import Category, Finding, PRReviewInput, Provider, Severity


class PersistResultsInput(BaseModel):
    review_input: PRReviewInput
    review_run_id: str
    workflow_id: str
    findings: list[Finding]
    by_category: dict[str, int]
    by_severity: dict[str, int]


class PostCommentInput(BaseModel):
    review_input: PRReviewInput
    marker: str
    body: str


class SetCommitStatusInput(BaseModel):
    provider: Provider
    repo_full_name: str
    repo_external_id: str
    commit_sha: str
    passed: bool
    critical_count: int
    dashboard_url: str | None = None


class FindingSnapshot(BaseModel):
    category: Category
    file: str
    line_number: int | None = None
    issue: str
    severity: Severity


class FetchPreviousInput(BaseModel):
    provider: Provider
    repo_external_id: str
    pr_number: int
    current_round: int
