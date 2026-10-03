from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from app.models.sprint import SprintStatus
from app.schemas.task import TaskResponse

class SprintBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    goal: Optional[str] = None
    description: Optional[str] = None
    status: SprintStatus = SprintStatus.PLANNED
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    capacity: Optional[float] = None

class SprintCreate(SprintBase):
    pass

class SprintUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    goal: Optional[str] = None
    description: Optional[str] = None
    status: Optional[SprintStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    capacity: Optional[float] = None

class SprintResponse(SprintBase):
    id: UUID
    project_id: UUID
    key: str
    created_by_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class SprintDetailsResponse(SprintResponse):
    tasks: List[TaskResponse] = []

class SprintStats(BaseModel):
    total_tasks: int
    completed_tasks: int
    total_points: float
    completed_points: float
    remaining_points: float

class SprintBurndownPoint(BaseModel):
    date: datetime
    ideal_remaining: float
    actual_remaining: float

class SprintBurndown(BaseModel):
    points: List[SprintBurndownPoint]
