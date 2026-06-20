from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        team_id: int,
        title: str,
        description: str,
        tech_stack_text: Optional[str] = None,
        repo_url: Optional[str] = None,
        demo_url: Optional[str] = None,
    ) -> Project:
        project = Project(
            team_id=team_id,
            title=title,
            description=description,
            tech_stack_text=tech_stack_text,
            repo_url=repo_url,
            demo_url=demo_url,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_by_id(self, project_id: int) -> Optional[Project]:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def list_all(self) -> List[Project]:
        return self.db.query(Project).all()

    def update_status(self, project_id: int, status: str) -> Optional[Project]:
        project = self.get_by_id(project_id)
        if not project:
            return None
        project.status = status
        self.db.commit()
        self.db.refresh(project)
        return project
