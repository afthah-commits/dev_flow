from typing import Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_organization_member
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.sprint import Sprint, SprintStatus
from app.schemas.task import PaginatedTaskResponse, TaskResponse
from app.models.organization import OrganizationRole

router = APIRouter()

def get_project_and_check_access(db: Session, project_id: UUID, user: User, required_role: OrganizationRole = OrganizationRole.MEMBER) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    check_organization_permission(db, user.id, project.organization_id, required_role)
    return project

@router.get("", response_model=PaginatedTaskResponse)
def get_backlog(
    project_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    get_project_and_check_access(db, project_id, current_user, OrganizationRole.MEMBER)
    
    # Backlog consists of tasks not in an active or planned or completed sprint.
    # Basically sprint_id == None, or perhaps sprint is cancelled.
    # We will just use sprint_id == None for backlog.
    query = db.query(Task).filter(Task.project_id == project_id, Task.sprint_id == None)
    
    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
        
    total = query.count()
    
    query = query.order_by(Task.position.asc(), Task.created_at.desc())
    tasks = query.offset((page - 1) * page_size).limit(page_size).all()
    
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedTaskResponse(
        items=tasks,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages
    )
