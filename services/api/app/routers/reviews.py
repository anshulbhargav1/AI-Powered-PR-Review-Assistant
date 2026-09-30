from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from pr_review_shared.models import ReviewRun

from ..deps import get_db
from ..schemas import ReviewRunDetailOut, ReviewRunOut

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.get("", response_model=list[ReviewRunOut])
def list_reviews(
    repository_id: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[ReviewRun]:
    stmt = select(ReviewRun).order_by(desc(ReviewRun.started_at)).offset(offset).limit(limit)
    if repository_id:
        stmt = stmt.where(ReviewRun.repository_id == repository_id)
    return list(db.execute(stmt).scalars().all())


@router.get("/{review_run_id}", response_model=ReviewRunDetailOut)
def get_review(review_run_id: str, db: Session = Depends(get_db)) -> ReviewRun:
    run = db.get(ReviewRun, review_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="review run not found")
    return run
