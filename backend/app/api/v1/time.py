import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func
from typing import Optional, Any
from datetime import datetime, timezone, timedelta
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.time import TimeEntry, ActiveTimer, TimeEntrySource
from app.schemas.time import (
    ActiveTimerBase, ActiveTimerResponse, TimeEntryCreate, TimeEntryUpdate, 
    TimeEntryResponse, PaginatedTimeEntryResponse, UserTimeSummary
)

router = APIRouter()

def _get_active_timer_response(timer: ActiveTimer) -> ActiveTimerResponse:
    now = datetime.now(timezone.utc)
    # Ensure started_at has timezone
    started_at = timer.started_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    
    elapsed = int((now - started_at).total_seconds())
    
    return ActiveTimerResponse(
        id=timer.id,
        organization_id=timer.organization_id,
        user_id=timer.user_id,
        project_id=timer.project_id,
        task_id=timer.task_id,
        description=timer.description,
        started_at=started_at,
        created_at=timer.created_at,
        updated_at=timer.updated_at,
        elapsed_seconds=elapsed
    )

@router.get("/timer/current", response_model=Optional[ActiveTimerResponse])
def get_current_timer(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    timer = db.query(ActiveTimer).filter(
        ActiveTimer.organization_id == org_id,
        ActiveTimer.user_id == current_user.id
    ).first()
    
    if not timer:
        return None
        
    return _get_active_timer_response(timer)

@router.post("/timer/start", response_model=ActiveTimerResponse)
def start_timer(
    request: ActiveTimerBase,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    
    # Check project
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project or project.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Check task
    if request.task_id:
        task = db.query(Task).filter(Task.id == request.task_id).first()
        if not task or task.project_id != request.project_id:
            raise HTTPException(status_code=404, detail="Task not found in project")
            
    # Check existing timer
    existing = db.query(ActiveTimer).filter(
        ActiveTimer.organization_id == org_id,
        ActiveTimer.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="A timer is already running in this organization")
        
    timer = ActiveTimer(
        organization_id=org_id,
        user_id=current_user.id,
        project_id=request.project_id,
        task_id=request.task_id,
        description=request.description,
        started_at=datetime.now(timezone.utc)
    )
    db.add(timer)
    db.commit()
    db.refresh(timer)
    
    return _get_active_timer_response(timer)

@router.post("/timer/stop", response_model=TimeEntryResponse)
def stop_timer(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    
    timer = db.query(ActiveTimer).filter(
        ActiveTimer.organization_id == org_id,
        ActiveTimer.user_id == current_user.id
    ).first()
    
    if not timer:
        raise HTTPException(status_code=404, detail="No active timer found")
        
    now = datetime.now(timezone.utc)
    started_at = timer.started_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
        
    duration = int((now - started_at).total_seconds())
    
    if duration < 1:
        duration = 1
        
    # Find sprint if task has one
    sprint_id = None
    if timer.task_id:
        task = db.query(Task).filter(Task.id == timer.task_id).first()
        if task:
            sprint_id = task.sprint_id
            
    entry = TimeEntry(
        organization_id=org_id,
        user_id=current_user.id,
        project_id=timer.project_id,
        task_id=timer.task_id,
        sprint_id=sprint_id,
        description=timer.description,
        started_at=started_at,
        ended_at=now,
        duration_seconds=duration,
        billable=False,
        source=TimeEntrySource.TIMER
    )
    db.add(entry)
    db.delete(timer)
    
    # Update actual_hours on task if present
    if timer.task_id and task:
        current_actual = task.actual_hours or 0.0
        task.actual_hours = current_actual + (duration / 3600.0)
        
    db.commit()
    db.refresh(entry)
    return entry

@router.post("/timer/discard")
def discard_timer(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    
    timer = db.query(ActiveTimer).filter(
        ActiveTimer.organization_id == org_id,
        ActiveTimer.user_id == current_user.id
    ).first()
    
    if not timer:
        raise HTTPException(status_code=404, detail="No active timer found")
        
    db.delete(timer)
    db.commit()
    return {"message": "Timer discarded"}
@router.post("/entries", response_model=TimeEntryResponse, status_code=status.HTTP_201_CREATED)
def create_time_entry(
    request: TimeEntryCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    
    if request.duration_seconds <= 0:
        raise HTTPException(status_code=400, detail="Duration must be positive")
        
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project or project.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if request.task_id:
        task = db.query(Task).filter(Task.id == request.task_id).first()
        if not task or task.project_id != request.project_id:
            raise HTTPException(status_code=404, detail="Task not found in project")
            
    ended_at = request.started_at + timedelta(seconds=request.duration_seconds)
    
    entry = TimeEntry(
        organization_id=org_id,
        user_id=current_user.id,
        project_id=request.project_id,
        task_id=request.task_id,
        sprint_id=request.sprint_id,
        description=request.description,
        started_at=request.started_at,
        ended_at=ended_at,
        duration_seconds=request.duration_seconds,
        billable=request.billable,
        source=TimeEntrySource.MANUAL
    )
    db.add(entry)
    
    if request.task_id and 'task' in locals() and task:
        current_actual = task.actual_hours or 0.0
        task.actual_hours = current_actual + (request.duration_seconds / 3600.0)
        
    db.commit()
    db.refresh(entry)
    return entry

@router.get("/entries", response_model=PaginatedTimeEntryResponse)
def list_time_entries(
    user_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    task_id: Optional[UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    
    query = db.query(TimeEntry).filter(TimeEntry.organization_id == org_id)
    
    if user_id:
        query = query.filter(TimeEntry.user_id == user_id)
    if project_id:
        query = query.filter(TimeEntry.project_id == project_id)
    if task_id:
        query = query.filter(TimeEntry.task_id == task_id)
    if date_from:
        query = query.filter(TimeEntry.started_at >= date_from)
    if date_to:
        query = query.filter(TimeEntry.started_at <= date_to)
        
    query = query.order_by(desc(TimeEntry.started_at))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedTimeEntryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 1
    )

@router.delete("/entries/{entry_id}")
def delete_time_entry(
    entry_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    # We will verify role here simply: users can delete their own entries. Admins/owners can delete any.
    member = deps.require_organization_member(db, current_user.id, org_id)
    
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id, TimeEntry.organization_id == org_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
        
    from app.models.organization import OrganizationRole
    if entry.user_id != current_user.id and member.role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this time entry")
        
    if entry.task_id:
        task = db.query(Task).filter(Task.id == entry.task_id).first()
        if task and task.actual_hours is not None:
            task.actual_hours = max(0.0, task.actual_hours - (entry.duration_seconds / 3600.0))
            
    db.delete(entry)
    db.commit()
    return {"message": "Time entry deleted"}

@router.patch("/entries/{entry_id}", response_model=TimeEntryResponse)
def update_time_entry(
    entry_id: UUID,
    request: TimeEntryUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id, TimeEntry.organization_id == org_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
        
    from app.models.organization import OrganizationRole
    if entry.user_id != current_user.id and member.role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to edit this time entry")
        
    update_data = request.model_dump(exclude_unset=True)
    
    if "duration_seconds" in update_data and "started_at" not in update_data:
        entry.ended_at = entry.started_at + timedelta(seconds=update_data["duration_seconds"])
    elif "started_at" in update_data and "duration_seconds" not in update_data:
        entry.ended_at = update_data["started_at"] + timedelta(seconds=entry.duration_seconds)
    elif "started_at" in update_data and "duration_seconds" in update_data:
        entry.ended_at = update_data["started_at"] + timedelta(seconds=update_data["duration_seconds"])

    # Adjust task actual_hours if duration changed
    if "duration_seconds" in update_data and update_data["duration_seconds"] != entry.duration_seconds:
        diff = update_data["duration_seconds"] - entry.duration_seconds
        if entry.task_id:
            task = db.query(Task).filter(Task.id == entry.task_id).first()
            if task:
                current_actual = task.actual_hours or 0.0
                task.actual_hours = max(0.0, current_actual + (diff / 3600.0))

    for field, value in update_data.items():
        if field not in ["started_at", "duration_seconds"]:
            setattr(entry, field, value)
            
    if "started_at" in update_data:
        entry.started_at = update_data["started_at"]
    if "duration_seconds" in update_data:
        entry.duration_seconds = update_data["duration_seconds"]
        
    db.commit()
    db.refresh(entry)
    return entry

@router.get("/my-summary", response_model=UserTimeSummary)
def get_user_time_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)
    
    entries = db.query(TimeEntry).filter(
        TimeEntry.organization_id == org_id,
        TimeEntry.user_id == current_user.id
    ).all()
    
    today_seconds = sum(e.duration_seconds for e in entries if e.started_at >= today_start)
    week_seconds = sum(e.duration_seconds for e in entries if e.started_at >= week_start)
    month_seconds = sum(e.duration_seconds for e in entries if e.started_at >= month_start)
    total_seconds = sum(e.duration_seconds for e in entries)
    billable_seconds = sum(e.duration_seconds for e in entries if e.billable)
    
    task_ids = list(set(e.task_id for e in entries if e.task_id))
    completed_tasks = 0
    if task_ids:
        from app.models.task import Task, TaskStatus
        completed_tasks = db.query(Task).filter(Task.id.in_(task_ids), Task.status == TaskStatus.DONE).count()
        
    active = db.query(ActiveTimer).filter(
        ActiveTimer.organization_id == org_id,
        ActiveTimer.user_id == current_user.id
    ).first()
    
    active_resp = None
    if active:
        active_resp = _get_active_timer_response(active)
        
    return UserTimeSummary(
        today_hours=today_seconds / 3600.0,
        week_hours=week_seconds / 3600.0,
        month_hours=month_seconds / 3600.0,
        tracked_hours=total_seconds / 3600.0,
        billable_hours=billable_seconds / 3600.0,
        completed_tasks=completed_tasks,
        active_timer=active_resp
    )

