from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.task import TaskPriority

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
