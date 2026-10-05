from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID

class DailyReportBase(BaseModel):
    report_date: date
    completed_tasks: List[str]
    next_plan: List[str]
    blockers: List[str]

class DailyReportCreate(DailyReportBase):
    pass

class DailyReportUpdate(BaseModel):
    report_date: Optional[date] = None
    completed_tasks: Optional[List[str]] = None
    next_plan: Optional[List[str]] = None
    blockers: Optional[List[str]] = None

class DailyReportResponse(DailyReportBase):
    id: UUID
    organization_id: UUID
    author_user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
