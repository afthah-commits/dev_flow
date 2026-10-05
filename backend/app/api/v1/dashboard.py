from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case
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

    # Phase 31: previously 6 separate COUNT queries over the same join;
    # collapse into a single aggregate pass.
    now = datetime.now(timezone.utc)
    row = db.query(
        func.count().label("total"),
        func.sum(case((Task.status == TaskStatus.TODO, 1), else_=0)).label("todo"),
        func.sum(case((Task.status == TaskStatus.IN_PROGRESS, 1), else_=0)).label("in_progress"),
        func.sum(case((Task.status == TaskStatus.IN_REVIEW, 1), else_=0)).label("in_review"),
        func.sum(case((Task.status == TaskStatus.DONE, 1), else_=0)).label("done"),
        func.sum(case(((Task.status != TaskStatus.DONE) & (Task.due_date < now), 1), else_=0)).label("overdue"),
    ).join(Project).filter(Project.organization_id == org_id).one()

    return TaskStats(
        total=row.total or 0,
        todo=row.todo or 0,
        in_progress=row.in_progress or 0,
        in_review=row.in_review or 0,
        done=row.done or 0,
        overdue=row.overdue or 0
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
    
    sprints = db.query(Sprint).options(joinedload(Sprint.project)).join(Project).filter(
        Project.organization_id == org_id,
        Sprint.status == SprintStatus.ACTIVE
    ).all()

    # Phase 31: single grouped query instead of 2 aggregates per sprint (N+1).
    sprint_ids = [s.id for s in sprints]
    agg: dict = {}
    if sprint_ids:
        rows = db.query(
            Task.sprint_id, Task.status, func.sum(Task.estimate_points)
        ).filter(Task.sprint_id.in_(sprint_ids)).group_by(Task.sprint_id, Task.status).all()
        for sprint_id, status, pts in rows:
            bucket = agg.setdefault(sprint_id, {"total": 0.0, "done": 0.0})
            bucket["total"] += float(pts or 0)
            if status == TaskStatus.DONE:
                bucket["done"] += float(pts or 0)

    result = []
    for s in sprints:
        bucket = agg.get(s.id, {"total": 0.0, "done": 0.0})
        total_pts = bucket["total"]
        completed_pts = bucket["done"]
        
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
