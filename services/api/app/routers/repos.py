from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pr_review_shared.models import Repository, ReviewRun

from ..deps import get_db
from ..schemas import RepositoryOut

router = APIRouter(prefix="/api/repos", tags=["repos"])


@router.get("", response_model=list[RepositoryOut])
def list_repos(db: Session = Depends(get_db)) -> list[RepositoryOut]:
    counts = dict(
        db.execute(
            select(ReviewRun.repository_id, func.count(ReviewRun.id)).group_by(ReviewRun.repository_id)
        ).all()
    )
    repos = db.execute(select(Repository)).scalars().all()
    return [
        RepositoryOut(id=r.id, provider=r.provider, full_name=r.full_name, review_run_count=counts.get(r.id, 0))
        for r in repos
    ]
