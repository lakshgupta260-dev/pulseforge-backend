from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.evaluation_repository import EvaluationRepository
from app.repositories.project_repository import ProjectRepository
from app.models.evaluation import Evaluation

# Composite weighting for the four judged criteria. Equal weighting is the
# safe default for a hackathon rubric; organizers can tune this later via
# the configurable-criteria hook noted in PS1 section 4.5.
CRITERIA_WEIGHTS = {
    "innovation": 0.30,
    "technical": 0.30,
    "impact": 0.25,
    "presentation": 0.15,
}


class EvaluationService:
    def __init__(self, db: Session):
        self.db = db
        self.evaluation_repo = EvaluationRepository(db)
        self.project_repo = ProjectRepository(db)

    def submit_evaluation(
        self,
        project_id: int,
        reviewer_id: int,
        innovation_score: float,
        technical_score: float,
        impact_score: float,
        presentation_score: float,
        feedback_text: Optional[str] = None,
    ) -> Evaluation:
        project = self.project_repo.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        raw_score = round(
            innovation_score * CRITERIA_WEIGHTS["innovation"]
            + technical_score * CRITERIA_WEIGHTS["technical"]
            + impact_score * CRITERIA_WEIGHTS["impact"]
            + presentation_score * CRITERIA_WEIGHTS["presentation"],
            2,
        )

        evaluation = self.evaluation_repo.create(
            project_id=project_id,
            reviewer_id=reviewer_id,
            innovation_score=innovation_score,
            technical_score=technical_score,
            impact_score=impact_score,
            presentation_score=presentation_score,
            raw_score=raw_score,
            feedback_text=feedback_text,
        )

        self.project_repo.update_status(project_id, "under_review")
        return evaluation
