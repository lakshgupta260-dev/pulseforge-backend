from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app import models  # noqa: F401
from app.routers.v1 import (
    participants,
    duplicates,
    skills,
    teams,
    projects,
    reviewers,
    evaluations,
    results,
    analytics,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="AI-powered Hackathon Intelligence Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(participants.router)
app.include_router(duplicates.router)
app.include_router(skills.router)
app.include_router(teams.router)
app.include_router(projects.router)
app.include_router(reviewers.router)
app.include_router(evaluations.router)
app.include_router(results.router)
app.include_router(analytics.router)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": settings.app_name}

