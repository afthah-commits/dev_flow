from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.milestone import MilestoneStatus
from app.schemas.task import TaskResponse
from app.schemas.sprint import SprintResponse

class MilestoneBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    status: MilestoneStatus = MilestoneStatus.PLANNED
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    position: float = 0.0

class MilestoneCreate(MilestoneBase):
    pass

class MilestoneUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[MilestoneStatus] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    position: Optional[float] = None

class MilestoneResponse(MilestoneBase):
    id: UUID
    project_id: UUID
    created_by_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class MilestoneDetailsResponse(MilestoneResponse):
    tasks: List[TaskResponse] = []

class MilestoneStats(BaseModel):
    total_tasks: int
    completed_tasks: int
    total_points: float
    completed_points: float
    remaining_points: float
    progress_percentage: float

class RoadmapResponse(BaseModel):
    milestones: List[MilestoneResponse]
    sprints: List[SprintResponse]
