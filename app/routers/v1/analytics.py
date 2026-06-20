from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["Analytics Dashboard"])


@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    """
    Real-time aggregate metrics across the hackathon lifecycle
    (PS1 section 4.7): participants, teams, projects, evaluation
    completion, reviewer workload balance, and fairness/bias-flag counts.
    """
    service = AnalyticsService(db)
    return service.overview()
