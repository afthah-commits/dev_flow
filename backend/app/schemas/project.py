from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from app.models.project import ProjectStatus, ProjectPriority

from pydantic import BaseModel, ConfigDict, Field, model_validator

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.PLANNING
    priority: ProjectPriority = ProjectPriority.MEDIUM
    tech_stack: List[str] = []
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @model_validator(mode='after')
    def check_dates(self) -> 'ProjectBase':
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError('end_date cannot be before start_date')
        return self

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    priority: Optional[ProjectPriority] = None
    tech_stack: Optional[List[str]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class ProjectInDBBase(ProjectBase):
    id: UUID
    owner_id: UUID
    slug: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ProjectResponse(ProjectInDBBase):
    task_stats: Optional[dict] = None

class PaginatedProjectResponse(BaseModel):
    items: List[ProjectResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
