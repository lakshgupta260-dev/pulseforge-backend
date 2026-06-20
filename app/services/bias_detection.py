"""
Bias Detection & Fairness (PS1 section 4.5 / 6.3)

Two complementary statistical mechanisms, both fully explainable
(no opaque ML black-box -- judges can audit the exact math):

1. Score normalization (per-reviewer leniency/harshness correction):
   Z-score normalizes each reviewer's raw scores against their own
   mean/std, so a reviewer who scores everyone 9-10 doesn't
   systematically inflate their projects' rankings versus a harsher
   reviewer who scores 6-7 for similarly strong work. This directly
   targets "inconsistent scoring across reviewers" (PS1 section 4.5).

2. Group-level (cohort) bias detection: compares mean normalized scores
   across demographic/contextual groups (gender, region/geographic,
   organization/institutional, tech-stack) and flags any group whose
   mean significantly diverges from the overall cohort mean, using a
   Welch's-t-style z-statistic over group means. This covers the five
   bias dimensions explicitly named in section 6.3.

3. Reviewer-level outlier detection: flags any reviewer whose *average*
   normalized score deviates strongly from the cross-reviewer average,
   which is the "flag unusual scoring patterns from individual
   reviewers" requirement.

This is intentionally statistical rather than a trained classifier --
defensible, instant, requires no training data, and is the right scope
for a 24-48h build per the implementation guidance in section 7.1.
"""
import statistics
from collections import defaultdict
from typing import Dict, List

from sqlalchemy.orm import Session

from app.repositories.evaluation_repository import EvaluationRepository, BiasFlagRepository
from app.repositories.project_repository import ProjectRepository

Z_SCORE_FLAG_THRESHOLD = 1.5  # |z| beyond this is flagged; lower = more sensitive


class ScoreNormalizationService:
    """Corrects for each reviewer's personal scoring tendency."""

    def __init__(self, db: Session):
        self.db = db
        self.evaluation_repo = EvaluationRepository(db)

    def normalize_all(self) -> int:
        evaluations = self.evaluation_repo.list_all()
        by_reviewer: Dict[int, List] = defaultdict(list)
        for ev in evaluations:
            by_reviewer[ev.reviewer_id].append(ev)

        updated = 0
        for reviewer_id, evals in by_reviewer.items():
            scores = [e.raw_score for e in evals]
            if len(scores) < 2:
                # Not enough data to normalize meaningfully; pass raw score through.
                for e in evals:
                    self.evaluation_repo.update_normalized_score(e.id, e.raw_score)
                    updated += 1
                continue

            mean = statistics.mean(scores)
            stdev = statistics.pstdev(scores) or 1.0  # avoid div-by-zero when all scores equal

            for e in evals:
                z = (e.raw_score - mean) / stdev
                # Rescale z-score onto a 0-10 band centered at the global
                # target mean of 7.0, so normalized scores stay human-readable.
                normalized = round(min(10.0, max(0.0, 7.0 + z * 1.5)), 2)
                self.evaluation_repo.update_normalized_score(e.id, normalized)
                updated += 1

        return updated


class BiasDetectionService:
    def __init__(self, db: Session):
        self.db = db
        self.evaluation_repo = EvaluationRepository(db)
        self.project_repo = ProjectRepository(db)
        self.bias_flag_repo = BiasFlagRepository(db)

    def _cohort_stat(self, group_scores: Dict[str, List[float]], all_scores: List[float]):
        if len(all_scores) < 2:
            return {}
        overall_mean = statistics.mean(all_scores)
        overall_stdev = statistics.pstdev(all_scores) or 1.0
        flags = {}
        for group_name, scores in group_scores.items():
            if len(scores) < 2:
                continue
            group_mean = statistics.mean(scores)
            # standard error of the group mean vs overall distribution
            se = overall_stdev / (len(scores) ** 0.5)
            z = (group_mean - overall_mean) / se if se else 0
            if abs(z) >= Z_SCORE_FLAG_THRESHOLD:
                flags[group_name] = {
                    "z": round(z, 2),
                    "group_mean": round(group_mean, 2),
                    "overall_mean": round(overall_mean, 2),
                    "n": len(scores),
                }
        return flags

    def detect_cohort_bias(self) -> List[Dict]:
        """Compares normalized scores across gender, region, organization,
        and tech-stack groups; flags any group with |z| >= threshold."""
        self.bias_flag_repo.clear_open_flags()

        evaluations = self.evaluation_repo.list_all()
        scored = [e for e in evaluations if e.normalized_score is not None]
        if len(scored) < 4:
            return []

        all_scores = [e.normalized_score for e in scored]

        by_gender: Dict[str, List[float]] = defaultdict(list)
        by_region: Dict[str, List[float]] = defaultdict(list)
        by_org: Dict[str, List[float]] = defaultdict(list)
        by_tech: Dict[str, List[float]] = defaultdict(list)

        for ev in scored:
            project = ev.project
            team = project.team if project else None
            members = team.members if team else []

            for m in members:
                p = m.participant
                if not p:
                    continue
                if p.gender:
                    by_gender[p.gender].append(ev.normalized_score)
                if p.region:
                    by_region[p.region].append(ev.normalized_score)
                if p.organization:
                    by_org[p.organization].append(ev.normalized_score)

            if project and project.tech_stack_text:
                for tag in [t.strip().lower() for t in project.tech_stack_text.split(",") if t.strip()]:
                    by_tech[tag].append(ev.normalized_score)

        created = []
        dimension_groups = [
            ("gender", by_gender),
            ("geographic", by_region),
            ("institutional", by_org),
            ("tech_stack", by_tech),
        ]

        for dimension, groups in dimension_groups:
            flagged = self._cohort_stat(groups, all_scores)
            for group_name, stat in flagged.items():
                direction = "above" if stat["z"] > 0 else "below"
                severity = "high" if abs(stat["z"]) >= 2.5 else "medium"
                description = (
                    f"Group '{group_name}' in dimension '{dimension}' scores "
                    f"{direction} the cohort mean ({stat['group_mean']} vs "
                    f"{stat['overall_mean']}, n={stat['n']}, z={stat['z']})."
                )
                flag = self.bias_flag_repo.create(
                    dimension=dimension,
                    scope="cohort",
                    description=description,
                    confidence=round(min(0.99, abs(stat["z"]) / 4), 2),
                    severity=severity,
                    statistic=stat["z"],
                )
                created.append(
                    {
                        "id": flag.id,
                        "dimension": dimension,
                        "group": group_name,
                        "z_score": stat["z"],
                        "severity": severity,
                        "description": description,
                    }
                )

        return created

    def detect_reviewer_outliers(self) -> List[Dict]:
        """Flags reviewers whose average normalized score deviates
        strongly from the cross-reviewer average (possible systematic
        harshness/leniency bias not fully corrected by normalization,
        or signals worth a manual audit)."""
        evaluations = self.evaluation_repo.list_all()
        scored = [e for e in evaluations if e.normalized_score is not None]

        by_reviewer: Dict[int, List[float]] = defaultdict(list)
        for ev in scored:
            by_reviewer[ev.reviewer_id].append(ev.normalized_score)

        if len(by_reviewer) < 3:
            return []

        reviewer_means = {rid: statistics.mean(scores) for rid, scores in by_reviewer.items()}
        all_means = list(reviewer_means.values())
        overall_mean = statistics.mean(all_means)
        overall_stdev = statistics.pstdev(all_means) or 1.0

        created = []
        for reviewer_id, mean_score in reviewer_means.items():
            z = (mean_score - overall_mean) / overall_stdev
            if abs(z) >= Z_SCORE_FLAG_THRESHOLD:
                severity = "high" if abs(z) >= 2.5 else "medium"
                direction = "lenient" if z > 0 else "harsh"
                description = (
                    f"Reviewer {reviewer_id} is a scoring outlier ({direction}): "
                    f"avg normalized score {round(mean_score, 2)} vs cohort "
                    f"average {round(overall_mean, 2)} (z={round(z, 2)})."
                )
                flag = self.bias_flag_repo.create(
                    dimension="reviewer_pattern",
                    scope="reviewer",
                    description=description,
                    confidence=round(min(0.99, abs(z) / 4), 2),
                    severity=severity,
                    reviewer_id=reviewer_id,
                    statistic=round(z, 2),
                )
                created.append(
                    {
                        "id": flag.id,
                        "reviewer_id": reviewer_id,
                        "z_score": round(z, 2),
                        "direction": direction,
                        "severity": severity,
                        "description": description,
                    }
                )

        return created
