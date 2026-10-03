import os

task_schema = """from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from uuid import UUID
from app.models.task import TaskStatus, TaskPriority, TaskDependencyType

class ChecklistItemBase(BaseModel):
    text: str
    completed: bool = False
    position: float = 0.0

class ChecklistItemCreate(ChecklistItemBase):
    pass

class ChecklistItemUpdate(BaseModel):
    text: Optional[str] = None
    completed: Optional[bool] = None
    position: Optional[float] = None

class ChecklistItemResponse(ChecklistItemBase):
    id: UUID
    task_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class TaskDependencyBase(BaseModel):
    target_id: UUID
    dependency_type: TaskDependencyType

class TaskDependencyCreate(TaskDependencyBase):
    pass

class TaskDependencyResponse(TaskDependencyBase):
    id: UUID
    source_id: UUID
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    labels: List[str] = [] # Legacy labels, keep for backward compatibility or ignore
    
    parent_id: Optional[UUID] = None
    estimate_points: Optional[float] = None
    estimate_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    position: float = 0.0
    recurring_config: Optional[Dict[str, Any]] = None

class TaskCreate(TaskBase):
    label_ids: Optional[List[UUID]] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    labels: Optional[List[str]] = None
    parent_id: Optional[UUID] = None
    estimate_points: Optional[float] = None
    estimate_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    position: Optional[float] = None
    recurring_config: Optional[Dict[str, Any]] = None
    label_ids: Optional[List[UUID]] = None

class TaskStatusUpdate(BaseModel):
    status: TaskStatus
    position: Optional[float] = None

class LabelResponse(BaseModel):
    id: UUID
    name: str
    color: str
    model_config = ConfigDict(from_attributes=True)

class UserAvatarInfo(BaseModel):
    id: UUID
    full_name: str
    email: str
    model_config = ConfigDict(from_attributes=True)

class TaskInDBBase(TaskBase):
    id: UUID
    task_key: Optional[str] = None
    project_id: UUID
    creator_id: UUID
    updated_by_id: Optional[UUID] = None
    is_blocked: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class TaskResponse(TaskInDBBase):
    labels_rel: List[LabelResponse] = []
    watchers: List[UserAvatarInfo] = []
    checklists: List[ChecklistItemResponse] = []
    blocks: List[TaskDependencyResponse] = []
    blocked_by: List[TaskDependencyResponse] = []
    subtasks: List["TaskResponse"] = [] # Simple nesting

class PaginatedTaskResponse(BaseModel):
    items: List[TaskResponse]
    page: int
    page_size: int
    total: int
    total_pages: int

class TaskStats(BaseModel):
    total: int
    todo: int
    in_progress: int
    in_review: int
    done: int
    overdue: int

class BulkTaskOperation(BaseModel):
    task_ids: List[UUID]
    
class BulkTaskUpdate(BulkTaskOperation):
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[UUID] = None
"""

label_schema = """from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class LabelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    color: str = "#808080"

class LabelCreate(LabelBase):
    pass

class LabelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    color: Optional[str] = None

class LabelResponse(LabelBase):
    id: UUID
    organization_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
"""

with open("c:/personal_projects/devflow/backend/app/schemas/task.py", "w", encoding="utf-8") as f:
    f.write(task_schema)

with open("c:/personal_projects/devflow/backend/app/schemas/label.py", "w", encoding="utf-8") as f:
    f.write(label_schema)

print("Schemas updated")
