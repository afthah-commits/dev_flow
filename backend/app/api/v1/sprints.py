from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.api.deps import get_db, get_current_user, get_current_organization_id, require_organization_member
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.sprint import Sprint, SprintStatus, SprintSnapshot
from app.schemas.sprint import SprintCreate, SprintUpdate, SprintDetailsResponse, SprintResponse, SprintStats, SprintBurndown
from app.schemas.task import TaskResponse, BulkTaskOperation
from app.models.organization import OrganizationRole

router = APIRouter()

def get_project_and_check_access(db: Session, project_id: UUID, user: User, required_role: OrganizationRole = OrganizationRole.MEMBER) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    check_organization_permission(db, user.id, project.organization_id, required_role)
    return project

@router.post("", response_model=SprintResponse, status_code=status.HTTP_201_CREATED)
def create_sprint(
    project_id: UUID,
    sprint_in: SprintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    project = get_project_and_check_access(db, project_id, current_user, OrganizationRole.ADMIN)
    
    # Generate sprint key (e.g., PROJ-S1)
    sprint_count = db.query(Sprint).filter(Sprint.project_id == project_id).count()
    sprint_key = f"{project.key or 'PRJ'}-S{sprint_count + 1}"
    
    sprint = Sprint(
        **sprint_in.model_dump(),
        project_id=project_id,
        key=sprint_key,
        created_by_id=current_user.id
    )
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return sprint

@router.get("", response_model=List[SprintResponse])
def get_sprints(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.MEMBER)
    sprints = db.query(Sprint).filter(Sprint.project_id == project_id).order_by(Sprint.created_at.desc()).all()
    return sprints

@router.get("/{sprint_id}", response_model=SprintDetailsResponse)
def get_sprint(
    project_id: UUID,
    sprint_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.MEMBER)
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return sprint

@router.patch("/{sprint_id}", response_model=SprintResponse)
def update_sprint(
    project_id: UUID,
    sprint_id: UUID,
    sprint_in: SprintUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.ADMIN)
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    
    update_data = sprint_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sprint, field, value)
    
    db.commit()
    db.refresh(sprint)
    return sprint

@router.delete("/{sprint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sprint(
    project_id: UUID,
    sprint_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.ADMIN)
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    
    # Nullify sprint_id on tasks
    db.query(Task).filter(Task.sprint_id == sprint.id).update({"sprint_id": None})
    
    db.delete(sprint)
    db.commit()

@router.post("/{sprint_id}/start", response_model=SprintResponse)
def start_sprint(
    project_id: UUID,
    sprint_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.ADMIN)
    
    active_sprint = db.query(Sprint).filter(
        Sprint.project_id == project_id, 
        Sprint.status == SprintStatus.ACTIVE
    ).first()
    
    if active_sprint and active_sprint.id != sprint_id:
        raise HTTPException(status_code=400, detail="Another sprint is already active in this project")
    
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    
    if sprint.status == SprintStatus.COMPLETED or sprint.status == SprintStatus.CANCELLED:
         raise HTTPException(status_code=400, detail="Cannot start a completed or cancelled sprint")

    sprint.status = SprintStatus.ACTIVE
    db.commit()
    db.refresh(sprint)
    return sprint

@router.post("/{sprint_id}/complete", response_model=SprintResponse)
def complete_sprint(
    project_id: UUID,
    sprint_id: UUID,
    move_incomplete_to: str = Query(None, description="sprint_id or 'backlog'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.ADMIN)
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    
    sprint.status = SprintStatus.COMPLETED
    
    # Handle incomplete tasks
    if move_incomplete_to:
        incomplete_tasks = db.query(Task).filter(
            Task.sprint_id == sprint.id,
            Task.status.in_(["TODO", "IN_PROGRESS", "IN_REVIEW"])
        ).all()
        
        for task in incomplete_tasks:
            if move_incomplete_to == 'backlog':
                task.sprint_id = None
            else:
                try:
                    target_sprint_id = UUID(move_incomplete_to)
                    target_sprint = db.query(Sprint).filter(Sprint.id == target_sprint_id, Sprint.project_id == project_id).first()
                    if target_sprint:
                        task.sprint_id = target_sprint.id
                except ValueError:
                    pass
    
    db.commit()
    db.refresh(sprint)
    return sprint

@router.post("/{sprint_id}/tasks", response_model=List[TaskResponse])
def add_tasks_to_sprint(
    project_id: UUID,
    sprint_id: UUID,
    operation: BulkTaskOperation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.MEMBER)
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    
    tasks = db.query(Task).filter(Task.id.in_(operation.task_ids), Task.project_id == project_id).all()
    for task in tasks:
        task.sprint_id = sprint.id
    
    db.commit()
    return tasks

@router.delete("/{sprint_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_task_from_sprint(
    project_id: UUID,
    sprint_id: UUID,
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.MEMBER)
    task = db.query(Task).filter(Task.id == task_id, Task.sprint_id == sprint_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found in this sprint")
    
    task.sprint_id = None
    db.commit()

@router.get("/{sprint_id}/stats", response_model=SprintStats)
def get_sprint_stats(
    project_id: UUID,
    sprint_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.MEMBER)
    
    total_tasks = db.query(func.count(Task.id)).filter(Task.sprint_id == sprint_id).scalar() or 0
    completed_tasks = db.query(func.count(Task.id)).filter(Task.sprint_id == sprint_id, Task.status == "DONE").scalar() or 0
    
    total_points = db.query(func.sum(Task.estimate_points)).filter(Task.sprint_id == sprint_id).scalar() or 0.0
    completed_points = db.query(func.sum(Task.estimate_points)).filter(Task.sprint_id == sprint_id, Task.status == "DONE").scalar() or 0.0
    
    return SprintStats(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        total_points=total_points,
        completed_points=completed_points,
        remaining_points=total_points - completed_points
    )

@router.get("/{sprint_id}/burndown", response_model=SprintBurndown)
def get_sprint_burndown(
    project_id: UUID,
    sprint_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.MEMBER)
    
    # Very simplified burndown based on snapshots
    snapshots = db.query(SprintSnapshot).filter(SprintSnapshot.sprint_id == sprint_id).order_by(SprintSnapshot.snapshot_date.asc()).all()
    points = [
        {"date": s.snapshot_date, "ideal_remaining": s.total_points, "actual_remaining": s.remaining_points}
        for s in snapshots
    ]
    
    # If no snapshots, just return an empty list or current status
    return {"points": points}

@router.get("/{sprint_id}/time/stats")
def get_sprint_time_stats(
    sprint_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
) -> Any:
    require_organization_member(db, current_user.id, org_id)
    from app.models.time import TimeEntry
    
    # We must make sure the sprint is in a project owned by org
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
        
    entries = db.query(TimeEntry).filter(TimeEntry.sprint_id == sprint_id).all()
    
    total_seconds = sum(e.duration_seconds for e in entries)
    billable_seconds = sum(e.duration_seconds for e in entries if e.billable)
    non_billable_seconds = total_seconds - billable_seconds
    
    team_members = len(set(e.user_id for e in entries))
    tasks_tracked = len(set(e.task_id for e in entries if e.task_id))
    
    total_hours = total_seconds / 3600.0
    billable_hours = billable_seconds / 3600.0
    non_billable_hours = non_billable_seconds / 3600.0
    
    hours_per_member = total_hours / team_members if team_members > 0 else 0
    hours_per_task = total_hours / tasks_tracked if tasks_tracked > 0 else 0
    
    from app.models.task import Task
    tasks = db.query(Task).filter(Task.sprint_id == sprint_id).all()
    estimated_hours = sum((t.estimate_hours or 0) for t in tasks)
    
    estimate_variance = total_hours - estimated_hours if estimated_hours > 0 else 0
    
    return {
        "total_tracked_hours": total_hours,
        "billable_hours": billable_hours,
        "non_billable_hours": non_billable_hours,
        "team_members": team_members,
        "hours_per_member": hours_per_member,
        "hours_per_task": hours_per_task,
        "estimated_hours": estimated_hours,
        "estimate_variance": estimate_variance
    }

