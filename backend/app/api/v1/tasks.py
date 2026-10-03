from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func
from typing import Optional, Any, List
from uuid import UUID
import math
from datetime import datetime, timezone

from app.api import deps
from app.models.user import User
from app.models.project import Project
from app.models.task import Task, TaskStatus, TaskPriority, Label, TaskLabel, TaskDependency, TaskDependencyType, TaskWatcher, ChecklistItem
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskStatusUpdate, TaskResponse, 
    PaginatedTaskResponse, TaskStats, BulkTaskUpdate, BulkTaskOperation,
    ChecklistItemCreate, ChecklistItemUpdate, ChecklistItemResponse,
    TaskDependencyCreate, TaskDependencyResponse
)

router = APIRouter()

def get_project_or_404(db: Session, project_id: UUID, current_user: User) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deps.require_organization_member(db, current_user.id, project.organization_id)
    return project

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    task_in: TaskCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = get_project_or_404(db, project_id, current_user)
    
    if task_in.assignee_id:
        deps.require_organization_member(db, task_in.assignee_id, project.organization_id)
        
    if task_in.parent_id:
        parent = db.query(Task).filter(Task.id == task_in.parent_id, Task.project_id == project.id).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Invalid parent task")
            
    # Generate task_key
    project.task_seq_num += 1
    seq = project.task_seq_num
    task_key = f"{project.key}-{seq}" if project.key else f"PROJ-{seq}"
        
    task_data = task_in.model_dump(exclude={"label_ids"})
    task = Task(
        **task_data,
        project_id=project.id,
        creator_id=current_user.id,
        task_key=task_key
    )
    
    if task_in.label_ids:
        # verify labels belong to org
        labels = db.query(Label).filter(Label.id.in_(task_in.label_ids), Label.organization_id == project.organization_id).all()
        if len(labels) != len(task_in.label_ids):
            raise HTTPException(status_code=400, detail="One or more invalid labels")
        task.labels_rel.extend(labels)

    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.get("", response_model=PaginatedTaskResponse)
def list_tasks(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    assignee_id: Optional[UUID] = None,
    parent_id: Optional[UUID] = None,
    is_blocked: Optional[bool] = None,
    sprint_id: Optional[str] = None,
    milestone_id: Optional[UUID] = None,
    sort_by: str = Query("position", pattern="^(created_at|updated_at|due_date|priority|title|position)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$")
) -> Any:
    project = get_project_or_404(db, project_id, current_user)
    
    query = db.query(Task).filter(Task.project_id == project.id)

    if search:
        query = query.filter(
            or_(
                Task.title.ilike(f"%{search}%"),
                Task.description.ilike(f"%{search}%"),
                Task.task_key.ilike(f"%{search}%")
            )
        )
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    if parent_id is not None:
        query = query.filter(Task.parent_id == parent_id)
    if sprint_id:
        if sprint_id == 'null':
            query = query.filter(Task.sprint_id == None)
        else:
            query = query.filter(Task.sprint_id == UUID(sprint_id))
    if milestone_id is not None:
        query = query.filter(Task.milestone_id == milestone_id)
    if is_blocked is not None:
        query = query.filter(Task.is_blocked == is_blocked)

    if sort_order == "desc":
        query = query.order_by(desc(getattr(Task, sort_by)))
    else:
        query = query.order_by(asc(getattr(Task, sort_by)))

    total = query.count()
    tasks = query.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedTaskResponse(
        items=tasks,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=math.ceil(total / page_size) if total > 0 else 1
    )

@router.get("/stats", response_model=TaskStats)
def get_task_stats(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = get_project_or_404(db, project_id, current_user)
    
    total = db.query(Task).filter(Task.project_id == project.id).count()
    todo = db.query(Task).filter(Task.project_id == project.id, Task.status == TaskStatus.TODO).count()
    in_progress = db.query(Task).filter(Task.project_id == project.id, Task.status == TaskStatus.IN_PROGRESS).count()
    in_review = db.query(Task).filter(Task.project_id == project.id, Task.status == TaskStatus.IN_REVIEW).count()
    done = db.query(Task).filter(Task.project_id == project.id, Task.status == TaskStatus.DONE).count()
    
    now = datetime.now(timezone.utc)
    overdue = db.query(Task).filter(
        Task.project_id == project.id, 
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

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    task_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = get_project_or_404(db, project_id, current_user)
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    task_id: UUID,
    task_in: TaskUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = get_project_or_404(db, project_id, current_user)
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task_in.assignee_id:
        deps.require_organization_member(db, task_in.assignee_id, project.organization_id)
        
    if task_in.parent_id and task_in.parent_id != task.parent_id:
        if task_in.parent_id == task.id:
            raise HTTPException(status_code=400, detail="Task cannot be its own parent")
        parent = db.query(Task).filter(Task.id == task_in.parent_id, Task.project_id == project.id).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Invalid parent task")
        # simple check to avoid 1-level cycle
        if parent.parent_id == task.id:
            raise HTTPException(status_code=400, detail="Circular parent reference")
    
    update_data = task_in.model_dump(exclude_unset=True, exclude={"label_ids"})
    for field, value in update_data.items():
        setattr(task, field, value)
        
    if task_in.label_ids is not None:
        labels = db.query(Label).filter(Label.id.in_(task_in.label_ids), Label.organization_id == project.organization_id).all()
        if len(labels) != len(task_in.label_ids):
            raise HTTPException(status_code=400, detail="One or more invalid labels")
        task.labels_rel = labels

    task.updated_by_id = current_user.id
    db.commit()
    db.refresh(task)
    return task

@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    task_id: UUID,
    status_in: TaskStatusUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = get_project_or_404(db, project_id, current_user)
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = status_in.status
    if status_in.position is not None:
        task.position = status_in.position
        
    task.updated_by_id = current_user.id
    db.commit()
    db.refresh(task)
    return task

@router.delete("/{task_id}")
def delete_task(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    task_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = get_project_or_404(db, project_id, current_user)
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}

# --- Checklists ---
@router.post("/{task_id}/checklists", response_model=ChecklistItemResponse)
def create_checklist_item(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    task_id: UUID,
    item_in: ChecklistItemCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = get_project_or_404(db, project_id, current_user)
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    item = ChecklistItem(**item_in.model_dump(), task_id=task.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.patch("/{task_id}/checklists/{item_id}", response_model=ChecklistItemResponse)
def update_checklist_item(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    task_id: UUID,
    item_id: UUID,
    item_in: ChecklistItemUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = get_project_or_404(db, project_id, current_user)
    item = db.query(ChecklistItem).filter(ChecklistItem.id == item_id, ChecklistItem.task_id == task_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
        
    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{task_id}/checklists/{item_id}")
def delete_checklist_item(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    task_id: UUID,
    item_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = get_project_or_404(db, project_id, current_user)
    item = db.query(ChecklistItem).filter(ChecklistItem.id == item_id, ChecklistItem.task_id == task_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    db.delete(item)
    db.commit()
    return {"message": "Checklist item deleted"}

# --- Dependencies ---
@router.post("/{task_id}/dependencies", response_model=TaskDependencyResponse)
def create_dependency(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    task_id: UUID,
    dep_in: TaskDependencyCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = get_project_or_404(db, project_id, current_user)
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Source task not found")
    
    if task_id == dep_in.target_id:
        raise HTTPException(status_code=400, detail="Task cannot depend on itself")
        
    target = db.query(Task).filter(Task.id == dep_in.target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target task not found")
        
    # verify target is in same project (as requested: "Prevent invalid cross-project dependencies unless explicitly supported.")
    if target.project_id != project.id:
        raise HTTPException(status_code=400, detail="Cross-project dependencies not supported in this phase")
        
    # check circular
    if dep_in.dependency_type == TaskDependencyType.BLOCKS:
        # if A blocks B, B cannot block A
        rev = db.query(TaskDependency).filter(
            TaskDependency.source_id == target.id, 
            TaskDependency.target_id == task.id,
            TaskDependency.dependency_type == TaskDependencyType.BLOCKS
        ).first()
        if rev:
            raise HTTPException(status_code=400, detail="Circular dependency detected")
            
    # check dup
    existing = db.query(TaskDependency).filter(
        TaskDependency.source_id == task.id,
        TaskDependency.target_id == target.id,
        TaskDependency.dependency_type == dep_in.dependency_type
    ).first()
    if existing:
        return existing
        
    dep = TaskDependency(
        source_id=task.id,
        target_id=target.id,
        dependency_type=dep_in.dependency_type
    )
    db.add(dep)
    
    # mark blocked if target is blocked by source
    if dep_in.dependency_type == TaskDependencyType.BLOCKS:
        target.is_blocked = True
        
    db.commit()
    db.refresh(dep)
    return dep

@router.delete("/{task_id}/dependencies/{dependency_id}")
def delete_dependency(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    task_id: UUID,
    dependency_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = get_project_or_404(db, project_id, current_user)
    dep = db.query(TaskDependency).filter(TaskDependency.id == dependency_id, TaskDependency.source_id == task_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Dependency not found")
        
    target = db.query(Task).filter(Task.id == dep.target_id).first()
    db.delete(dep)
    
    # re-evaluate blocked status
    if dep.dependency_type == TaskDependencyType.BLOCKS and target:
        remaining = db.query(TaskDependency).filter(
            TaskDependency.target_id == target.id,
            TaskDependency.dependency_type == TaskDependencyType.BLOCKS
        ).count()
        if remaining == 0:
            target.is_blocked = False
            
    db.commit()
    return {"message": "Dependency deleted"}

# --- Watchers ---
@router.post("/{task_id}/watchers")
def watch_task(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    task_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = get_project_or_404(db, project_id, current_user)
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if current_user not in task.watchers:
        task.watchers.append(current_user)
        db.commit()
    return {"message": "Watching task"}

@router.delete("/{task_id}/watchers")
def unwatch_task(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    task_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = get_project_or_404(db, project_id, current_user)
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if current_user in task.watchers:
        task.watchers.remove(current_user)
        db.commit()
    return {"message": "Unwatched task"}

# --- Bulk Operations ---
@router.post("/bulk/update")
def bulk_update_tasks(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    bulk_in: BulkTaskUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = get_project_or_404(db, project_id, current_user)
    
    if bulk_in.assignee_id:
        deps.require_organization_member(db, bulk_in.assignee_id, project.organization_id)
        
    tasks = db.query(Task).filter(Task.id.in_(bulk_in.task_ids), Task.project_id == project.id).all()
    for task in tasks:
        if bulk_in.status:
            task.status = bulk_in.status
        if bulk_in.priority:
            task.priority = bulk_in.priority
        if bulk_in.assignee_id:
            task.assignee_id = bulk_in.assignee_id
        if bulk_in.sprint_id:
            task.sprint_id = bulk_in.sprint_id
        if bulk_in.remove_sprint:
            task.sprint_id = None
        if bulk_in.milestone_id:
            task.milestone_id = bulk_in.milestone_id
        if bulk_in.remove_milestone:
            task.milestone_id = None
        task.updated_by_id = current_user.id
        
    db.commit()
    return {"message": f"Updated {len(tasks)} tasks"}

@router.post("/bulk/delete")
def bulk_delete_tasks(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    bulk_in: BulkTaskOperation,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    project = get_project_or_404(db, project_id, current_user)
    
    tasks = db.query(Task).filter(Task.id.in_(bulk_in.task_ids), Task.project_id == project.id).all()
    count = len(tasks)
    for task in tasks:
        db.delete(task)
        
    db.commit()
    return {"message": f"Deleted {count} tasks"}
