"""
Results Processing (PS1 section 4.6)

Generates transparent, confidence-scored project rankings from
normalized evaluation scores. Confidence is derived from reviewer
agreement (inverse of score variance) -- projects reviewed consistently
by multiple reviewers get high confidence; projects with only one
reviewer or wildly disagreeing reviewers get lower confidence, which is
exactly the kind of transparency PS1 section 6 calls for ("ranking
algorithms with confidence intervals").

Tie-breaking order: normalized mean score -> technical_score mean
(reward technical depth on ties) -> earliest submission (created_at) --
fully deterministic and auditable.
"""
import statistics
from collections import defaultdict
from typing import Dict, List

from sqlalchemy.orm import Session

from app.repositories.evaluation_repository import EvaluationRepository
from app.repositories.project_repository import ProjectRepository


class ResultsService:
    def __init__(self, db: Session):
        self.db = db
        self.evaluation_repo = EvaluationRepository(db)
        self.project_repo = ProjectRepository(db)

    def generate_rankings(self) -> List[Dict]:
        projects = self.project_repo.list_all()
        rankings = []

        for project in projects:
            evals = self.evaluation_repo.list_for_project(project.id)
            scored = [e for e in evals if e.normalized_score is not None]

            if not scored:
                rankings.append(
                    {
                        "project_id": project.id,
                        "title": project.title,
                        "mean_score": None,
                        "confidence": 0.0,
                        "reviewer_count": 0,
                        "rank": None,
                        "status": "awaiting_evaluation",
                    }
                )
                continue

            scores = [e.normalized_score for e in scored]
            mean_score = round(statistics.mean(scores), 2)
            technical_mean = round(statistics.mean([e.technical_score for e in scored]), 2)

            if len(scores) >= 2:
                stdev = statistics.pstdev(scores)
                # Confidence shrinks as reviewer disagreement (stdev) grows;
                # a perfectly agreeing pair of reviewers -> confidence ~0.95+.
                confidence = round(max(0.3, 1.0 - (stdev / 10)), 2)
            else:
                confidence = 0.5  # single reviewer: capped, since there's no agreement signal

            rankings.append(
                {
                    "project_id": project.id,
                    "title": project.title,
                    "mean_score": mean_score,
                    "technical_mean": technical_mean,
                    "confidence": confidence,
                    "reviewer_count": len(scored),
                    "created_at": project.created_at,
                    "status": "ranked",
                }
            )

        ranked = [r for r in rankings if r["status"] == "ranked"]
        unranked = [r for r in rankings if r["status"] != "ranked"]

        ranked.sort(
            key=lambda r: (
                -r["mean_score"],
                -r["technical_mean"],
                r["created_at"],
            )
        )

        for i, r in enumerate(ranked, start=1):
            r["rank"] = i
            r.pop("created_at", None)  # internal tie-break key only, not user-facing

        return ranked + unranked

    def generate_feedback(self, project_id: int) -> Dict:
        """Generates a short, structured feedback summary for a project
        by aggregating reviewer feedback text and per-criterion averages --
        the 'comprehensive feedback' requirement from section 4.6."""
        project = self.project_repo.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        evals = self.evaluation_repo.list_for_project(project_id)
        if not evals:
            return {
                "project_id": project_id,
                "title": project.title,
                "feedback": "No evaluations submitted yet.",
                "criteria_breakdown": {},
            }

        criteria_breakdown = {
            "innovation": round(statistics.mean([e.innovation_score for e in evals]), 2),
            "technical": round(statistics.mean([e.technical_score for e in evals]), 2),
            "impact": round(statistics.mean([e.impact_score for e in evals]), 2),
            "presentation": round(statistics.mean([e.presentation_score for e in evals]), 2),
        }

        comments = [e.feedback_text for e in evals if e.feedback_text]

        return {
            "project_id": project_id,
            "title": project.title,
            "criteria_breakdown": criteria_breakdown,
            "reviewer_comments": comments,
            "reviewer_count": len(evals),
        }
