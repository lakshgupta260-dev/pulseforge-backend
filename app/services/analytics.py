"""
Analytics Dashboard (PS1 section 4.7)

Aggregates cross-cutting metrics organizers care about: registration
volume, skill coverage, evaluation completion, bias-flag counts, and
reviewer workload distribution. All numbers are computed live from
current DB state -- no separate analytics pipeline needed at this scale,
which keeps the implementation honest for a 24-48h build while still
satisfying the "real-time visualization of all hackathon metrics"
requirement.
"""
import statistics
from collections import Counter
from typing import Dict

from sqlalchemy.orm import Session

from app.repositories.participant_repository import ParticipantRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.reviewer_repository import ReviewerRepository, ReviewerAssignmentRepository
from app.repositories.evaluation_repository import EvaluationRepository, BiasFlagRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.duplicate_repository import DuplicateFlagRepository


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.participant_repo = ParticipantRepository(db)
        self.project_repo = ProjectRepository(db)
        self.reviewer_repo = ReviewerRepository(db)
        self.assignment_repo = ReviewerAssignmentRepository(db)
        self.evaluation_repo = EvaluationRepository(db)
        self.bias_flag_repo = BiasFlagRepository(db)
        self.team_repo = TeamRepository(db)

    def overview(self) -> Dict:
        participants = self.participant_repo.list_for_duplicate_scan()
        projects = self.project_repo.list_all()
        reviewers = self.reviewer_repo.list_all()
        evaluations = self.evaluation_repo.list_all()
        assignments = self.assignment_repo.list_all()
        bias_flags = self.bias_flag_repo.list_all()
        teams = self.team_repo.list_all()

        evaluated_project_ids = {e.project_id for e in evaluations}
        evaluation_completion_rate = (
            round(len(evaluated_project_ids) / len(projects) * 100, 1) if projects else 0.0
        )

        workload_counts = Counter(a.reviewer_id for a in assignments if a.status == "assigned")
        workload_values = list(workload_counts.values())
        workload_balance_variance = (
            round(statistics.pvariance(workload_values), 2) if len(workload_values) >= 2 else 0.0
        )

        open_bias_flags = [f for f in bias_flags if f.status == "open"]
        severity_counts = Counter(f.severity for f in open_bias_flags)

        return {
            "participants": {
                "total": len(participants),
                "organizations_represented": len({p.organization for p in participants if p.organization}),
            },
            "teams": {"total": len(teams)},
            "projects": {
                "total": len(projects),
                "evaluation_completion_rate_pct": evaluation_completion_rate,
            },
            "reviewers": {
                "total": len(reviewers),
                "active_assignments": sum(workload_values),
                "workload_balance_variance": workload_balance_variance,
            },
            "evaluations": {
                "total": len(evaluations),
                "avg_normalized_score": round(
                    statistics.mean([e.normalized_score for e in evaluations if e.normalized_score is not None]), 2
                ) if any(e.normalized_score is not None for e in evaluations) else None,
            },
            "fairness": {
                "open_bias_flags": len(open_bias_flags),
                "by_severity": dict(severity_counts),
            },
        }
