from enum import Enum

from pydantic import BaseModel, Field, model_validator


class Provider(str, Enum):
    github = "github"
    gitlab = "gitlab"


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class Category(str, Enum):
    security = "security"
    performance = "performance"
    code_quality = "code_quality"
    testing = "testing"


class PRReviewInput(BaseModel):
    """Everything the workflow needs to review one commit of one PR/MR."""

    provider: Provider
    repo_full_name: str
    repo_external_id: str
    pr_number: int
    commit_sha: str
    base_sha: str
    author: str
    title: str
    source_branch: str
    target_branch: str
    html_url: str
    review_round: int = 1


class CodeFileDiff(BaseModel):
    path: str
    status: str = "modified"
    additions: int = 0
    deletions: int = 0
    patch: str = ""


class CodeContext(BaseModel):
    files: list[CodeFileDiff]


class Finding(BaseModel):
    category: Category
    severity: Severity
    file: str
    line_number: int | None = None
    issue: str
    explanation: str | None = None
    impact: str | None = None
    recommendation: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    agent: str = ""


class AgentResult(BaseModel):
    agent: str
    category: Category
    findings: list[Finding] = Field(default_factory=list)
    passed: bool = True
    error: str | None = None

    @model_validator(mode="after")
    def _compute_passed(self) -> "AgentResult":
        blocking = {Severity.critical, Severity.high}
        if any(f.severity in blocking for f in self.findings):
            self.passed = False
        return self


class ReviewSummary(BaseModel):
    review_run_id: str
    total_findings: int
    by_category: dict[str, int]
    by_severity: dict[str, int]
    dashboard_url: str
    passed: bool = True


class PersistedReview(BaseModel):
    review_run_id: str
    dashboard_url: str


class ReviewWorkflowResult(BaseModel):
    review_run_id: str
    summary: ReviewSummary
    comment_url: str | None = None
    skipped: bool = False
    skip_reason: str | None = None
