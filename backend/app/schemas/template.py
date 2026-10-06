from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.task import TaskPriority


# ---------------------------------------------------------------------------
# Existing TaskTemplate (task-level template) — unchanged
# ---------------------------------------------------------------------------

class TaskTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    title_template: Optional[str] = None
    description_template: Optional[str] = None
    priority_template: Optional[TaskPriority] = None
    labels_template: List[str] = []
    checklist_template: List[str] = []

class TaskTemplateCreate(TaskTemplateBase):
    pass

class TaskTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    title_template: Optional[str] = None
    description_template: Optional[str] = None
    priority_template: Optional[TaskPriority] = None
    labels_template: Optional[List[str]] = None
    checklist_template: Optional[List[str]] = None

class TaskTemplateResponse(TaskTemplateBase):
    id: UUID
    organization_id: UUID
    created_by_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Phase 44 — Project templates
# ---------------------------------------------------------------------------

class ProjectTemplateTaskIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    position: int = 0
    label_names: List[str] = []
    checklist_items: List[str] = []

class ProjectTemplateTaskCreate(ProjectTemplateTaskIn):
    pass

class ProjectTemplateTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    position: Optional[int] = None
    label_names: Optional[List[str]] = None
    checklist_items: Optional[List[str]] = None

class ProjectTemplateTaskResponse(ProjectTemplateTaskIn):
    id: UUID
    template_id: UUID
    model_config = ConfigDict(from_attributes=True)

class ProjectTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class ProjectTemplateCreate(ProjectTemplateBase):
    tasks: List[ProjectTemplateTaskCreate] = []

class ProjectTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_archived: Optional[bool] = None
    tasks: Optional[List[ProjectTemplateTaskCreate]] = None

class ProjectTemplateResponse(ProjectTemplateBase):
    id: UUID
    organization_id: UUID
    is_archived: bool = False
    created_by_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tasks: List[ProjectTemplateTaskResponse] = []
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Phase 44 — Create project from template
# ---------------------------------------------------------------------------

class ProjectFromTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    # Optional overrides of the template defaults
    status: Optional[str] = None
    priority: Optional[str] = None

class ProjectFromTemplateResponse(BaseModel):
    project_id: UUID
    name: str
    slug: str
    tasks_created: int
