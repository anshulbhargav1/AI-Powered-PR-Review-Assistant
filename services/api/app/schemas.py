from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    severity: str
    file: str
    line_number: int | None
    issue: str
    explanation: str | None
    impact: str | None
    recommendation: str
    confidence: float
    agent: str


class ReviewRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    repository_id: str
    pr_number: int
    commit_sha: str
    title: str
    author: str
    html_url: str
    status: str
    total_findings: int
    by_category: dict
    by_severity: dict
    comment_url: str | None
    started_at: datetime
    completed_at: datetime | None


class ReviewRunDetailOut(ReviewRunOut):
    findings: list[FindingOut]


class RepositoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider: str
    full_name: str
    review_run_count: int = 0


class StatsOut(BaseModel):
    total_reviews: int
    total_findings: int
    by_category: dict[str, int]
    by_severity: dict[str, int]
    recent_reviews_per_day: dict[str, int]
