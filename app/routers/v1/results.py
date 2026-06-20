from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.results import ResultsService

router = APIRouter(prefix="/api/results", tags=["Results Processing"])


@router.get("/rankings")
def get_rankings(db: Session = Depends(get_db)):
    """
    Transparent, confidence-scored project rankings (PS1 section 4.6).
    Tie-break order: normalized mean score -> technical score -> earliest
    submission. Run /api/evaluations/normalize first for accurate ranking.
    """
    service = ResultsService(db)
    return {"rankings": service.generate_rankings()}


@router.get("/feedback/{project_id}")
def get_feedback(project_id: int, db: Session = Depends(get_db)):
    """Aggregated per-criterion feedback for a single project."""
    service = ResultsService(db)
    try:
        return service.generate_feedback(project_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
