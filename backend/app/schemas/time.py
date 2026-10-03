from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.models.time import TimeEntrySource

class ActiveTimerBase(BaseModel):
    project_id: UUID
    task_id: Optional[UUID] = None
    description: Optional[str] = None

class ActiveTimerResponse(ActiveTimerBase):
    id: UUID
    organization_id: UUID
    user_id: UUID
    started_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    elapsed_seconds: int

    model_config = ConfigDict(from_attributes=True)

class TimeEntryCreate(BaseModel):
    project_id: UUID
    task_id: Optional[UUID] = None
    sprint_id: Optional[UUID] = None
    description: Optional[str] = None
    started_at: datetime
    duration_seconds: int
    billable: bool = False

class TimeEntryUpdate(BaseModel):
    description: Optional[str] = None
    started_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    billable: Optional[bool] = None
    sprint_id: Optional[UUID] = None
    task_id: Optional[UUID] = None

class TimeEntryResponse(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: UUID
    project_id: UUID
    task_id: Optional[UUID] = None
    sprint_id: Optional[UUID] = None
    description: Optional[str] = None
    started_at: datetime
    ended_at: datetime
    duration_seconds: int
    billable: bool
    source: TimeEntrySource
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PaginatedTimeEntryResponse(BaseModel):
    items: List[TimeEntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class UserTimeSummary(BaseModel):
    today_hours: float
    week_hours: float
    month_hours: float
    tracked_hours: float
    billable_hours: float
    completed_tasks: int
    active_timer: Optional[ActiveTimerResponse] = None

class ProjectTimeStats(BaseModel):
    total_tracked_hours: float
    billable_hours: float
    non_billable_hours: float
    active_users: int
    tasks_tracked: int
    avg_time_per_task: float
    estimated_hours: float
    estimate_variance: float

class SprintTimeStats(BaseModel):
    total_tracked_hours: float
    billable_hours: float
    non_billable_hours: float
    team_members: int
    hours_per_member: float
    hours_per_task: float
    estimated_hours: float
    estimate_variance: float

class ProductivityStats(BaseModel):
    total_hours: float
    active_days: int
    tasks_completed: int
    tasks_worked_on: int
    avg_hours_per_day: float
    avg_hours_per_task: float
    estimated_hours: float
    completion_rate: float

class DailyProductivity(BaseModel):
    date: str
    hours: float

class WeeklyProductivity(BaseModel):
    week: str
    tracked_hours: float
    completed_tasks: int
    created_tasks: int
    avg_daily_hours: float

class TeamWorkloadItem(BaseModel):
    user_id: UUID
    user_name: str
    tracked_hours: float
    assigned_tasks: int
    completed_tasks: int
    overdue_tasks: int
    estimated_hours: float
    workload_percentage: float
