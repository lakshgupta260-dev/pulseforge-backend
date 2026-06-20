from typing import Optional

from pydantic import BaseModel, Field


class EvaluationCreate(BaseModel):
    project_id: int
    reviewer_id: int
    innovation_score: float = Field(ge=0, le=10)
    technical_score: float = Field(ge=0, le=10)
    impact_score: float = Field(ge=0, le=10)
    presentation_score: float = Field(ge=0, le=10)
    feedback_text: Optional[str] = None
