import datetime as pdt
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
    report_date: Optional[pdt.date] = None
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

class DailyReportSummaryResponse(BaseModel):
    total_reports: int
    completed_task_count: int
    next_plan_count: int
    blocker_count: int
    unique_contributors: int
    missing_reports: int
    date: Optional[pdt.date] = None

class TeamDailyReportResponse(DailyReportResponse):
    author_name: Optional[str] = None

class BlockerSummaryResponse(BaseModel):
    blocker: str
    occurrences: int
    latest_report_date: date
    reporters: List[str]

class DailyTrendItem(BaseModel):
    date: pdt.date
    reports_submitted: int
    completed_tasks: int

class WeeklySummaryResponse(BaseModel):
    start_date: date
    end_date: date
    total_reports: int
    completed_tasks: int
    blockers: int
    trend: List[DailyTrendItem]
