from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from typing import Optional, Any
import re
import math

from app.api import deps
from app.models.user import User
from app.models.organization import OrganizationMember
from uuid import UUID
from app.models.project import Project, ProjectStatus, ProjectPriority
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, PaginatedProjectResponse
)

router = APIRouter()

def generate_slug(name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return slug if slug else "project"

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: ProjectCreate,
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    deps.require_organization_member(db, current_user.id, org_id)
    # generate a unique slug
    base_slug = generate_slug(project_in.name)
    slug = base_slug
    counter = 1
    while db.query(Project).filter(Project.organization_id == org_id, Project.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    project = Project(
        **project_in.model_dump(),
        owner_id=current_user.id,
        organization_id=org_id,
        slug=slug
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("", response_model=PaginatedProjectResponse)
def list_projects(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[ProjectStatus] = None,
    priority: Optional[ProjectPriority] = None,
    sort_by: str = Query("updated_at", pattern="^(created_at|updated_at|name)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$")
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    deps.require_organization_member(db, current_user.id, org_id)
    query = db.query(Project).filter(Project.organization_id == org_id)

    if search:
        query = query.filter(
            or_(
                Project.name.ilike(f"%{search}%"),
                Project.description.ilike(f"%{search}%")
            )
        )
    if status:
        query = query.filter(Project.status == status)
    if priority:
        query = query.filter(Project.priority == priority)

    if sort_order == "desc":
        query = query.order_by(desc(getattr(Project, sort_by)))
    else:
        query = query.order_by(asc(getattr(Project, sort_by)))

    total = query.count()
    projects = query.offset((page - 1) * page_size).limit(page_size).all()

    # compute task stats
    from app.models.task import Task, TaskStatus
    from sqlalchemy import func
    
    project_ids = [p.id for p in projects]
    if project_ids:
        # group by project_id and status
        stats_query = db.query(Task.project_id, Task.status, func.count(Task.id)).filter(Task.project_id.in_(project_ids)).group_by(Task.project_id, Task.status).all()
        stats_map = {pid: {"total": 0, "done": 0, "in_progress": 0} for pid in project_ids}
        for pid, status, count in stats_query:
            stats_map[pid]["total"] += count
            if status == TaskStatus.DONE:
                stats_map[pid]["done"] += count
            elif status == TaskStatus.IN_PROGRESS:
                stats_map[pid]["in_progress"] += count
        
        for p in projects:
            p.task_stats = stats_map.get(p.id, {"total": 0, "done": 0, "in_progress": 0})
            
    return PaginatedProjectResponse(
        items=projects,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=math.ceil(total / page_size) if total > 0 else 1
    )

from uuid import UUID

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deps.require_organization_member(db, current_user.id, project.organization_id)
    return project

@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    project_in: ProjectUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deps.require_organization_member(db, current_user.id, project.organization_id)
    
    update_data = project_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(project, field, value)
        
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}")
def delete_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deps.require_organization_member(db, current_user.id, project.organization_id)
        
    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}

@router.get("/{project_id}/time/stats")
def get_project_time_stats(
    project_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    project = db.query(Project).filter(Project.id == project_id, Project.organization_id == org_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    from app.models.time import TimeEntry
    entries = db.query(TimeEntry).filter(TimeEntry.project_id == project_id).all()
    
    total_seconds = sum(e.duration_seconds for e in entries)
    billable_seconds = sum(e.duration_seconds for e in entries if e.billable)
    non_billable_seconds = total_seconds - billable_seconds
    
    active_users = len(set(e.user_id for e in entries))
    tasks_tracked = len(set(e.task_id for e in entries if e.task_id))
    
    total_hours = total_seconds / 3600.0
    billable_hours = billable_seconds / 3600.0
    non_billable_hours = non_billable_seconds / 3600.0
    
    avg_time_per_task = total_hours / tasks_tracked if tasks_tracked > 0 else 0
    
    # get estimated hours
    from app.models.task import Task
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    estimated_hours = sum((t.estimate_hours or 0) for t in tasks)
    
    estimate_variance = total_hours - estimated_hours if estimated_hours > 0 else 0
    
    return {
        "total_tracked_hours": total_hours,
        "billable_hours": billable_hours,
        "non_billable_hours": non_billable_hours,
        "active_users": active_users,
        "tasks_tracked": tasks_tracked,
        "avg_time_per_task": avg_time_per_task,
        "estimated_hours": estimated_hours,
        "estimate_variance": estimate_variance
    }

