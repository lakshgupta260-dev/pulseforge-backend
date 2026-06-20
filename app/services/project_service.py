from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.project_repository import ProjectRepository
from app.repositories.team_repository import TeamRepository
from app.models.project import Project


class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.team_repo = TeamRepository(db)

    def create_project(
        self,
        team_id: int,
        title: str,
        description: str,
        tech_stack_text: Optional[str] = None,
        repo_url: Optional[str] = None,
        demo_url: Optional[str] = None,
    ) -> Project:
        team = self.team_repo.get_by_id(team_id)
        if not team:
            raise ValueError(f"Team {team_id} not found")

        return self.project_repo.create(
            team_id=team_id,
            title=title,
            description=description,
            tech_stack_text=tech_stack_text,
            repo_url=repo_url,
            demo_url=demo_url,
        )
