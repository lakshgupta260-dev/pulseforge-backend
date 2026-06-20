from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.project import ProjectCreate, ProjectOut
from app.services.project_service import ProjectService
from app.repositories.project_repository import ProjectRepository

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def submit_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    service = ProjectService(db)
    try:
        project = service.create_project(
            team_id=payload.team_id,
            title=payload.title,
            description=payload.description,
            tech_stack_text=payload.tech_stack_text,
            repo_url=payload.repo_url,
            demo_url=payload.demo_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return project


@router.get("/", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    return repo.list_all()


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project
