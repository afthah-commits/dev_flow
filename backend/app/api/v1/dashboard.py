from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Any
from datetime import datetime, timezone

from app.api import deps
from uuid import UUID
from fastapi import HTTPException
from app.models.user import User
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskStats

router = APIRouter()

@router.get("/stats", response_model=TaskStats)
def get_dashboard_stats(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    deps.require_organization_member(db, current_user.id, org_id)
    # Get all tasks for all projects owned by user
    base_query = db.query(Task).join(Project).filter(Project.organization_id == org_id)
    
    total = base_query.count()
    todo = base_query.filter(Task.status == TaskStatus.TODO).count()
    in_progress = base_query.filter(Task.status == TaskStatus.IN_PROGRESS).count()
    in_review = base_query.filter(Task.status == TaskStatus.IN_REVIEW).count()
    done = base_query.filter(Task.status == TaskStatus.DONE).count()
    
    now = datetime.now(timezone.utc)
    overdue = base_query.filter(
        Task.status != TaskStatus.DONE,
        Task.due_date < now
    ).count()

    return TaskStats(
        total=total,
        todo=todo,
        in_progress=in_progress,
        in_review=in_review,
        done=done,
        overdue=overdue
    )

from app.models.sprint import Sprint, SprintStatus

@router.get("/sprints/active")
def get_active_sprints(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    deps.require_organization_member(db, current_user.id, org_id)
    
    sprints = db.query(Sprint).join(Project).filter(
        Project.organization_id == org_id,
        Sprint.status == SprintStatus.ACTIVE
    ).all()
    
    result = []
    for s in sprints:
        total_pts = db.query(func.sum(Task.estimate_points)).filter(Task.sprint_id == s.id).scalar() or 0.0
        completed_pts = db.query(func.sum(Task.estimate_points)).filter(Task.sprint_id == s.id, Task.status == TaskStatus.DONE).scalar() or 0.0
        
        result.append({
            "id": s.id,
            "project_name": s.project.name,
            "sprint_name": s.name,
            "key": s.key,
            "end_date": s.end_date,
            "total_points": total_pts,
            "completed_points": completed_pts,
            "progress": (completed_pts / total_pts * 100) if total_pts > 0 else 0
        })
    return result
