from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_organization_member
from app.models.user import User
from app.models.project import Project
from app.models.milestone import Milestone
from app.models.sprint import Sprint
from app.schemas.milestone import RoadmapResponse
from app.models.organization import OrganizationRole

router = APIRouter()

def get_project_and_check_access(db: Session, project_id: UUID, user: User, required_role: OrganizationRole = OrganizationRole.MEMBER) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    check_organization_permission(db, user.id, project.organization_id, required_role)
    return project

@router.get("", response_model=RoadmapResponse)
def get_roadmap(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.MEMBER)
    
    milestones = db.query(Milestone).filter(Milestone.project_id == project_id).order_by(Milestone.position.asc(), Milestone.start_date.asc()).all()
    sprints = db.query(Sprint).filter(Sprint.project_id == project_id).order_by(Sprint.start_date.asc()).all()
    
    return RoadmapResponse(
        milestones=milestones,
        sprints=sprints
    )
