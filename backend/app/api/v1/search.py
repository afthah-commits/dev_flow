from fastapi import APIRouter, Depends, Query
from typing import Any
from sqlalchemy.orm import Session
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.collaboration import Discussion

router = APIRouter()

@router.get("")
def search_global(
    q: str = Query(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    
    # Very basic search implementation for demonstration
    term = f"%{q}%"
    
    projects = db.query(Project).filter(Project.organization_id == org_id, Project.name.ilike(term)).limit(5).all()
    tasks = db.query(Task).join(Project).filter(Project.organization_id == org_id, Task.title.ilike(term)).limit(5).all()
    discussions = db.query(Discussion).filter(Discussion.organization_id == org_id, Discussion.title.ilike(term)).limit(5).all()
    
    return {
        "projects": [{"id": p.id, "title": p.name} for p in projects],
        "tasks": [{"id": t.id, "title": t.title, "project_id": t.project_id} for t in tasks],
        "discussions": [{"id": d.id, "title": d.title, "project_id": d.project_id} for d in discussions],
        "users": [],
        "sprints": [],
        "releases": []
    }
