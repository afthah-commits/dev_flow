import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.api import deps
from app.models.api_key import APIKey
from app.models.project import Project
from app.models.task import Task
from typing import Any

router = APIRouter()

# Local Rate Limiter Simulation
from collections import defaultdict
import time
RATE_LIMIT_DB = defaultdict(list)
RATE_LIMIT = 100 # requests
RATE_WINDOW = 60 # seconds

def rate_limit(api_key: APIKey):
    now = time.time()
    RATE_LIMIT_DB[api_key.id] = [t for t in RATE_LIMIT_DB[api_key.id] if now - t < RATE_WINDOW]
    if len(RATE_LIMIT_DB[api_key.id]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    RATE_LIMIT_DB[api_key.id].append(now)

@router.get("/projects")
def get_projects(
    db: Session = Depends(deps.get_db),
    api_key: APIKey = Depends(deps.get_api_key_auth)
) -> Any:
    rate_limit(api_key)
    if "projects:read" not in api_key.scopes:
        raise HTTPException(status_code=403, detail="Missing scope projects:read")
        
    projects = db.query(Project).filter(Project.organization_id == uuid.UUID(str(api_key.organization_id))).all()
    return projects

@router.get("/projects/{project_id}/tasks")
def get_tasks(
    project_id: str,
    db: Session = Depends(deps.get_db),
    api_key: APIKey = Depends(deps.get_api_key_auth)
) -> Any:
    rate_limit(api_key)
    if "tasks:read" not in api_key.scopes:
        raise HTTPException(status_code=403, detail="Missing scope tasks:read")
        
    project = db.query(Project).filter(Project.id == project_id, Project.organization_id == uuid.UUID(str(api_key.organization_id))).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    return tasks
