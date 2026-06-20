from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Project(Base):
    """A team's hackathon submission. This is the central entity that
    reviewer assignment, evaluation, and results all hang off of."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    tech_stack_text = Column(String, nullable=True)  # raw, e.g. "React, FastAPI, Postgres"
    repo_url = Column(String, nullable=True)
    demo_url = Column(String, nullable=True)
    status = Column(String, default="submitted")  # submitted | under_review | evaluated
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team")
    assignments = relationship("ReviewerAssignment", back_populates="project")
    evaluations = relationship("Evaluation", back_populates="project")
