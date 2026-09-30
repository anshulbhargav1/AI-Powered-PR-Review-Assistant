from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from pr_review_shared.models import FindingRow, ReviewRun

from ..deps import get_db
from ..schemas import StatsOut

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)) -> StatsOut:
    runs = db.execute(select(ReviewRun)).scalars().all()
    findings = db.execute(select(FindingRow)).scalars().all()

    by_category = Counter(f.category for f in findings)
    by_severity = Counter(f.severity for f in findings)

    per_day: Counter = Counter()
    for r in runs:
        if r.started_at:
            per_day[r.started_at.date().isoformat()] += 1

    return StatsOut(
        total_reviews=len(runs),
        total_findings=len(findings),
        by_category=dict(by_category),
        by_severity=dict(by_severity),
        recent_reviews_per_day=dict(sorted(per_day.items())[-14:]),
    )
