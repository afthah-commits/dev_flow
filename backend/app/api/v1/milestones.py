from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, get_current_user, require_organization_member
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.milestone import Milestone
from app.schemas.milestone import MilestoneCreate, MilestoneUpdate, MilestoneResponse, MilestoneDetailsResponse, MilestoneStats
from app.models.organization import OrganizationRole

router = APIRouter()

def get_project_and_check_access(db: Session, project_id: UUID, user: User, required_role: OrganizationRole = OrganizationRole.MEMBER) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    check_organization_permission(db, user.id, project.organization_id, required_role)
    return project

@router.post("", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
def create_milestone(
    project_id: UUID,
    milestone_in: MilestoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.ADMIN)
    
    milestone = Milestone(
        **milestone_in.model_dump(),
        project_id=project_id,
        created_by_id=current_user.id
    )
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone

@router.get("", response_model=List[MilestoneResponse])
def get_milestones(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.MEMBER)
    milestones = db.query(Milestone).filter(Milestone.project_id == project_id).order_by(Milestone.position.asc()).all()
    return milestones

@router.get("/{milestone_id}", response_model=MilestoneDetailsResponse)
def get_milestone(
    project_id: UUID,
    milestone_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.MEMBER)
    milestone = db.query(Milestone).filter(Milestone.id == milestone_id, Milestone.project_id == project_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return milestone

@router.patch("/{milestone_id}", response_model=MilestoneResponse)
def update_milestone(
    project_id: UUID,
    milestone_id: UUID,
    milestone_in: MilestoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.ADMIN)
    milestone = db.query(Milestone).filter(Milestone.id == milestone_id, Milestone.project_id == project_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    
    update_data = milestone_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(milestone, field, value)
    
    db.commit()
    db.refresh(milestone)
    return milestone

@router.delete("/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_milestone(
    project_id: UUID,
    milestone_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.ADMIN)
    milestone = db.query(Milestone).filter(Milestone.id == milestone_id, Milestone.project_id == project_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    
    # Nullify milestone_id on tasks
    db.query(Task).filter(Task.milestone_id == milestone.id).update({"milestone_id": None})
    
    db.delete(milestone)
    db.commit()

@router.get("/{milestone_id}/stats", response_model=MilestoneStats)
def get_milestone_stats(
    project_id: UUID,
    milestone_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.MEMBER)
    
    total_tasks = db.query(func.count(Task.id)).filter(Task.milestone_id == milestone_id).scalar() or 0
    completed_tasks = db.query(func.count(Task.id)).filter(Task.milestone_id == milestone_id, Task.status == "DONE").scalar() or 0
    
    total_points = db.query(func.sum(Task.estimate_points)).filter(Task.milestone_id == milestone_id).scalar() or 0.0
    completed_points = db.query(func.sum(Task.estimate_points)).filter(Task.milestone_id == milestone_id, Task.status == "DONE").scalar() or 0.0
    
    pct = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
    
    return MilestoneStats(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        total_points=total_points,
        completed_points=completed_points,
        remaining_points=total_points - completed_points,
        progress_percentage=pct
    )
