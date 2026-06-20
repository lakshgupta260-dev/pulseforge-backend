from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Evaluation(Base):
    """A single reviewer's score+feedback for a single project.
    raw_score is what the reviewer entered; normalized_score is computed
    later to correct for each reviewer's personal scoring tendency
    (some reviewers run harsh, some run lenient) -- see ScoreNormalization."""

    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("reviewers.id"), nullable=False)

    innovation_score = Column(Float, nullable=False)
    technical_score = Column(Float, nullable=False)
    impact_score = Column(Float, nullable=False)
    presentation_score = Column(Float, nullable=False)

    raw_score = Column(Float, nullable=False)  # weighted composite, pre-normalization
    normalized_score = Column(Float, nullable=True)  # filled in by ScoreNormalizationService

    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="evaluations")
    reviewer = relationship("Reviewer")


class BiasFlag(Base):
    """A statistically-detected bias signal raised against either a single
    evaluation (reviewer-level outlier) or a hackathon-wide pattern
    (group-level disparity across a demographic dimension)."""

    __tablename__ = "bias_flags"

    id = Column(Integer, primary_key=True, index=True)
    dimension = Column(String, nullable=False)  # gender | geographic | institutional | tech_stack
    scope = Column(String, nullable=False)  # "reviewer" | "cohort"
    reviewer_id = Column(Integer, ForeignKey("reviewers.id"), nullable=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=True)

    description = Column(Text, nullable=False)
    severity = Column(String, default="medium")  # low | medium | high
    statistic = Column(Float, nullable=True)  # e.g. z-score or mean-gap magnitude
    confidence = Column(Float, nullable=False)

    status = Column(String, default="open")  # open | reviewed | dismissed
    created_at = Column(DateTime, default=datetime.utcnow)
