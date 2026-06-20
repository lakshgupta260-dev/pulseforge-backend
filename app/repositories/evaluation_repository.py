from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.evaluation import Evaluation, BiasFlag


class EvaluationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        project_id: int,
        reviewer_id: int,
        innovation_score: float,
        technical_score: float,
        impact_score: float,
        presentation_score: float,
        raw_score: float,
        feedback_text: Optional[str] = None,
    ) -> Evaluation:
        evaluation = Evaluation(
            project_id=project_id,
            reviewer_id=reviewer_id,
            innovation_score=innovation_score,
            technical_score=technical_score,
            impact_score=impact_score,
            presentation_score=presentation_score,
            raw_score=raw_score,
            feedback_text=feedback_text,
        )
        self.db.add(evaluation)
        self.db.commit()
        self.db.refresh(evaluation)
        return evaluation

    def get_by_id(self, evaluation_id: int) -> Optional[Evaluation]:
        return self.db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()

    def list_for_project(self, project_id: int) -> List[Evaluation]:
        return self.db.query(Evaluation).filter(Evaluation.project_id == project_id).all()

    def list_for_reviewer(self, reviewer_id: int) -> List[Evaluation]:
        return self.db.query(Evaluation).filter(Evaluation.reviewer_id == reviewer_id).all()

    def list_all(self) -> List[Evaluation]:
        return self.db.query(Evaluation).all()

    def update_normalized_score(self, evaluation_id: int, normalized_score: float) -> None:
        evaluation = self.get_by_id(evaluation_id)
        if evaluation:
            evaluation.normalized_score = normalized_score
            self.db.commit()


class BiasFlagRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        dimension: str,
        scope: str,
        description: str,
        confidence: float,
        severity: str = "medium",
        reviewer_id: Optional[int] = None,
        evaluation_id: Optional[int] = None,
        statistic: Optional[float] = None,
    ) -> BiasFlag:
        flag = BiasFlag(
            dimension=dimension,
            scope=scope,
            description=description,
            confidence=confidence,
            severity=severity,
            reviewer_id=reviewer_id,
            evaluation_id=evaluation_id,
            statistic=statistic,
        )
        self.db.add(flag)
        self.db.commit()
        self.db.refresh(flag)
        return flag

    def list_all(self, status: Optional[str] = None) -> List[BiasFlag]:
        query = self.db.query(BiasFlag)
        if status:
            query = query.filter(BiasFlag.status == status)
        return query.order_by(BiasFlag.created_at.desc()).all()

    def clear_open_flags(self) -> int:
        """Clears prior open flags before a fresh detection run."""
        rows = self.db.query(BiasFlag).filter(BiasFlag.status == "open").all()
        count = len(rows)
        for row in rows:
            self.db.delete(row)
        self.db.commit()
        return count
