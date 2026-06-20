from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    team_id: int
    title: str
    description: str
    tech_stack_text: Optional[str] = None
    repo_url: Optional[str] = None
    demo_url: Optional[str] = None


class ProjectOut(BaseModel):
    id: int
    team_id: int
    title: str
    description: str
    tech_stack_text: Optional[str] = None
    repo_url: Optional[str] = None
    demo_url: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
